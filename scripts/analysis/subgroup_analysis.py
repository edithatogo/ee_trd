"""
Subgroup Analysis for Psychedelic Therapies vs ECT
- Analyzes cost-effectiveness by patient subgroups
- Subgroups: Age (young <35, middle 35-65, elderly >65), Gender, Severity
- Outputs subgroup_analysis_{country}.csv and plots
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

def create_subgroups(country="AU"):
    """Create simulated subgroup data based on PSA results"""
    # Load PSA results
    psa_file = f"psa_results_{country}.csv"
    if not os.path.exists(psa_file):
        print(f"PSA results not found: {psa_file}")
        return None

    psa_data = pd.read_csv(psa_file)

    # Since we don't have real subgroup data, we'll simulate subgroup effects
    # by applying differential effects to the base PSA results

    np.random.seed(42)  # For reproducibility

    # Define subgroup characteristics and their effects
    subgroups = {
        'Age_Young': {'effect_multiplier': 1.2, 'cost_multiplier': 0.9, 'name': 'Young (<35 years)'},
        'Age_Middle': {'effect_multiplier': 1.0, 'cost_multiplier': 1.0, 'name': 'Middle (35-65 years)'},
        'Age_Elderly': {'effect_multiplier': 0.8, 'cost_multiplier': 1.1, 'name': 'Elderly (>65 years)'},
        'Gender_Male': {'effect_multiplier': 1.1, 'cost_multiplier': 0.95, 'name': 'Male'},
        'Gender_Female': {'effect_multiplier': 0.95, 'cost_multiplier': 1.05, 'name': 'Female'},
        'Severity_Mild': {'effect_multiplier': 1.3, 'cost_multiplier': 0.8, 'name': 'Mild Depression'},
        'Severity_Moderate': {'effect_multiplier': 1.0, 'cost_multiplier': 1.0, 'name': 'Moderate Depression'},
        'Severity_Severe': {'effect_multiplier': 0.7, 'cost_multiplier': 1.2, 'name': 'Severe Depression'}
    }

    subgroup_results = []

    for subgroup_key, subgroup_info in subgroups.items():
        print(f"Analyzing subgroup: {subgroup_info['name']}")

        # Apply subgroup-specific effects to each PSA iteration
        subgroup_data = psa_data.copy()

        # Modify QALYs and costs based on subgroup characteristics
        effect_mult = subgroup_info['effect_multiplier']
        cost_mult = subgroup_info['cost_multiplier']

        # Apply effect multiplier to incremental QALYs (assuming differential treatment effects)
        subgroup_data['inc_qalys'] = subgroup_data['inc_qalys'] * effect_mult

        # Apply cost multiplier to incremental costs
        subgroup_data['inc_cost'] = subgroup_data['inc_cost'] * cost_mult

        # Recalculate NMB with WTP of 50,000
        wtp = 50000
        subgroup_data['nmb'] = subgroup_data['inc_qalys'] * wtp - subgroup_data['inc_cost']

        # Calculate summary statistics for this subgroup
        for strategy in ['Ketamine', 'Esketamine', 'Psilocybin']:
            strat_data = subgroup_data[subgroup_data['strategy'] == strategy]

            mean_nmb = strat_data['nmb'].mean()
            mean_inc_cost = strat_data['inc_cost'].mean()
            mean_inc_qaly = strat_data['inc_qalys'].mean()

            # Probability cost-effective (NMB > 0)
            prob_ce = (strat_data['nmb'] > 0).mean()

            subgroup_results.append({
                'Subgroup': subgroup_info['name'],
                'Subgroup_Type': subgroup_key.split('_')[0],
                'Strategy': strategy,
                'Mean_NMB': mean_nmb,
                'Mean_Inc_Cost': mean_inc_cost,
                'Mean_Inc_QALY': mean_inc_qaly,
                'Prob_Cost_Effective': prob_ce,
                'Effect_Multiplier': effect_mult,
                'Cost_Multiplier': cost_mult
            })

    return pd.DataFrame(subgroup_results)

def analyze_subgroups(country="AU"):
    """Perform subgroup analysis and create outputs"""
    results_df = create_subgroups(country)
    if results_df is None:
        return

    # Save results
    results_df.to_csv(f'subgroup_analysis_{country}.csv', index=False)

    # Create plots
    subgroup_types = ['Age', 'Gender', 'Severity']

    for subgroup_type in subgroup_types:
        type_data = results_df[results_df['Subgroup_Type'] == subgroup_type]

        if type_data.empty:
            continue

        # Plot NMB by subgroup and strategy
        plt.figure(figsize=(12, 8))

        subgroups = type_data['Subgroup'].unique()
        strategies = type_data['Strategy'].unique()

        x = np.arange(len(subgroups))
        width = 0.25

        for i, strategy in enumerate(strategies):
            strat_data = type_data[type_data['Strategy'] == strategy]
            plt.bar(x + i*width, strat_data['Mean_NMB'], width,
                   label=strategy, alpha=0.8)

        plt.xlabel(f'{subgroup_type} Subgroups')
        plt.ylabel('Mean Net Monetary Benefit ($)')
        plt.title(f'Net Monetary Benefit (NMB) by {subgroup_type} Subgroup\n{country}')
        plt.xticks(x + width, list(subgroups), rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'subgroup_analysis_{subgroup_type.lower()}_{country}.png', dpi=300, bbox_inches='tight')
        plt.close()

        # Plot probability cost-effective
        plt.figure(figsize=(12, 8))

        for i, strategy in enumerate(strategies):
            strat_data = type_data[type_data['Strategy'] == strategy]
            plt.bar(x + i*width, strat_data['Prob_Cost_Effective']*100, width,
                   label=strategy, alpha=0.8)

        plt.xlabel(f'{subgroup_type} Subgroups')
        plt.ylabel('Probability Cost-Effective (%)')
        plt.title(f'Probability of Cost-Effectiveness by {subgroup_type} Subgroup\n{country}')
        plt.xticks(x + width, list(subgroups), rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'subgroup_prob_ce_{subgroup_type.lower()}_{country}.png', dpi=300, bbox_inches='tight')
        plt.close()

    print(f"Saved subgroup analysis results for {country}")

    # Print summary
    print(f"\nSubgroup Analysis Summary for {country}:")
    for subgroup_type in subgroup_types:
        type_data = results_df[results_df['Subgroup_Type'] == subgroup_type]
        if not type_data.empty:
            print(f"\n{subgroup_type} Subgroups:")
            for _, row in type_data.iterrows():
                print(f"  {row['Subgroup']} - {row['Strategy']}: "
                     f"NMB=${row['Mean_NMB']:.0f}, "
                     f"P(CE)={row['Prob_Cost_Effective']:.1%}")

def main():
    for country in ["AU", "NZ"]:
        analyze_subgroups(country)

if __name__ == "__main__":
    main()