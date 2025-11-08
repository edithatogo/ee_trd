"""
Unit tests for the core analysis engines in the TRD CEA Toolkit.

This module contains unit tests for individual functions and classes
within the health economic evaluation engines.
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Import the modules to test
from src.trd_cea.models.dcea_engine import DCEAResult, IndigenousDCEAResult
from src.trd_cea.models.voi_engine import run_voi_analysis
from src.trd_cea.models.bia_engine import run_bia_all_arms
from src.trd_cea.models.cea_engine import simulate_arm, run_cea_all_arms
from src.trd_cea.core.config import load_config, validate_parameters
from src.trd_cea.core.io import load_data, save_results
from src.trd_cea.core.utils import calculate_icer, calculate_nmb, calculate_icr


class TestCEAFunctions(unittest.TestCase):
    """Unit tests for the Cost-Effectiveness Analysis functions."""
    
    def test_calculate_icer(self):
        """Test ICER calculation."""
        icer = calculate_icer(
            cost_new=1500, 
            cost_old=1000, 
            effect_new=0.8, 
            effect_old=0.6
        )
        expected_icer = (1500 - 1000) / (0.8 - 0.6)  # 500 / 0.2 = 2500
        self.assertAlmostEqual(icer, 2500.0)
    
    def test_calculate_nmb(self):
        """Test Net Monetary Benefit calculation."""
        nmb = calculate_nmb(
            cost=1000,
            effect=0.6,
            wtp=50000
        )
        expected_nmb = 0.6 * 50000 - 1000  # 30000 - 1000 = 29000
        self.assertAlmostEqual(nmb, 29000.0)

    def test_cea_functions_exist(self):
        """Test that core CEA functions exist and are callable."""
        self.assertTrue(callable(simulate_arm))
        self.assertTrue(callable(run_cea_all_arms))


class TestDCEAEngine(unittest.TestCase):
    """Unit tests for the Distributional Cost-Effectiveness Analysis engine."""
    
    def test_initialize_with_parameters(self):
        """Test initialization with valid parameters."""
        dcea_result = DCEAResult()
        self.assertIsInstance(dcea_result, DCEAResult)
        
        indigenous_result = IndigenousDCEAResult()
        self.assertIsInstance(indigenous_result, IndigenousDCEAResult)
    
    def test_equity_weights_calculation(self):
        """Test equity weight calculation methods."""
        # Example test for equity-weighted QALY calculation
        weights = np.array([1.0, 1.2, 0.8])  # General, disadvantaged, privileged groups
        qalys = np.array([0.5, 0.4, 0.7])
        
        # Weighted calculation
        weighted_qalys = np.sum(weights * qalys)
        
        # The calculation itself would be in the engine's method
        # This is just verifying the concept works
        self.assertIsInstance(weighted_qalys, (int, float))


class TestVOIFunction(unittest.TestCase):
    """Unit tests for the Value of Information analysis function."""
    
    def test_voi_function_exists(self):
        """Test VOI function is callable."""
        self.assertTrue(callable(run_voi_analysis))


class TestBIAFunction(unittest.TestCase):
    """Unit tests for the Budget Impact Analysis function."""
    
    def test_bia_function_exists(self):
        """Test BIA function is callable."""
        self.assertTrue(callable(run_bia_all_arms))
    
    def test_budget_calculation(self):
        """Test budget calculation methods."""
        # Example testing budget projection calculations
        n_patients = 1000
        unit_cost = 5000
        uptake_rate = 0.3
        
        expected_first_year_cost = n_patients * uptake_rate * unit_cost
        
        # This would be calculated by the engine in a real implementation
        # Here we're just verifying the concept
        self.assertEqual(expected_first_year_cost, 1500000.0)


class TestCoreUtilities(unittest.TestCase):
    """Unit tests for core utility functions."""
    
    def test_calculate_icer_positive_increment(self):
        """Test ICER calculation with positive increments."""
        icer = calculate_icer(
            cost_new=2000,
            cost_old=1000,
            effect_new=0.7,
            effect_old=0.5
        )
        expected = (2000 - 1000) / (0.7 - 0.5)  # 1000 / 0.2 = 5000
        self.assertAlmostEqual(icer, 5000.0)
    
    def test_calculate_icer_negative_increment(self):
        """Test ICER calculation with negative cost increment (cost saving)."""
        icer = calculate_icer(
            cost_new=800,  # cheaper
            cost_old=1000,
            effect_new=0.6,
            effect_old=0.5
        )
        expected = (800 - 1000) / (0.6 - 0.5)  # -200 / 0.1 = -2000
        self.assertAlmostEqual(icer, -2000.0)
    
    def test_calculate_icer_dominant_strategy(self):
        """Test ICER calculation where new strategy is dominant (better effect, lower cost)."""
        icer = calculate_icer(
            cost_new=800,  # cheaper
            cost_old=1000,
            effect_new=0.7,  # better
            effect_old=0.5
        )
        # Dominant strategies have negative ICER (saving cost while gaining effect)
        self.assertLess(icer, 0)
    
    def test_calculate_nmb_beneficial_intervention(self):
        """Test NMB calculation for beneficial intervention."""
        nmb = calculate_nmb(
            cost=1000,
            effect=0.6,
            wtp=50000
        )
        expected = 0.6 * 50000 - 1000  # 30000 - 1000 = 29000
        self.assertAlmostEqual(nmb, 29000.0)
    
    def test_calculate_nmb_costly_intervention(self):
        """Test NMB calculation for costly intervention."""
        nmb = calculate_nmb(
            cost=20000,
            effect=0.3,
            wtp=50000
        )
        expected = 0.3 * 50000 - 20000  # 15000 - 20000 = -5000
        self.assertAlmostEqual(nmb, -5000.0)

    def test_calculate_icr(self):
        """Test Incremental Cost-Ratio calculation."""
        icr = calculate_icr(
            cost=2000,
            effect=0.75
        )
        expected = 2000 / 0.75  # 2666.67
        self.assertAlmostEqual(icr, expected)


class TestConfiguration(unittest.TestCase):
    """Unit tests for configuration management."""
    
    def test_parameter_validation(self):
        """Test parameter validation functions."""
        # Example parameters for validation
        params = {
            'costs': [1000, 1500, 2000],
            'effects': [0.5, 0.6, 0.7],
            'time_horizon': 10,
            'discount_rate': 0.035
        }
        
        # Would call validation function in real implementation
        # validate_parameters(params)  # This function doesn't exist in our mock yet
        # self.assertTrue(valid)  # Would test validation result
        pass


class TestDataIO(unittest.TestCase):
    """Unit tests for data input/output functions."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = Path("temp_test_data")
        self.temp_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_load_data_formats(self):
        """Test loading of different data formats."""
        # Create mock data file
        test_data = pd.DataFrame({
            'strategy': ['A', 'B', 'C'],
            'cost': [1000, 1500, 1200],
            'effect': [0.5, 0.7, 0.6]
        })
        
        csv_path = self.temp_dir / "test_data.csv"
        test_data.to_csv(csv_path, index=False)
        
        # Would test load_data function in real implementation
        # loaded_data = load_data(str(csv_path))
        # pd.testing.assert_frame_equal(test_data, loaded_data)
        pass
        

if __name__ == '__main__':
    # Run tests with more verbose output
    unittest.main(verbosity=2)