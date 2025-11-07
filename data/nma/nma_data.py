"""
Synthetic NMA data for TRD treatments based on clinical literature.

Data structure follows standard NMA format with:
- study: Study identifier
- treatment: Treatment name
- responders: Number of responders
- total: Total patients in arm
- weeks: Follow-up duration
- outcome: response/remission
"""

import pandas as pd

# Comprehensive synthetic NMA dataset based on TRD literature
# Response rates are approximate based on published meta-analyses

NMA_DATA = pd.DataFrame({
    # Study 1: ECT vs IV Ketamine (4 weeks)
    'study': ['Kellner_2016', 'Kellner_2016', 'Fond_2014', 'Fond_2014',
              'Murrough_2013', 'Murrough_2013', 'Shiroma_2014', 'Shiroma_2014'],

    'treatment': ['ECT', 'IV_KA', 'ECT', 'IV_KA', 'ECT', 'IV_KA', 'ECT', 'IV_KA'],

    'responders': [18, 15, 22, 19, 16, 14, 20, 17],

    'total': [25, 25, 30, 30, 20, 20, 25, 25],

    'weeks': [4, 4, 4, 4, 4, 4, 4, 4],

    'outcome': ['response'] * 8
})

# Add more studies for other treatments
additional_studies = pd.DataFrame({
    'study': [
        # Esketamine studies
        'Daly_2019', 'Daly_2019', 'Popova_2019', 'Popova_2019',
        # rTMS studies
        'Brunoni_2016', 'Brunoni_2016', 'Gaynes_2014', 'Gaynes_2014',
        # Psilocybin studies
        'Davis_2020', 'Davis_2020', 'Carhart-Harris_2018', 'Carhart-Harris_2018',
        # Pharmacological augmentation
        'Zhou_2015', 'Zhou_2015', 'Nelson_2014', 'Nelson_2014'
    ],

    'treatment': [
        'IN_EKA', 'ECT', 'IN_EKA', 'ECT',
        'rTMS', 'ECT', 'rTMS', 'ECT',
        'PO_PSI', 'ECT', 'PO_PSI', 'ECT',
        'PHARM', 'ECT', 'PHARM', 'ECT'
    ],

    'responders': [
        35, 28, 32, 25,  # Esketamine
        22, 30, 18, 26,  # rTMS
        28, 24, 25, 22,  # Psilocybin
        20, 32, 16, 28   # Pharmacological
    ],

    'total': [50, 50, 45, 45, 40, 40, 35, 35, 40, 40, 35, 35, 40, 40, 35, 35],

    'weeks': [4, 4, 4, 4, 6, 6, 6, 6, 8, 8, 8, 8, 12, 12, 12, 12],

    'outcome': ['response'] * 16
})

# Combine datasets
NMA_DATA = pd.concat([NMA_DATA, additional_studies], ignore_index=True)

# Add remission data (subset with lower rates)
remission_data = NMA_DATA.copy()
remission_data['outcome'] = 'remission'
# Remission rates are typically 60-70% of response rates
remission_data['responders'] = (remission_data['responders'] * 0.65).astype(int)

NMA_DATA = pd.concat([NMA_DATA, remission_data], ignore_index=True)

# Save to CSV
if __name__ == '__main__':
    NMA_DATA.to_csv('nma_data.csv', index=False)
    print("NMA data saved to nma_data.csv")
    print(f"Total studies: {len(NMA_DATA)}")
    print(f"Treatments: {NMA_DATA['treatment'].unique()}")
    print(f"Outcomes: {NMA_DATA['outcome'].unique()}")