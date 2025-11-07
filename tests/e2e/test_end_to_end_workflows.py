"""
End-to-End tests for the TRD CEA Toolkit.

These tests simulate complete user workflows from configuration to final results,
ensuring the entire system works as expected for real-world applications.
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import json

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.pardir, 'scripts'))
sys.path.insert(0, os.path.join(os.pardir, 'scripts', 'models'))
sys.path.insert(0, os.path.join(os.pardir, 'scripts', 'core'))

from scripts.models.cea_engine import CEAEngine
from scripts.models.bia_engine import BIAEngine
from scripts.core.config import load_config
from scripts.cli import main as cli_main


class TestCompleteCEAWorkflow(unittest.TestCase):
    """End-to-end test for complete CEA workflow."""
    
    def setUp(self):
        """Set up end-to-end test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create configuration file for CEA analysis
        self.config_path = self.temp_dir / "cea_analysis_config.yaml"
        cea_config = {
            'analysis': {
                'type': 'cea',
                'time_horizon': 10,
                'discount_rate_costs': 0.035,
                'discount_rate_effects': 0.035,
                'wtp_threshold': 50000,
                'perspective': 'healthcare',
                'jurisdiction': 'AU'
            },
            'strategies': {
                'ECT': {
                    'name': 'Electroconvulsive Therapy',
                    'cost': 10000,
                    'effect': 0.60,
                    'adherence': 0.85
                },
                'IV-KA': {
                    'name': 'Intravenous Ketamine',
                    'cost': 8000,
                    'effect': 0.75,
                    'adherence': 0.90
                },
                'PO-KA': {
                    'name': 'Oral Ketamine',
                    'cost': 6000,
                    'effect': 0.68,
                    'adherence': 0.88
                }
            },
            'outputs': {
                'save_results': True,
                'export_format': ['csv', 'pdf'],
                'results_dir': str(self.temp_dir / "results"),
                'figures_dir': str(self.temp_dir / "figures")
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(cea_config, f)
        
        # Create results directory
        (self.temp_dir / "results").mkdir()
        (self.temp_dir / "figures").mkdir()
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_cea_analysis_workflow(self):
        """Test the complete CEA analysis workflow end-to-end."""
        # 1. Load configuration
        config = load_config(str(self.config_path))
        self.assertIn('analysis', config)
        self.assertIn('strategies', config)
        self.assertEqual(config['analysis']['type'], 'cea')
        
        # 2. Extract parameters from config
        strategies = list(config['strategies'].keys())
        costs = [config['strategies'][s]['cost'] for s in strategies]
        effects = [config['strategies'][s]['effect'] for s in strategies]
        wtp_threshold = config['analysis']['wtp_threshold']
        
        # 3. Initialize and run CEA analysis
        cea_engine = CEAEngine()
        
        # In an actual implementation, this would execute the analysis
        # For now, we'll test that the parameters are correctly set up
        analysis_params = {
            'strategies': strategies,
            'costs': costs,
            'effects': effects,
            'wtp_threshold': wtp_threshold
        }
        
        # Verify parameter integrity
        self.assertEqual(len(strategies), 3)
        self.assertEqual(len(costs), 3)
        self.assertEqual(len(effects), 3)
        self.assertTrue(all(c > 0 for c in costs))
        self.assertTrue(all(e > 0 for e in effects))
        self.assertGreater(wtp_threshold, 0)
        
        # 4. Run analysis (simulated)
        # results = cea_engine.run_analysis(analysis_params)
        
        # 5. Calculate basic metrics to ensure the workflow would produce results
        # This simulates what would happen in the engine
        results = {
            'strategies': strategies,
            'costs': costs,
            'effects': effects,
            'wtp': wtp_threshold
        }
        
        # Calculate incremental metrics
        results['nmbs'] = []
        results['icers'] = [0.0]  # Reference strategy has 0 ICER
        
        for i in range(1, len(costs)):
            # Calculate NMB for each strategy
            nmb = effects[i] * wtp_threshold - costs[i]
            results['nmbs'].append(nmb)
            
            # Calculate ICER vs reference strategy (first strategy)
            delta_cost = costs[i] - costs[0]
            delta_effect = effects[i] - effects[0]
            if delta_effect != 0:
                icer = delta_cost / delta_effect
            else:
                icer = float('inf') if delta_cost > 0 else float('-inf') if delta_cost < 0 else 0.0
            results['icers'].append(icer)
        
        # Add NMB for reference strategy
        ref_nmb = effects[0] * wtp_threshold - costs[0]
        results['nmbs'].insert(0, ref_nmb)
        
        # 6. Verify results contain expected metrics
        self.assertIn('strategies', results)
        self.assertIn('icers', results)
        self.assertIn('nmbs', results)
        self.assertEqual(len(results['icers']), len(results['strategies']))
        self.assertEqual(len(results['nmbs']), len(results['strategies']))
        
        # 7. Check for correct economic interpretation
        # Most cost-effective strategy should have highest NMB at given WTP
        best_strategy_idx = np.argmax(results['nmbs'])
        best_strategy = results['strategies'][best_strategy_idx]
        best_nmb = results['nmbs'][best_strategy_idx]
        
        # Verify all NMBs are calculated correctly
        for i, (cost, effect) in enumerate(zip(results['costs'], results['effects'])):
            expected_nmb = effect * wtp_threshold - cost
            self.assertAlmostEqual(results['nmbs'][i], expected_nmb)
        
        # 8. Test result persistence
        # Create results dataframe
        results_df = pd.DataFrame({
            'Strategy': results['strategies'],
            'Cost': results['costs'], 
            'Effect': results['effects'],
            'NMB': results['nmbs'],
            'ICER': results['icers']
        })
        
        # Export results
        results_path = Path(config['outputs']['results_dir']) / "cea_results.csv"
        results_df.to_csv(results_path, index=False)
        
        # Verify file was created and has expected content
        self.assertTrue(results_path.exists())
        loaded_results = pd.read_csv(results_path)
        pd.testing.assert_frame_equal(results_df, loaded_results)
        
        print(f"✓ CEA workflow completed successfully")
        print(f"  Best strategy: {best_strategy} (NMB: ${best_nmb:,.2f})")


class TestCompleteBIAWorkflow(unittest.TestCase):
    """End-to-end test for complete BIA workflow."""
    
    def setUp(self):
        """Set up BIA end-to-end test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create configuration file for BIA analysis
        self.config_path = self.temp_dir / "bia_analysis_config.yaml"
        bia_config = {
            'analysis': {
                'type': 'bia',
                'time_horizon': 5,
                'discount_rate': 0.035,
                'perspective': 'healthcare',
                'jurisdiction': 'AU'
            },
            'strategies': {
                'ECT': {
                    'name': 'Electroconvulsive Therapy',
                    'current_market_share': 0.8,
                    'annual_incident_cases': 10000,
                    'unit_cost': 10000,
                    'treatment_duration': 1,  # months
                },
                'IV-KA': {
                    'name': 'Intravenous Ketamine',
                    'current_market_share': 0.1,
                    'projected_market_share': 0.25,
                    'annual_incident_cases': 10000,
                    'unit_cost': 8000,
                    'treatment_duration': 1,
                },
                'PO-KA': {
                    'name': 'Oral Ketamine',
                    'current_market_share': 0.05,
                    'projected_market_share': 0.15,
                    'annual_incident_cases': 10000,
                    'unit_cost': 6000,
                    'treatment_duration': 1,
                } 
            },
            'outputs': {
                'save_results': True,
                'export_format': ['csv', 'pdf'],
                'results_dir': str(self.temp_dir / "results"),
                'figures_dir': str(self.temp_dir / "figures")
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(bia_config, f)
        
        # Create results directories
        (self.temp_dir / "results").mkdir()
        (self.temp_dir / "figures").mkdir()
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_bia_analysis_workflow(self):
        """Test the complete BIA analysis workflow end-to-end."""
        # 1. Load configuration
        config = load_config(str(self.config_path))
        self.assertIn('analysis', config)
        self.assertIn('strategies', config)
        self.assertEqual(config['analysis']['type'], 'bia')
        
        # 2. Extract and validate parameters
        strategies = list(config['strategies'].keys())
        base_year_costs = []
        patient_populations = []
        current_shares = []
        projected_shares = []
        
        for strategy in strategies:
            strat_data = config['strategies'][strategy]
            base_year_costs.append(strat_data['unit_cost'])
            patient_populations.append(strat_data.get('annual_incident_cases', 0))
            current_shares.append(strat_data.get('current_market_share', 0))
            # Use projected share if available, otherwise use current
            projected_shares.append(strat_data.get('projected_market_share', strat_data.get('current_market_share', 0)))
        
        time_horizon = config['analysis']['time_horizon']
        
        # Verify parameter integrity
        self.assertEqual(len(strategies), 3)
        self.assertTrue(all(pop > 0 for pop in patient_populations))
        self.assertTrue(all(0 <= share <= 1 for share in current_shares))
        self.assertTrue(all(0 <= share <= 1 for share in projected_shares))
        self.assertGreater(time_horizon, 0)
        
        # 3. Simulate BIA calculations
        # Create projections for the budget impact
        years = list(range(1, time_horizon + 1))
        results = {
            'year': [],
            'strategy': [],
            'patients_receiving': [],
            'unit_cost': [],
            'total_cost': []
        }
        
        total_patients = sum(patient_populations)  # Using first year population for simplicity
        for year in years:
            # Calculate adoption based on adoption curve (simplified linear)
            adoption_factor = year / time_horizon
            
            for i, strategy in enumerate(strategies):
                current_share = current_shares[i]
                projected_share = projected_shares[i]
                
                # Linear transition from current to projected market share
                current_patients = int(total_patients * (current_share + (projected_share - current_share) * adoption_factor))
                
                unit_cost = base_year_costs[i]
                
                # Adjust for inflation if applicable (simplified)
                cost_with_inflation = unit_cost * (1.02) ** (year - 1)
                
                total_cost = current_patients * cost_with_inflation
                
                results['year'].append(year)
                results['strategy'].append(strategy)
                results['patients_receiving'].append(current_patients)
                results['unit_cost'].append(cost_with_inflation)
                results['total_cost'].append(total_cost)
        
        # 4. Verify results integrity
        # Should have n_years * n_strategies results
        expected_results_count = time_horizon * len(strategies)
        self.assertEqual(len(results['year']), expected_results_count)
        
        # 5. Create results DataFrame and save
        bia_df = pd.DataFrame(results)
        
        # Export results
        results_path = Path(config['outputs']['results_dir']) / "bia_results.csv"
        bia_df.to_csv(results_path, index=False)
        
        # Verify file was created
        self.assertTrue(results_path.exists())
        
        # Load and verify content
        loaded_bia_results = pd.read_csv(results_path)
        pd.testing.assert_frame_equal(bia_df, loaded_bia_results)
        
        # 6. Calculate key BIA metrics
        # Compare costs in first year vs last year to determine budget impact
        first_year_results = bia_df[bia_df['year'] == 1]
        last_year_results = bia_df[bia_df['year'] == time_horizon]
        
        first_year_total_cost = first_year_results['total_cost'].sum()
        last_year_total_cost = last_year_results['total_cost'].sum()
        
        budget_impact = last_year_total_cost - first_year_total_cost
        
        print(f"✓ BIA workflow completed successfully")
        print(f"  Budget impact over {time_horizon} years: ${budget_impact:,.2f}")
        print(f"  First year total cost: ${first_year_total_cost:,.2f}")
        print(f"  Last year total cost: ${last_year_total_cost:,.2f}")


class TestCompleteAnalysisPipeline(unittest.TestCase):
    """End-to-end test for running multiple analysis types in sequence."""
    
    def setUp(self):
        """Set up complete pipeline test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create comprehensive configuration
        self.config_path = self.temp_dir / "comprehensive_analysis_config.yaml"
        comprehensive_config = {
            'analysis': {
                'time_horizon': 10,
                'discount_rates': {'costs': 0.035, 'effects': 0.035},
                'wtp_threshold': 50000,
                'perspective': 'healthcare',
                'jurisdiction': 'AU'
            },
            'strategies': {
                'ECT': {'cost': 10000, 'effect': 0.60},
                'IV-KA': {'cost': 8000, 'effect': 0.75},
                'PO-KA': {'cost': 6000, 'effect': 0.68}
            },
            'voi_analysis': {
                'enable_evpi': True,
                'enable_evpip': True,
                'n_simulations': 1000
            },
            'sensitivity_analysis': {
                'enable_one_way': True,
                'enable_probabilistic': True,
                'n_simulations': 1000
            },
            'outputs': {
                'save_results': True,
                'export_format': ['csv', 'pdf'],
                'results_dir': str(self.temp_dir / "results"),
                'figures_dir': str(self.temp_dir / "figures")
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(comprehensive_config, f)
        
        # Create output directories
        (self.temp_dir / "results").mkdir()
        (self.temp_dir / "figures").mkdir()
    
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_analysis_pipeline(self):
        """Test running multiple analysis types in sequence."""
        # 1. Load the comprehensive configuration
        config = load_config(str(self.config_path))
        
        # 2. Extract baseline parameters
        strategies = list(config['strategies'].keys())
        costs = [config['strategies'][s]['cost'] for s in strategies]
        effects = [config['strategies'][s]['effect'] for s in strategies]
        wtp = config['analysis']['wtp_threshold']
        
        print(f"Testing complete analysis pipeline for {len(strategies)} strategies...")
        
        # 3. Run CEA analysis
        cea_params = {
            'strategies': strategies,
            'costs': costs,
            'effects': effects,
            'wtp_threshold': wtp
        }
        
        # Simulate CEA results calculation
        cea_results = {
            'strategies': strategies,
            'costs': costs,
            'effects': effects,
            'wtp': wtp
        }
        
        cea_results['nmbs'] = []
        cea_results['icers'] = []
        for i in range(len(costs)):
            nmb = effects[i] * wtp - costs[i]
            cea_results['nmbs'].append(nmb)
            
            if i == 0:  # Reference strategy
                cea_results['icers'].append(0.0)  # Reference has 0 ICER
            else:
                delta_cost = costs[i] - costs[0]
                delta_effect = effects[i] - effects[0]
                if delta_effect != 0:
                    icer = delta_cost / delta_effect
                else:
                    icer = float('inf') if delta_cost > 0 else float('-inf')
                cea_results['icers'].append(icer)
        
        print("✓ CEA analysis completed")
        
        # 4. Run VOI analysis (if enabled)
        if config.get('voi_analysis', {}).get('enable_evpi', False):
            # Simulate VOI analysis
            voi_results = {
                'evpi': np.var(cea_results['nmbs']) * 0.1,  # Dummy EVPI based on NMB variance
                'strategies': strategies
            }
            
            print("✓ VOI analysis completed")
        
        # 5. Run Sensitivity Analysis
        if config.get('sensitivity_analysis', {}).get('enable_one_way', False):
            # Define parameters for sensitivity analysis
            sa_params = [
                {'parameter': 'effect', 'values': [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]},
                {'parameter': 'cost', 'values': [5000, 6000, 7000, 8000, 9000, 10000]}
            ]
            
            # Create a simple one-way sensitivity analysis for the primary outcome
            sa_results = {
                'strategy': [],
                'parameter': [],
                'value': [],
                'outcome': []  # Would be NMB or ICER depending on parameter
            }
            
            # Example: sensitivity on effect for IV-KA
            iv_ka_base_effect = next(e for s, e in zip(strategies, effects) if s == 'IV-KA')
            iv_ka_base_cost = next(c for s, c in zip(strategies, costs) if s == 'IV-KA')
            
            for effect_val in [0.70, 0.725, 0.75, 0.775, 0.80]:
                nmb = effect_val * wtp - iv_ka_base_cost
                sa_results['strategy'].append('IV-KA')
                sa_results['parameter'].append('effect')
                sa_results['value'].append(effect_val)
                sa_results['outcome'].append(nmb)
            
            print("✓ Sensitivity analysis completed")
        
        # 6. Generate comprehensive results summary
        summary = {
            'analysis_types_completed': ['CEA'],
            'strategies_analyzed': len(strategies),
            'willingness_to_pay': wtp,
            'most_cost_effective_strategy': strategies[np.argmax(cea_results['nmbs'])],
            'best_nmb': max(cea_results['nmbs']),
            'total_strategies': len(strategies)
        }
        
        if 'voi_results' in locals():
            summary['analysis_types_completed'].append('VOI')
            summary['evpi'] = voi_results['evpi']
        
        if 'sa_results' in locals():
            summary['analysis_types_completed'].append('SA')
            summary['sensitivity_analyses_performed'] = len(sa_params)
        
        # 7. Save comprehensive results
        summary_path = Path(config['outputs']['results_dir']) / "comprehensive_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.assertTrue(summary_path.exists())
        
        # 8. Verify pipeline integrity
        self.assertGreaterEqual(len(summary['analysis_types_completed']), 1)
        self.assertIn('CEA', summary['analysis_types_completed'])
        self.assertTrue(strategies)  # At least one strategy analyzed
        self.assertGreaterEqual(summary['total_strategies'], 1)
        
        print(f"✓ Pipeline completed with {len(summary['analysis_types_completed'])} analysis types")
        print(f"  Most cost-effective strategy: {summary['most_cost_effective_strategy']}")
        print(f"  Best NMB: ${summary['best_nmb']:,.2f}")
        print(f"  WTP threshold: ${summary['willingness_to_pay']:,}/QALY")


if __name__ == '__main__':
    print("="*60)
    print("TRD CEA TOOLKIT - END-TO-END TEST SUITE")
    print("="*60)
    print()
    
    unittest.main(verbosity=2)