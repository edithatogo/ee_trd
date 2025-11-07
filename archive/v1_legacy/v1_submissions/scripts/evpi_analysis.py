"""
Expected Value of Perfect Information (EVPI) Analysis
- Calculates the value of eliminating all uncertainty
- Compares current expected NMB vs perfect information NMB
- Outputs evpi_{country}_{perspective}.csv and evpi_{country}_{perspective}.png
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

def calculate_evpi(country="AU", perspective="healthcare"):
    """Calculate Expected Value of Perfect Information"""

    # Load PSA results
    psa_file = f"psa_results_{country}_{perspective}.csv"
    if not os.path.exists(psa_file):
        print(f"PSA results not found: {psa_file}")
        return

    psa_data = pd.read_csv(psa_file)

    # WTP thresholds
    wtp_thresholds = np.arange(0, 100001, 5000)

    evpi_results = []

    for wtp in wtp_thresholds:
        # Current expected NMB (under uncertainty)
        current_enmb = psa_data['nmb'].mean()

        # Expected NMB under perfect information
        # This is the average of the maximum NMB for each iteration
        # (since with perfect information, we'd choose the best option)
        perfect_enmb = np.maximum(0, psa_data['nmb']).mean()

        # EVPI = Expected NMB with perfect information - Expected NMB under uncertainty
        evpi = perfect_enmb - current_enmb

        # Population EVPI (assuming 1000 patients per year)
        population_evpi = evpi * 1000

        evpi_results.append({
            'WTP_Threshold': wtp,
            'Current_ENMB': current_enmb,
            'Perfect_ENMB': perfect_enmb,
            'EVPI': max(0, evpi),  # EVPI cannot be negative
            'Population_EVPI': max(0, population_evpi)
        })

    # Save results
    df = pd.DataFrame(evpi_results)
    df.to_csv(f'evpi_{country}_{perspective}.csv', index=False)

    # Create EVPI plot
    plt.figure(figsize=(12, 8))

    plt.plot(df['WTP_Threshold']/1000, df['Population_EVPI']/1000,
            linewidth=3, marker='o', markersize=6, color='darkblue')

    plt.xlabel('Willingness-to-Pay Threshold ($ thousands per QALY)')
    plt.ylabel('Population Expected Value of Perfect Information ($ thousands)')
    plt.title(f'Expected Value of Perfect Information\n{country} - {perspective.title()} Perspective')
    plt.grid(True, alpha=0.3)

    # Add reference line at $50k/QALY
    plt.axvline(x=50, color='red', linestyle='--', alpha=0.7,
               label='$50,000 per QALY threshold')

    plt.legend()
    plt.tight_layout()
    plt.savefig(f'evpi_{country}_{perspective}.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved evpi_{country}_{perspective}.csv and evpi_{country}_{perspective}.png")

    # Print summary
    max_evpi = df['Population_EVPI'].max()
    max_evpi_wtp = df.loc[df['Population_EVPI'].idxmax(), 'WTP_Threshold']
    print(f"Maximum Population EVPI: ${max_evpi:,.0f} at ${max_evpi_wtp:,.0f} per QALY threshold")

def main():
    for country in ["AU", "NZ"]:
        for perspective in ["healthcare", "societal"]:
            calculate_evpi(country, perspective)

if __name__ == "__main__":
    main()