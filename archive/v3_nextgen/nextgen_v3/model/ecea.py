import pandas as pd
import numpy as np
from scipy.stats import lognorm

def compute_lognormal_params(mean, sd):
    """Compute mu, sigma for lognormal from mean and sd."""
    sigma2 = np.log(1 + (sd / mean)**2)
    mu = np.log(mean) - sigma2 / 2
    sigma = np.sqrt(sigma2)
    return mu, sigma

def run_ecea(inputs, out_dir='nextgen_v3/out/'):
    """Run Extended CEA for OoP and catastrophe."""
    oop_df = inputs.ecea_oop_inputs
    income_df = inputs.income_quintiles
    
    results = []
    for _, oop_row in oop_df.iterrows():
        arm = oop_row['Arm']
        jur = oop_row['Jurisdiction']
        group = oop_row['Group']
        mean_oop = oop_row['Mean_OoP_per_patient']
        sd_oop = oop_row['OoP_SD']
        _private_share = oop_row['PrivateShare']
        travel_oop = oop_row['Travel_OoP_per_patient']
        
        # Total OoP per patient
        total_oop_per_patient = mean_oop + travel_oop
        
        # Lognormal params
        mu, sigma = compute_lognormal_params(total_oop_per_patient, sd_oop)
        
        # For each quintile
        quintiles = income_df[(income_df['Jurisdiction'] == jur) & (income_df['Group'] == group)]
        for _, quintile_row in quintiles.iterrows():
            quintile = quintile_row['Quintile']
            _mean_income = quintile_row['Mean_Income']
            hh_size = quintile_row['HH_Size']
            threshold = quintile_row['Catastrophic_Threshold']
            
            # OoP per HH
            oop_per_hh = total_oop_per_patient * hh_size
            
            # Catastrophe rate: P(OoP > threshold)
            # For lognormal, use cdf
            catastrophe_rate = 1 - lognorm.cdf(threshold, s=sigma, scale=np.exp(mu))
            
            # OoP stats
            mean_oop_hh = oop_per_hh
            # SD from lognormal
            sd_oop_hh = np.sqrt((np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2)) * hh_size
            
            results.append({
                'arm': arm,
                'jurisdiction': jur,
                'group': group,
                'quintile': quintile,
                'mean_oop_hh': mean_oop_hh,
                'sd_oop_hh': sd_oop_hh,
                'catastrophe_rate': catastrophe_rate
            })
    
    df = pd.DataFrame(results)
    df.to_csv(f'{out_dir}/ecea_results_v3.csv', index=False)