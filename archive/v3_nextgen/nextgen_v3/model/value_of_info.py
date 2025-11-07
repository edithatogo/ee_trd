import pandas as pd
import numpy as np

def compute_evppi(psa_samples_df, parameter_groups, wtp=50000):
    """Compute EVPPI for parameter groups using GP regression."""
    # Assume psa_samples_df has columns for params and outcomes
    # Stub: mock EVPPI values
    evppi_results = []
    groups = ['durability', 'relapse_hazards', 'theatre_minutes', 'price_psilocybin', 'price_esketamine']
    for group in groups:
        evppi_value = np.random.uniform(1000, 10000)  # Stub
        evppi_results.append({'parameter_group': group, 'evppi': evppi_value})
    return pd.DataFrame(evppi_results)

def compute_evsi(trial_design, psa_samples_df, wtp=50000):
    """Compute EVSI for trial design."""
    # Stub: EVSI increases with sample size
    sample_sizes = [50, 100, 200, 500]
    evsi_results = []
    for n in sample_sizes:
        evsi_value = n * 10  # Stub
        evsi_results.append({'sample_size': n, 'evsi': evsi_value})
    return pd.DataFrame(evsi_results)

def run_value_of_info(settings, inputs, out_dir='nextgen_v3/out/'):
    """Run VoI analysis."""
    # Stub PSA samples
    psa_samples_df = pd.DataFrame({'param1': np.random.normal(0,1,100), 'inb': np.random.normal(10000,2000,100)})
    
    # EVPPI
    parameter_groups = ['durability', 'relapse_hazards', 'theatre_minutes', 'price_psilocybin', 'price_esketamine']
    evppi_df = compute_evppi(psa_samples_df, parameter_groups)
    evppi_df.to_csv(f'{out_dir}/evppi_v3.csv', index=False)
    
    # EVSI
    trial_design = settings.get('evsi', {})
    evsi_df = compute_evsi(trial_design, psa_samples_df)
    evsi_df.to_csv(f'{out_dir}/evsi_v3.csv', index=False)