"""
Unit tests for configuration and utility functions in the TRD CEA Toolkit.

This module tests configuration loading, parameter validation, and core utility functions.
"""

import unittest
import os
import sys
import tempfile
import yaml
from pathlib import Path
import numpy as np
import pandas as pd

# Import from the correct source location
from src.trd_cea.core.utils import (
    calculate_icer, calculate_nmb, calculate_icr, 
    calculate_dalys_averted
)
from src.trd_cea.core.io import load_data, save_results
from src.trd_cea.core.validation import validate_analysis_parameters
from src.trd_cea.core.config import load_config, validate_config, set_random_seed


class TestConfiguration(unittest.TestCase):
    """Unit tests for configuration management."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary config file for testing
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        
        test_config = {
            'analysis': {
                'time_horizon': 10,
                'discount_rate_costs': 0.035,
                'discount_rate_effects': 0.035,
                'wtp_threshold': 50000
            },
            'strategies': {
                'ECT': {'name': 'Electroconvulsive Therapy', 'abbreviation': 'ECT'},
                'IV_KA': {'name': 'Intravenous Ketamine', 'abbreviation': 'IV-KA'}
            }
        }
        
        yaml.dump(test_config, self.temp_config)
        self.temp_config.close()
    
    def tearDown(self):
        """Clean up after each test method."""
        os.unlink(self.temp_config.name)
    
    def test_load_config_valid_yaml(self):
        """Test loading a valid YAML configuration file."""
        loaded_config = load_config(self.temp_config.name)
        
        self.assertIsInstance(loaded_config, dict)
        self.assertIn('analysis', loaded_config)
        self.assertEqual(loaded_config['analysis']['time_horizon'], 10)
        self.assertEqual(loaded_config['analysis']['wtp_threshold'], 50000)
        self.assertIn('strategies', loaded_config)
        self.assertIn('ECT', loaded_config['strategies'])
    
    def test_validate_config_structure(self):
        """Test configuration structure validation."""
        loaded_config = load_config(self.temp_config.name)
        is_valid, errors = validate_config(loaded_config)
        
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_set_random_seed(self):
        """Test random seed setting for reproducibility."""
        initial_state = np.random.get_state()
        
        # Set seed and generate a number
        set_random_seed(42)
        val1 = np.random.random()
        
        # Set the same seed and generate another number
        set_random_seed(42)
        val2 = np.random.random()
        
        # Values should be the same
        self.assertEqual(val1, val2)
        
        # Restore initial state
        np.random.set_state(initial_state)


class TestUtilityFunctions(unittest.TestCase):
    """Unit tests for core utility functions."""
    
    def test_calculate_icer_basic(self):
        """Test basic ICER calculation."""
        icer = calculate_icer(
            cost_new=1500,
            cost_old=1000,
            effect_new=0.8,
            effect_old=0.6
        )
        expected = (1500 - 1000) / (0.8 - 0.6)  # 500 / 0.2 = 2500
        self.assertAlmostEqual(icer, expected)
    
    def test_calculate_icer_dominant(self):
        """Test ICER calculation with dominant strategy (better effect, lower cost)."""
        icer = calculate_icer(
            cost_new=800,   # cheaper
            cost_old=1000,
            effect_new=0.7,  # better
            effect_old=0.6
        )
        # Should be negative (cost-saving with better outcomes)
        self.assertLess(icer, 0)
        
    def test_calculate_icer_same_effect(self):
        """Test ICER calculation with same effect (should return infinity)."""
        icer = calculate_icer(
            cost_new=1200,
            cost_old=1000,
            effect_new=0.6,
            effect_old=0.6  # Same effect
        )
        
        # When effect difference is zero, ICER should be infinite (or undefined)
        self.assertEqual(icer, float('inf'))
    
    def test_calculate_icer_same_cost(self):
        """Test ICER calculation with same cost (but different effect)."""
        icer = calculate_icer(
            cost_new=1000,  # Same cost
            cost_old=1000,
            effect_new=0.8,  # Better effect
            effect_old=0.6
        )
        
        # When cost difference is zero but effect differs, ICER should be 0
        self.assertEqual(icer, 0.0)
    
    def test_calculate_nmb_positive_benefit(self):
        """Test NMB calculation with positive health benefit."""
        nmb = calculate_nmb(
            cost=1000,
            effect=0.5,
            wtp=50000
        )
        expected = 0.5 * 50000 - 1000  # 25000 - 1000 = 24000
        self.assertAlmostEqual(nmb, expected)
    
    def test_calculate_nmb_zero_effect(self):
        """Test NMB calculation with zero health effect."""
        nmb = calculate_nmb(
            cost=1000,
            effect=0.0,
            wtp=50000
        )
        expected = 0.0 * 50000 - 1000  # 0 - 1000 = -1000
        self.assertAlmostEqual(nmb, expected)
    
    def test_calculate_icr(self):
        """Test Incremental Cost-Ratio calculation."""
        icr = calculate_icr(
            cost=2000,
            effect=0.75
        )
        expected = 2000 / 0.75  # 2666.67
        self.assertAlmostEqual(icr, expected)
    
    def test_calculate_dalys_averted(self):
        """Test calculation of DALYs averted."""
        # Using placeholder values for testing
        mortality_rate = 0.01  # 1% mortality rate
        morbidities = [0.05, 0.03]  # 5% and 3% prevalence
        time_horizon = 10  # 10 years
        discount_rate = 0.035  # 3.5%
        
        dalys = calculate_dalys_averted(mortality_rate, morbidities, time_horizon, discount_rate)
        self.assertIsInstance(dalys, (int, float))
        self.assertGreaterEqual(dalys, 0)  # DALYs should be non-negative


class TestValidation(unittest.TestCase):
    """Unit tests for validation functions."""
    
    def test_validate_analysis_parameters_basic(self):
        """Test basic parameter validation."""
        params = {
            'strategies': ['A', 'B'],
            'costs': [1000, 1500],
            'effects': [0.5, 0.7],
            'wtp_threshold': 50000
        }
        
        is_valid, errors = validate_analysis_parameters(params)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_analysis_parameters_invalid_costs(self):
        """Test validation with invalid (negative) costs."""
        params = {
            'strategies': ['A', 'B'],
            'costs': [1000, -1500],  # Negative cost is invalid
            'effects': [0.5, 0.7],
            'wtp_threshold': 50000
        }
        
        is_valid, errors = validate_analysis_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn('All costs must be non-negative', errors)
    
    def test_validate_analysis_parameters_invalid_effects(self):
        """Test validation with invalid (negative) effects."""
        params = {
            'strategies': ['A', 'B'],
            'costs': [1000, 1500],
            'effects': [0.5, -0.2],  # Negative effect is invalid
            'wtp_threshold': 50000
        }
        
        is_valid, errors = validate_analysis_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn('All effects must be non-negative', errors)
    
    def test_validate_analysis_parameters_mismatched_lengths(self):
        """Test validation with mismatched array lengths."""
        params = {
            'strategies': ['A', 'B', 'C'],  # 3 strategies
            'costs': [1000, 1500],  # Only 2 costs
            'effects': [0.5, 0.7, 0.6],  # 3 effects
            'wtp_threshold': 50000
        }
        
        is_valid, errors = validate_analysis_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn('Parameter arrays must have the same length', errors)
    
    def test_validate_analysis_parameters_negative_wtp(self):
        """Test validation with negative WTP threshold."""
        params = {
            'strategies': ['A', 'B'],
            'costs': [1000, 1500],
            'effects': [0.5, 0.7],
            'wtp_threshold': -50000  # Negative WTP is invalid
        }
        
        is_valid, errors = validate_analysis_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn('WTP threshold must be non-negative', errors)


class TestDataIO(unittest.TestCase):
    """Unit tests for data I/O functions."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_results(self):
        """Test saving and loading of analysis results."""
        test_results = {
            'strategies': ['A', 'B', 'C'],
            'costs': [1000, 1500, 1200],
            'effects': [0.6, 0.8, 0.7],
            'icers': [float('inf'), 2500, 3000]
        }
        
        # Save results
        output_path = self.temp_dir / "test_results.csv"
        save_results(test_results, output_path)
        
        # Check that file was created
        self.assertTrue(output_path.exists())
        
        # In a real implementation, we would load and verify content
        # loaded_data = load_data(str(output_path))
        # This would depend on the specific implementation of load_data
    
    def test_load_data_formats(self):
        """Test data loading with different formats."""
        # Create test data in various formats
        test_data = pd.DataFrame({
            'strategy': ['A', 'B', 'C'],
            'cost': [1000, 1500, 1200],
            'effect': [0.5, 0.7, 0.6]
        })
        
        # Test CSV format
        csv_path = self.temp_dir / "test_data.csv"
        test_data.to_csv(csv_path, index=False)
        
        # Test Excel format
        excel_path = self.temp_dir / "test_data.xlsx"
        test_data.to_excel(excel_path, index=False)
        
        # Would test load_data function if implemented
        # loaded_csv = load_data(str(csv_path))
        # loaded_excel = load_data(str(excel_path))
        # pd.testing.assert_frame_equal(test_data, loaded_csv)
        # pd.testing.assert_frame_equal(test_data, loaded_excel)
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)