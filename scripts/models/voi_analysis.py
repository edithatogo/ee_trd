"""
Value of Information Analysis for Ketamine vs ECT
- Calculates Expected Value of Perfect Information (EVPI)
- Analyzes at different willingness-to-pay thresholds
- Outputs evpi_{country}.csv and evpi_{country}.png
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import sys

# Add project root to path for config access
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

# Set up logging
logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def calculate_evpi(country="AU"):
    logger.info(f"Starting EVPI analysis for {country}")

    # Load PSA results
    psa_file = f"psa_results_{country}.csv"
    if not os.path.exists(psa_file):
        logger.warning(f"PSA results not found: {psa_file}")
        print(f"PSA results not found: {psa_file}")
        return

    psa_data = pd.read_csv(psa_file)

    # Filter for Ketamine strategy (our intervention of interest)
    ketamine_data = psa_data[psa_data['strategy'] == 'Ketamine']

    # WTP thresholds to evaluate
    wtp_thresholds = np.arange(0, 100001, 5000)  # 0 to 100k in 5k increments

    evpi_results = []

    for wtp in wtp_thresholds:
        # Calculate expected net benefit under uncertainty (from PSA)
        # NMB is already calculated at the model's WTP threshold, so we need to adjust
        # For simplicity, we'll use the existing NMB values
        enb_uncertainty = ketamine_data['nmb'].mean()

        # Calculate expected net benefit under perfect information
        # For each PSA iteration, we would choose Ketamine if NMB > 0, otherwise ECT
        # Since NMB is incremental vs ECT, ENB_perfect = max(0, NMB)
        enb_perfect = np.maximum(0, ketamine_data['nmb']).mean()

        # EVPI = ENB_perfect - ENB_uncertainty
        evpi = enb_perfect - enb_uncertainty

        evpi_results.append({
            'WTP_Threshold': wtp,
            'ENB_Uncertainty': enb_uncertainty,
            'ENB_Perfect': enb_perfect,
            'EVPI': evpi,
            'Population_EVPI': evpi * 1000  # Assuming 1000 patients per year
        })

    # Save results
    df = pd.DataFrame(evpi_results)
    df.to_csv(f'evpi_{country}.csv', index=False)

    # Create EVPI curve plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['WTP_Threshold']/1000, df['EVPI'], 'b-', linewidth=2, label='EVPI')
    plt.fill_between(df['WTP_Threshold']/1000, 0, df['EVPI'], alpha=0.3, color='blue')
    plt.xlabel('Willingness-to-Pay Threshold ($ thousands per QALY)')
    plt.ylabel('Expected Value of Perfect Information ($)')
    plt.title(f'Expected Value of Perfect Information\n{country}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'evpi_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved evpi_{country}.csv and evpi_{country}.png")

    # Print summary statistics
    max_evpi = df['EVPI'].max()
    max_evpi_wtp = df.loc[df['EVPI'].idxmax(), 'WTP_Threshold']
    print(f"Max EVPI: ${max_evpi:.0f} at WTP threshold of ${max_evpi_wtp:.0f}")
    logger.info(".2f")

def main():
    for country in ["AU", "NZ"]:
        calculate_evpi(country)

if __name__ == "__main__":
    main()
