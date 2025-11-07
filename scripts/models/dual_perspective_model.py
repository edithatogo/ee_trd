#!/usr/bin/env python3
"""
Dual-Perspective Economic Evaluation Model
Integrates health system and societal perspectives with proper cost categorization
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
from datetime import datetime

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

# Set reproducible seed
SEED = int(os.environ.get('SEED', 20250929))
np.random.seed(SEED)

class DualPerspectiveModel:
    """Economic evaluation model supporting both health system and societal perspectives"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.config = self.load_configuration()
        self.health_system_costs = self.load_health_system_costs()
        self.societal_costs = self.load_societal_costs()
        self.clinical_data = self.load_clinical_data()
        
    def load_configuration(self):
        """Load repository configuration"""
        config = {
            'currency': 'AUD',
            'price_year': 2024,
            'country': 'AU',
            'perspectives': ['health_system', 'societal'],
            'wtp_threshold': 50000,
            'horizon': 5,
            'discount_rate': 0.05
        }
        
        # Load from config files
        try:
            with open(self.base_path / 'config/strategies.yml', 'r') as f:
                strategies_config = yaml.safe_load(f)
                config.update(strategies_config)
        except Exception:
            pass
            
        try:
            with open(self.base_path / 'config/analysis_v2_defaults.yml', 'r') as f:
                analysis_config = yaml.safe_load(f)
                config.update({
                    'lambda_single': analysis_config.get('lambda_single', 50000),
                    'lambda_min': analysis_config.get('lambda_min', 0),
                    'lambda_max': analysis_config.get('lambda_max', 75000),
                })
        except Exception:
            pass
            
        return config
    
    def load_health_system_costs(self):
        """Load health system perspective costs"""
        try:
            df = pd.read_csv(self.base_path / 'data/cost_inputs_au.csv')
            return df
        except Exception as e:
            logger.warning(f"Could not load health system costs - {e}")
            return pd.DataFrame()
    
    def load_societal_costs(self):
        """Load societal perspective costs"""
        try:
            # Load societal configuration
            with open(self.base_path / 'inputs/societal/perspective_societal.yml', 'r') as f:
                societal_config = yaml.safe_load(f)
            
            # Convert nested config to flat DataFrame for easier handling
            societal_params = []
            
            def flatten_config(config_dict, prefix=''):
                for key, value in config_dict.items():
                    if isinstance(value, dict):
                        if 'value' in value and 'unit' in value:
                            # This is a parameter
                            societal_params.append({
                                'parameter': value.get('variable', f"{prefix}_{key}"),
                                'value': value['value'],
                                'unit': value['unit'],
                                'category': prefix.split('_')[0] if prefix else key
                            })
                        else:
                            # This is a nested category
                            flatten_config(value, f"{prefix}_{key}" if prefix else key)
            
            flatten_config(societal_config)
            return pd.DataFrame(societal_params)
            
        except Exception as e:
            logger.warning(f"Could not load societal costs - {e}")
            return pd.DataFrame()
    
    def load_clinical_data(self):
        """Load clinical effectiveness data"""
        try:
            # Try to load from multiple sources
            clinical_files = [
                'results/v3_corrected_test/cea_results.csv',
                'data/clinical_inputs.csv'
            ]
            
            for file_path in clinical_files:
                try:
                    df = pd.read_csv(self.base_path / file_path)
                    if 'Arm' in df.columns or 'strategy' in df.columns:
                        return df
                except Exception:
                    continue
            
            # Generate synthetic clinical data if no files found
            return self.generate_synthetic_clinical_data()
            
        except Exception as e:
            logger.warning(f"Using synthetic clinical data - {e}")
            return self.generate_synthetic_clinical_data()
    
    def generate_synthetic_clinical_data(self):
        """Generate synthetic clinical effectiveness data for demonstration"""
        strategies = ['Usual care', 'ECT', 'ECT-KA', 'IV-KA', 'IN-EKA', 'PO psilocybin', 'PO-KA']
        
        # Base effectiveness and costs (health system perspective)
        base_data = {
            'Usual care': {'effect': 0.0, 'hs_cost': 0},
            'ECT': {'effect': 2.378, 'hs_cost': 9788},
            'ECT-KA': {'effect': 2.378, 'hs_cost': 13688}, 
            'IV-KA': {'effect': 2.397, 'hs_cost': 18988},
            'IN-EKA': {'effect': 2.397, 'hs_cost': 32163},
            'PO psilocybin': {'effect': 2.397, 'hs_cost': 42163},
            'PO-KA': {'effect': 2.397, 'hs_cost': 1404}
        }
        
        clinical_data = []
        for strategy in strategies:
            data = base_data.get(strategy, {'effect': 1.0, 'hs_cost': 5000})
            clinical_data.append({
                'Arm': strategy,
                'Effect': data['effect'],
                'HS_Cost': data['hs_cost']
            })
        
        return pd.DataFrame(clinical_data)
    
    def calculate_societal_costs_per_strategy(self, strategy):
        """Calculate additional societal costs for a strategy"""
        
        # Get societal parameters
        societal_params = {}
        for _, row in self.societal_costs.iterrows():
            societal_params[row['parameter']] = row['value']
        
        # Strategy-specific societal cost calculations
        
        # Patient time costs (per episode)
        time_cost_per_visit = (
            societal_params.get('patient_time_cost_per_hour', 45.50) * 
            (societal_params.get('patient_waiting_time_per_visit', 0.75) + 
             societal_params.get('patient_travel_time_per_visit', 1.25))
        )
        
        # Travel costs (per episode) 
        travel_cost_per_visit = max(
            societal_params.get('patient_travel_cost_per_km', 0.85) * 
            societal_params.get('patient_average_distance_to_facility', 28.0),
            societal_params.get('patient_public_transport_cost_per_trip', 12.50)
        )
        
        # Strategy-specific visit patterns
        visit_patterns = {
            'Usual care': {'sessions': 0, 'intensity': 'low'},
            'ECT': {'sessions': 12, 'intensity': 'high'},  # Initial + maintenance
            'ECT-KA': {'sessions': 12, 'intensity': 'high'},
            'IV-KA': {'sessions': 24, 'intensity': 'medium'},  # Multiple sessions
            'IN-EKA': {'sessions': 16, 'intensity': 'medium'}, 
            'PO psilocybin': {'sessions': 8, 'intensity': 'high'},  # Intensive therapy
            'PO-KA': {'sessions': 4, 'intensity': 'low'}  # Oral - fewer visits
        }
        
        pattern = visit_patterns.get(strategy, {'sessions': 8, 'intensity': 'medium'})
        
        # Patient costs
        patient_time_cost = time_cost_per_visit * pattern['sessions']
        patient_travel_cost = travel_cost_per_visit * pattern['sessions']
        
        # Out-of-pocket costs (annual)
        patient_oop_costs = (
            societal_params.get('patient_copayment_per_session', 85.0) * pattern['sessions'] +
            societal_params.get('medication_oop_cost_annual', 420.0) + 
            societal_params.get('ancillary_oop_costs', 680.0)
        )
        
        # Productivity losses
        absenteeism_cost = 0
        if pattern['intensity'] in ['medium', 'high']:
            days_lost = societal_params.get('absenteeism_days_per_episode', 8.5)
            if pattern['intensity'] == 'high':
                days_lost *= 1.5  # More intensive treatments
            
            absenteeism_cost = (
                days_lost * societal_params.get('productivity_loss_per_absence_day', 385.0)
            )
        
        # Presenteeism (reduced productivity while at work)
        weeks_affected = pattern['sessions'] * 0.5  # Assume 0.5 weeks impact per session
        presenteeism_cost = (
            weeks_affected * 5 * 8 *  # 5 days * 8 hours per week
            societal_params.get('patient_time_cost_per_hour', 45.50) *
            societal_params.get('presenteeism_productivity_loss', 0.35)
        )
        
        # Informal caregiver costs
        caregiver_weeks = pattern['sessions'] * 0.25  # Intensive support during treatment
        caregiver_cost = (
            caregiver_weeks *
            societal_params.get('informal_caregiver_time_per_week', 12.5) *
            societal_params.get('informal_care_replacement_cost', 65.0)
        )
        
        # Total societal costs
        total_societal_cost = (
            patient_time_cost + patient_travel_cost + patient_oop_costs +
            absenteeism_cost + presenteeism_cost + caregiver_cost
        )
        
        return {
            'patient_time_cost': patient_time_cost,
            'patient_travel_cost': patient_travel_cost,
            'patient_oop_costs': patient_oop_costs,
            'absenteeism_cost': absenteeism_cost,
            'presenteeism_cost': presenteeism_cost,
            'caregiver_cost': caregiver_cost,
            'total_societal_cost': total_societal_cost,
            'sessions': pattern['sessions'],
            'intensity': pattern['intensity']
        }
    
    def compute_dual_perspective_outcomes(self):
        """Compute economic outcomes for both perspectives"""
        
        results = {
            'health_system': [],
            'societal': []
        }
        
        for _, row in self.clinical_data.iterrows():
            strategy = row['Arm']
            effect = row['Effect']
            hs_cost = row.get('HS_Cost', row.get('Cost', 0))
            
            # Calculate societal costs
            societal_breakdown = self.calculate_societal_costs_per_strategy(strategy)
            total_societal_cost = hs_cost + societal_breakdown['total_societal_cost']
            
            # Health system perspective results
            hs_inmb = self.config['lambda_single'] * effect - hs_cost
            results['health_system'].append({
                'strategy': strategy,
                'effect': effect,
                'cost': hs_cost,
                'inmb': hs_inmb,
                'perspective': 'health_system'
            })
            
            # Societal perspective results  
            soc_inmb = self.config['lambda_single'] * effect - total_societal_cost
            results['societal'].append({
                'strategy': strategy,
                'effect': effect,
                'cost': total_societal_cost,
                'hs_cost': hs_cost,
                'societal_add_cost': societal_breakdown['total_societal_cost'],
                'inmb': soc_inmb,
                'perspective': 'societal',
                **societal_breakdown  # Include cost breakdown
            })
        
        return results
    
    def generate_psa_samples(self, n_samples=100):
        """Generate PSA samples for both perspectives"""
        
        psa_results = {
            'health_system': [],
            'societal': []
        }
        
        base_outcomes = self.compute_dual_perspective_outcomes()
        
        for i in range(n_samples):
            # Add parameter uncertainty
            np.random.seed(SEED + i)  # Ensure reproducibility
            
            for perspective in ['health_system', 'societal']:
                for outcome in base_outcomes[perspective]:
                    # Add uncertainty to effects (±20%)
                    effect_sample = outcome['effect'] * np.random.normal(1.0, 0.2)
                    effect_sample = max(0, effect_sample)
                    
                    # Add uncertainty to costs (±25%)
                    cost_sample = outcome['cost'] * np.random.normal(1.0, 0.25)
                    cost_sample = max(0, cost_sample)
                    
                    # Calculate INMB
                    inmb_sample = self.config['lambda_single'] * effect_sample - cost_sample
                    
                    psa_sample = {
                        'iteration': i,
                        'strategy': outcome['strategy'],
                        'effect': effect_sample,
                        'cost': cost_sample,
                        'inmb': inmb_sample,
                        'perspective': perspective
                    }
                    
                    psa_results[perspective].append(psa_sample)
        
        return psa_results
    
    def calculate_ceac_data(self, psa_results, wtp_range=None):
        """Calculate cost-effectiveness acceptability curves for both perspectives"""
        
        if wtp_range is None:
            wtp_range = np.arange(0, 100001, 5000)
        
        ceac_results = {
            'health_system': [],
            'societal': []
        }
        
        for perspective in ['health_system', 'societal']:
            psa_df = pd.DataFrame(psa_results[perspective])
            strategies = psa_df['strategy'].unique()
            
            for wtp in wtp_range:
                # Calculate NMB at this WTP for each iteration
                wtp_results = []
                
                for iteration in psa_df['iteration'].unique():
                    iter_data = psa_df[psa_df['iteration'] == iteration]
                    best_strategy = None
                    best_nmb = -np.inf
                    
                    for strategy in strategies:
                        strategy_data = iter_data[iter_data['strategy'] == strategy]
                        if len(strategy_data) > 0:
                            effect = strategy_data['effect'].iloc[0]
                            cost = strategy_data['cost'].iloc[0]
                            nmb = wtp * effect - cost
                            
                            if nmb > best_nmb:
                                best_nmb = nmb
                                best_strategy = strategy
                    
                    wtp_results.append(best_strategy)
                
                # Calculate probabilities
                for strategy in strategies:
                    prob = np.mean([s == strategy for s in wtp_results if s is not None])
                    
                    ceac_results[perspective].append({
                        'wtp_threshold': wtp,
                        'strategy': strategy,
                        'probability': prob,
                        'perspective': perspective
                    })
        
        return ceac_results

def main():
    """Main function to create dual-perspective model"""
    logger.info("Creating Dual-Perspective Economic Evaluation Model...")

    base_path = Path("/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT")

    # Initialize model
    logger.info("Initializing dual-perspective model...")
    model = DualPerspectiveModel(base_path)

    # Compute outcomes for both perspectives
    logger.info("Computing economic outcomes...")
    outcomes = model.compute_dual_perspective_outcomes()

    # Generate PSA samples
    logger.info("Generating PSA samples...")
    psa_results = model.generate_psa_samples(n_samples=100)

    # Calculate CEAC
    logger.info("Calculating CEAC data...")
    ceac_results = model.calculate_ceac_data(psa_results)

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = base_path / f"outputs/data_vNEXT_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save results
    logger.info(f"Saving results to {output_dir.name}...")

    # Deterministic outcomes
    for perspective in ['health_system', 'societal']:
        df = pd.DataFrame(outcomes[perspective])
        df.to_csv(output_dir / f"outcomes_{perspective}.csv", index=False)

        # PSA results
        psa_df = pd.DataFrame(psa_results[perspective])
        psa_df.to_csv(output_dir / f"psa_{perspective}.csv", index=False)

        # CEAC results
        ceac_df = pd.DataFrame(ceac_results[perspective])
        ceac_df.to_csv(output_dir / f"ceac_{perspective}.csv", index=False)

    # Summary comparison
    comparison_data = []
    for perspective in ['health_system', 'societal']:
        df = pd.DataFrame(outcomes[perspective])
        best_strategy = df.loc[df['inmb'].idxmax()]

        comparison_data.append({
            'perspective': perspective,
            'best_strategy': best_strategy['strategy'],
            'best_inmb': best_strategy['inmb'],
            'best_cost': best_strategy['cost'],
            'best_effect': best_strategy['effect'],
            'num_strategies': len(df)
        })

    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv(output_dir / "perspective_comparison.csv", index=False)

    # Print summary
    logger.info("Dual-perspective model integration complete!")
    logger.info("Perspectives analyzed: health_system, societal")
    logger.info(f"Strategies evaluated: {len(outcomes['health_system'])}")
    logger.info("PSA iterations: 100 per perspective")

    logger.info("Best strategies by perspective:")
    for _, row in comparison_df.iterrows():
        logger.info(f"  {row['perspective'].replace('_', ' ').title()}: {row['best_strategy']} "
                   f"(INMB: ${row['best_inmb']:,.0f})")

    logger.info(f"Output directory: {output_dir}")
    logger.info("Files created:")
    for file in output_dir.glob("*.csv"):
        logger.info(f"  {file.name}")

    logger.info("Dual-perspective model creation completed successfully")

    return {
        'model': model,
        'outcomes': outcomes,
        'psa_results': psa_results,
        'ceac_results': ceac_results,
        'output_dir': output_dir,
        'comparison': comparison_df
    }

if __name__ == "__main__":
    main()
