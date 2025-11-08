"""
Test suite for TRD CEA data science toolkit.

This module tests the core functionalities of the health economic evaluation toolkit.
"""
import unittest
import sys
import os
import pandas as pd
import numpy as np


class TestCoreModules(unittest.TestCase):
    """Test that core modules can be imported and basic functionality works."""
    
    def test_core_imports(self):
        """Test that core modules can be imported."""
        try:
            from src.trd_cea.core import config
            from src.trd_cea.core import io
            from src.trd_cea.core import deltas
            from src.trd_cea.core import nmb
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")
    
    def test_config_module(self):
        """Test basic config functionality."""
        from src.trd_cea.core.config import load_config
        
        # Since we don't have actual config files in the expected locations,
        # we'll just test that the function exists and has the expected signature
        self.assertTrue(callable(load_config))
    
    def test_io_module(self):
        """Test basic I/O functionality."""
        from src.trd_cea.core.io import load_data, save_results
        
        # Test that functions exist
        self.assertTrue(callable(load_data))
        self.assertTrue(callable(save_results))
    
    def test_deltas_module(self):
        """Test basic deltas functionality."""
        from src.trd_cea.core.deltas import compute_deltas
        
        # Test that function exists
        self.assertTrue(callable(compute_deltas))
    
    def test_nmb_module(self):
        """Test basic NMB functionality."""
        from src.trd_cea.core.nmb import calculate_nmb
        
        # Test basic calculation
        cost = 1000
        effect = 0.5
        wtp = 50000
        
        nmb = calculate_nmb(cost, effect, wtp)
        expected_nmb = effect * wtp - cost
        self.assertEqual(nmb, expected_nmb)


class TestAnalysisEngines(unittest.TestCase):
    """Test that analysis engines can be imported and have basic functionality."""
    
    def test_cea_engine_import(self):
        """Test CEA engine import."""
        try:
            # Import the CEA engine
            from src.trd_cea.models.cea_engine import CEAEngine
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import CEA engine: {e}")
    
    def test_bia_engine_import(self):
        """Test BIA engine import."""
        try:
            from src.trd_cea.models.bia_engine import BIAEngine
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import BIA engine: {e}")
    
    def test_dcea_engine_import(self):
        """Test DCEA engine import."""
        try:
            from src.trd_cea.models.dcea_engine import DCEAEngine
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import DCEA engine: {e}")
    
    def test_voi_engine_import(self):
        """Test VOI engine import."""
        try:
            from src.trd_cea.models.voi_engine import VOIEngine
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import VOI engine: {e}")


class TestUtilities(unittest.TestCase):
    """Test utility functions."""
    
    def test_calculate_icer(self):
        """Test ICER calculation function."""
        from src.trd_cea.core.utils import calculate_icer
        
        # Test with known values
        icer = calculate_icer(1500, 1000, 0.8, 0.6)
        expected_icer = (1500 - 1000) / (0.8 - 0.6)  # 500 / 0.2 = 2500
        self.assertEqual(icer, expected_icer)
    
    def test_calculate_nmb(self):
        """Test NMB calculation function."""
        from src.trd_cea.core.utils import calculate_nmb
        
        # Test with known values
        nmb = calculate_nmb(1000, 0.6, 50000)
        expected_nmb = 0.6 * 50000 - 1000  # 30000 - 1000 = 29000
        self.assertEqual(nmb, expected_nmb)


if __name__ == '__main__':
    unittest.main()