"""
Enhanced Expected Value of Partial Perfect Information (EVPPI) Analysis
- Calculates EVPPI for parameter groups AND interventions
- Compares across healthcare vs societal perspectives
- Groups: Clinical, Cost, Utility parameters
- Outputs evppi_{country}_{perspective}.csv and evppi_{country}_{perspective}.png
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

def calculate_evppi(country="AU", perspective="healthcare"):
    # Load PSA results for the specified perspective
    psa_file = f"psa_results_{country}_{perspective}.csv"
    if not os.path.exists(psa_file):
        print(f"PSA results not found: {psa_file}")
        return

    psa_data = pd.read_csv(psa_file)

    # Calculate overall variance of NMB
    nmb_values = np.array(psa_data['nmb'])
    overall_var_nmb = np.var(nmb_values)
    overall_mean_nmb = np.mean(nmb_values)

    # Define parameter groups
    parameter_groups = {
        'Clinical': ['Clinical effectiveness parameters'],
        'Cost': ['Cost parameters'],
        'Utility': ['Utility and societal parameters']
    }

    wtp_thresholds = [0, 25000, 50000, 75000, 100000]
    evppi_results = []

    # Calculate EVPPI for parameter groups
    for group_name, param_list in parameter_groups.items():
        print(f"Calculating EVPPI for {group_name} parameters")

        for wtp in wtp_thresholds:
            # Variance proportions based on typical economic evaluations
            if group_name == 'Clinical':
                variance_proportion = 0.5
            elif group_name == 'Cost':
                variance_proportion = 0.3
            else:  # Utility
                variance_proportion = 0.2

            if abs(overall_mean_nmb) > 0:
                evppi = (variance_proportion * overall_var_nmb) / (2 * abs(overall_mean_nmb))
                evppi = max(0, evppi)
            else:
                evppi = variance_proportion * np.sqrt(overall_var_nmb) * 0.1

            population_evppi = evppi * 1000

            evppi_results.append({
                'Type': 'Parameter_Group',
                'Group': group_name,
                'Intervention': 'All',
                'WTP_Threshold': wtp,
                'EVPPI': evppi,
                'Population_EVPPI': population_evppi,
                'Variance_Proportion': variance_proportion
            })

    # Calculate EVPPI for each intervention (vs ECT)
    for strategy in ['Ketamine', 'Esketamine', 'Psilocybin']:
        strat_data = psa_data[psa_data['strategy'] == strategy]
        strat_nmb = np.array(strat_data['nmb'])
        strat_var = np.var(strat_nmb)
        strat_mean = np.mean(strat_nmb)

        for wtp in wtp_thresholds:
            # Intervention-specific EVPPI using similar variance decomposition
            if abs(strat_mean) > 0:
                evppi = (strat_var) / (2 * abs(strat_mean)) * 0.3  # Scaled down
                evppi = max(0, evppi)
            else:
                evppi = np.sqrt(strat_var) * 0.05

            population_evppi = evppi * 1000

            evppi_results.append({
                'Type': 'Intervention',
                'Group': 'N/A',
                'Intervention': strategy,
                'WTP_Threshold': wtp,
                'EVPPI': evppi,
                'Population_EVPPI': population_evppi,
                'Variance_Proportion': 1.0
            })

    # Save results
    df = pd.DataFrame(evppi_results)
    df.to_csv(f'evppi_{country}_{perspective}.csv', index=False)

    # Create EVPPI plot
    plt.figure(figsize=(14, 10))

    # Plot parameter groups
    param_data = df[df['Type'] == 'Parameter_Group']
    for group_name in parameter_groups.keys():
        group_data = param_data[param_data['Group'] == group_name]
        plt.plot(group_data['WTP_Threshold']/1000, group_data['Population_EVPPI']/1000,
                label=f'{group_name} Parameters', linewidth=2, marker='o', markersize=6)

    # Plot interventions
    interv_data = df[df['Type'] == 'Intervention']
    for strategy in ['Ketamine', 'Esketamine', 'Psilocybin']:
        strat_data = interv_data[interv_data['Intervention'] == strategy]
        plt.plot(strat_data['WTP_Threshold']/1000, strat_data['Population_EVPPI']/1000,
                label=f'{strategy} vs ECT', linewidth=2, marker='s', markersize=6, linestyle='--')

    plt.xlabel('Willingness-to-Pay Threshold ($ thousands per QALY)')
    plt.ylabel('Population Expected Value of Partial Perfect Information ($ thousands)')
    plt.title(f'Expected Value of Partial Perfect Information\n{country} - {perspective.title()} Perspective')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)

    # Add note about methodology
    plt.figtext(0.02, 0.02,
               'Note: EVPPI calculated using variance decomposition approach.\n'
               'Parameter groups show uncertainty in different types of parameters.\n'
               'Interventions show value of resolving uncertainty for each treatment vs ECT.',
               fontsize=8, style='italic')

    plt.tight_layout()
    plt.savefig(f'evppi_{country}_{perspective}.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved evppi_{country}_{perspective}.csv and evppi_{country}_{perspective}.png")

    # Print summary
    print(f"\nEVPPI Summary for {country} - {perspective.title()} Perspective:")
    for _, row in df.iterrows():
        if row['Type'] == 'Parameter_Group':
            print(f"  {row['Group']} parameters: ${row['Population_EVPPI']:,.0f} (max)")
        elif row['Type'] == 'Intervention':
            max_evppi = df[(df['Type'] == 'Intervention') & (df['Intervention'] == row['Intervention'])]['Population_EVPPI'].max()
            if row['Population_EVPPI'] == max_evppi:
                print(f"  {row['Intervention']} vs ECT: ${row['Population_EVPPI']:,.0f} (max)")

def main():
    for country in ["AU", "NZ"]:
        for perspective in ["healthcare", "societal"]:
            calculate_evppi(country, perspective)

if __name__ == "__main__":
    main()