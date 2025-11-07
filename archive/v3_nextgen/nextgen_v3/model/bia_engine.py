import pandas as pd
import numpy as np

def adoption_curve(year, max_adoption=1.0, inflection=2.5, steepness=1.0):
    """Sigmoid adoption curve."""
    return max_adoption / (1 + np.exp(-steepness * (year - inflection)))

def compute_bia(arm, jurisdiction, settings, inputs, base_arm='ECT_std'):
    """Compute 5-year BIA for arm vs base."""
    years = 5
    results = []
    for year in range(1, years + 1):
        adoption = adoption_curve(year)
        # TODO: Compute costs with constraints (theatre slots, anaesthetist FTE)
        # For now, stub
        cost = 100000 * adoption  # example
        base_cost = 80000  # stub
        incremental_cost = cost - base_cost
        results.append({
            'year': year,
            'arm': arm,
            'adoption': adoption,
            'cost': cost,
            'base_cost': base_cost,
            'incremental_cost': incremental_cost
        })
    return pd.DataFrame(results)

def run_bia_all_arms(settings_path, inputs, out_dir='nextgen_v3/out/'):
    """Run BIA for all arms, output by jurisdiction."""
    import yaml
    with open(settings_path, 'r') as f:
        settings = yaml.safe_load(f)

    for jur in settings['jurisdictions']:
        results = []
        for arm in settings['arms']:
            if arm != 'ECT_std':  # vs base
                df = compute_bia(arm, jur, settings, inputs)
                results.append(df)
        if results:
            all_df = pd.concat(results)
            all_df.to_csv(f'{out_dir}/bia_summary_{jur}_v3.csv', index=False)