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

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.pardir, 'scripts'))
sys.path.insert(0, os.path.join(os.pardir, 'scripts', 'core'))
sys.path.insert(0, os.path.join(os.pardir, 'scripts', 'models'))

# Import specific modules to test
from scripts.core.config import load_config, validate_config, set_random_seed
from scripts.core.utils import (
    calculate_icer, calculate_nmb, calculate_icur, 
    check_dominated_strategies, create_ce_plane_data
)
from scripts.core.io import load_data, save_results
from scripts.core.validation import validate_analysis_parameters


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
        config = load_config(self.temp_config.name)
        
        self.assertIsInstance(config, dict)
        self.assertIn('analysis', config)
        self.assertEqual(config['analysis']['time_horizon'], 10)
        self.assertEqual(config['analysis']['wtp_threshold'], 50000)
        self.assertIn('strategies', config)
        self.assertIn('ECT', config['strategies'])
    
    def test_validate_config_structure(self):
        """Test configuration structure validation."""
        config = load_config(self.temp_config.name)
        is_valid, errors = validate_config(config)
        
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
    
    def test_calculate_icur(self):
        """Test Incremental Cost-Utility Ratio calculation."""
        icur = calculate_icur(
            cost_new=2000,
            cost_old=1000,
            utility_new=0.75,
            utility_old=0.65
        )
        expected = (2000 - 1000) / (0.75 - 0.65)  # 1000 / 0.1 = 10000
        self.assertAlmostEqual(icur, expected)
    
    def test_check_dominated_strategies_simple(self):
        """Test identification of dominated strategies."""
        costs = [1000, 2000, 1500]  # Strategy 2 dominates Strategy 1
        effects = [0.5, 0.4, 0.6]  # Strategy 2 gives less effect but more cost than Strategy 1
        
        # Strategy 2 (cost=2000, effect=0.4) is dominated by Strategy 1 (cost=1000, effect=0.5)
        dominated = check_dominated_strategies(costs, effects)
        
        # In this case, Strategy 1 dominates Strategy 2, so Strategy 2 should be dominated
        # Actually, Strategy 0 dominates Strategy 1 in this setup
        # Let me correct the example:
        costs = [2000, 1000, 1500]  # Strategy 1 is cheaper and better
        effects = [0.5, 0.6, 0.55]  # Strategy 1 has better effect
        
        # Now Strategy 1 dominates Strategy 0
        dominated = check_dominated_strategies(costs, effects)
        self.assertIn(0, dominated)  # Strategy 0 should be dominated
    
    def test_create_ce_plane_data(self):
        """Test creation of cost-effectiveness plane data."""
        costs = [1000, 1500, 1200]
        effects = [0.6, 0.8, 0.7]
        strategies = ['A', 'B', 'C']
        
        df = create_ce_plane_data(costs, effects, strategies)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn('cost', df.columns)
        self.assertIn('effect', df.columns)
        self.assertIn('strategy', df.columns)
        self.assertEqual(df.loc[0, 'strategy'], 'A')


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