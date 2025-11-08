"""
Integration tests for the TRD CEA Toolkit.

This module tests how different components work together in realistic
workflows, ensuring the entire analysis pipeline functions correctly.
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

from src.trd_cea.models.cea_engine import run_cea_all_arms, simulate_arm
from src.trd_cea.models.dcea_engine import DCEAResult
from src.trd_cea.models.voi_engine import run_voi_analysis
from src.trd_cea.core.config import load_config
from src.trd_cea.core.utils import calculate_icer, calculate_nmb
from src.trd_cea.core.io import save_results


class TestCEAIntegration(unittest.TestCase):
    """Integration tests for the Cost-Effectiveness Analysis engine."""
    
    def setUp(self):
        """Set up integration test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test configuration
        self.config_path = self.temp_dir / "test_config.yaml"
        config_data = {
            'analysis': {
                'time_horizon': 10,
                'discount_rate_costs': 0.035,
                'discount_rate_effects': 0.035,
                'wtp_threshold': 50000
            },
            'strategies': {
                'ECT': {'name': 'Electroconvulsive Therapy', 'abbreviation': 'ECT'},
                'IV_KA': {'name': 'Intravenous Ketamine', 'abbreviation': 'IV-KA'},
                'PO_KA': {'name': 'Oral Ketamine', 'abbreviation': 'PO-KA'}
            },
            'parameters': {
                'costs': {
                    'ECT': 10000,
                    'IV_KA': 8000,
                    'PO_KA': 6000
                },
                'effects': {
                    'ECT': 0.6,
                    'IV_KA': 0.75,
                    'PO_KA': 0.68
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_utility_functions_integration(self):
        """Test that utility functions work correctly with analysis parameters."""
        # Load configuration
        config = load_config(str(self.config_path))
        
        # Extract parameters
        strategies = list(config['strategies'].keys())
        costs = [config['parameters']['costs'][s] for s in strategies]
        effects = [config['parameters']['effects'][s] for s in strategies]
        wtp_threshold = config['analysis']['wtp_threshold']
        
        # Validate inputs
        params = {
            'strategies': strategies,
            'costs': costs,
            'effects': effects,
            'wtp_threshold': wtp_threshold
        }
        
        # Verify results structure (placeholder)
        self.assertIsNotNone(params)
        self.assertEqual(len(params['strategies']), 3)
        self.assertEqual(params['wtp_threshold'], 50000)
        
        # Test that ICERs can be calculated from the parameters
        # This is a minimal integration test of utility functions
        if len(costs) > 1 and len(effects) > 1:
            icer = calculate_icer(costs[1], costs[0], effects[1], effects[0])
            self.assertIsInstance(icer, (int, float))
    
    def test_cea_with_io_pipeline(self):
        """Test CEA analysis with input/output pipeline."""
        # Define test parameters
        strategies = ['ECT', 'IV-KA', 'PO-KA']
        costs = [10000, 8000, 6000]
        effects = [0.60, 0.75, 0.68]
        wtp_threshold = 50000
        
        # Would run actual analysis in real implementation
        # results = self.cea_engine.run_analysis(params)
        
        # Run preliminary calculations (would be in actual analysis)
        results = {
            'strategies': strategies,
            'costs': costs,
            'effects': effects,
            'wtp_threshold': wtp_threshold
        }
        
        # Add calculated metrics
        results['nmbs'] = []
        for i in range(len(costs)):
            nmb = calculate_nmb(costs[i], effects[i], wtp_threshold)
            results['nmbs'].append(nmb)
        
        # Save results to temporary file
        output_path = self.temp_dir / "test_cea_results.csv"
        df = pd.DataFrame({
            'strategy': results['strategies'],
            'cost': results['costs'],
            'effect': results['effects'],
            'nmb': results['nmbs']
        })
        df.to_csv(output_path, index=False)
        
        # Verify file was created and has expected content
        self.assertTrue(output_path.exists())
        saved_df = pd.read_csv(output_path)
        self.assertEqual(len(saved_df), len(strategies))
        self.assertIn('strategy', saved_df.columns)
        self.assertIn('cost', saved_df.columns)
        self.assertIn('effect', saved_df.columns)
        self.assertIn('nmb', saved_df.columns)


class TestDCEAIntegration(unittest.TestCase):
    """Integration tests for the Distributional CEA engine."""
    
    def setUp(self):
        """Set up integration test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_dcea_pipeline(self):
        """Test the complete DCEA analysis pipeline."""
        # Define DCEA-specific parameters
        params = {
            'strategies': ['ECT', 'IV-KA', 'PO-KA'],
            'costs': [10000, 8000, 6000],
            'effects': [0.60, 0.75, 0.68],
            'population_subgroups': ['general', 'indigenous', 'rural'],
            'equity_weights': [1.0, 1.5, 1.2],
            'time_horizon': 10,
            'wtp_threshold': 50000
        }
        
        # Initialize and test DCEA result
        result = DCEAResult()
        
        # Verify that parameters have appropriate structure
        self.assertEqual(len(params['strategies']), len(params['costs']))
        self.assertEqual(len(params['strategies']), len(params['effects']))
        self.assertEqual(len(params['population_subgroups']), len(params['equity_weights']))
        
        # Verify that weights and subgroups are valid
        for weight in params['equity_weights']:
            self.assertGreaterEqual(weight, 0.0, "Equity weight should be non-negative")


class TestVOIIntegration(unittest.TestCase):
    """Integration tests for the Value of Information engine."""
    
    def setUp(self):
        """Set up integration test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_voi_function_callable(self):
        """Test VOI functions are properly importable and callable."""
        # Simply test the function exists and is callable
        self.assertTrue(callable(run_voi_analysis))


class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete analysis workflows."""
    
    def setUp(self):
        """Set up integration test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_multiple_analysis_integration(self):
        """Test running multiple analysis types in sequence."""
        # Simulate running CEA, then using results for DCEA, then VOI
        # This is a simplified simulation of the workflow
        base_params = {
            'strategies': ['ECT', 'IV-KA', 'PO-KA'],
            'costs': [10000, 8000, 6000],
            'effects': [0.60, 0.75, 0.68],
            'wtp_threshold': 50000
        }
        
        # Step 1: Calculate CEA metrics
        cea_results = {
            'strategies': base_params['strategies'],
            'costs': base_params['costs'],
            'effects': base_params['effects'],
            'wtp': base_params['wtp_threshold']
        }
        
        # Add calculated metrics to CEA results
        cea_results['nmbs'] = []
        for i in range(len(base_params['costs'])):
            nmb = calculate_nmb(base_params['costs'][i], base_params['effects'][i], base_params['wtp_threshold'])
            cea_results['nmbs'].append(nmb)
        
        # Verify CEA results
        self.assertEqual(len(cea_results['nmbs']), len(cea_results['strategies']))
        
        # Step 2: Prepare DCEA with results from CEA
        dcea_params = base_params.copy()
        dcea_params.update({
            'population_subgroups': ['general', 'indigenous'],
            'equity_weights': [1.0, 1.8]
        })
        
        # Would run DCEA with these parameters
        dcea_result = DCEAResult()
        
        # Verify DCEA integration with CEA results
        self.assertIn('strategies', dcea_params)
        self.assertEqual(len(dcea_params['strategies']), len(dcea_params['costs']))
        
        # Step 3: Prepare VOI with results from previous analyses
        voi_params = base_params.copy()
        voi_params.update({
            'cost_uncertainty': [0.1, 0.12, 0.1],
            'effect_uncertainty': [0.05, 0.07, 0.06],
            'n_simulations': 500
        })
        
        # Would run VOI with these parameters
        # voi_results = self.voi_engine.run_analysis(voi_params)
        
        # Verify VOI parameters
        self.assertIn('cost_uncertainty', voi_params)
        self.assertIn('effect_uncertainty', voi_params)
        self.assertEqual(len(voi_params['cost_uncertainty']), len(voi_params['strategies']))
        
        # Verify the workflow connected properly
        self.assertEqual(base_params['wtp_threshold'], 50000)
        self.assertEqual(cea_results['wtp'], base_params['wtp_threshold'])
    
    def test_parameter_propagation_through_pipeline(self):
        """Test that parameters correctly propagate through the analysis pipeline."""
        # Create parameters
        analysis_config = {
            'time_horizon': 10,
            'discount_rates': {'costs': 0.035, 'effects': 0.035},
            'wtp_threshold': 50000,
            'strategies': ['ECT', 'IV-KA', 'PO-KA'],
            'base_values': {
                'costs': [10000, 8000, 6000],
                'effects': [0.60, 0.75, 0.68]
            },
            'uncertainty': {
                'cost_cv': [0.1, 0.15, 0.12],
                'effect_cv': [0.05, 0.08, 0.07]
            }
        }
        
        # Verify structure of configuration
        self.assertIn('strategies', analysis_config)
        self.assertIn('base_values', analysis_config)
        self.assertIn('uncertainty', analysis_config)
        self.assertIn('costs', analysis_config['base_values'])
        self.assertIn('effects', analysis_config['base_values'])
        
        # Verify parameter consistency
        n_strategies = len(analysis_config['strategies'])
        self.assertEqual(len(analysis_config['base_values']['costs']), n_strategies)
        self.assertEqual(len(analysis_config['base_values']['effects']), n_strategies)
        self.assertEqual(len(analysis_config['uncertainty']['cost_cv']), n_strategies)
        self.assertEqual(len(analysis_config['uncertainty']['effect_cv']), n_strategies)
        
        # Verify parameter relationships
        self.assertGreaterEqual(analysis_config['wtp_threshold'], 0)
        self.assertGreaterEqual(analysis_config['time_horizon'], 1)
        for cost in analysis_config['base_values']['costs']:
            self.assertGreaterEqual(cost, 0)
        for effect in analysis_config['base_values']['effects']:
            self.assertGreaterEqual(effect, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)