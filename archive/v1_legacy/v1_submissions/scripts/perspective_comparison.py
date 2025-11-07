"""
Perspective Comparison Analysis
- Compares healthcare vs societal perspectives
- Shows differences in costs, QALYs, NMB, and cost-effectiveness
- Analyzes impact of including societal costs
- Outputs perspective_comparison_{country}.csv and plots
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

def compare_perspectives(country="AU"):
    """Compare healthcare vs societal perspectives"""

    # Load both perspective results
    healthcare_file = f"psa_results_{country}_healthcare.csv"
    societal_file = f"psa_results_{country}_societal.csv"

    if not os.path.exists(healthcare_file) or not os.path.exists(societal_file):
        print(f"PSA results not found for {country}")
        return

    hc_data = pd.read_csv(healthcare_file)
    soc_data = pd.read_csv(societal_file)

    comparison_results = []

    for strategy in ['Ketamine', 'Esketamine', 'Psilocybin']:
        hc_strat = hc_data[hc_data['strategy'] == strategy]
        soc_strat = soc_data[soc_data['strategy'] == strategy]

        # Calculate differences
        hc_mean_cost = hc_strat['cost'].mean()
        soc_mean_cost = soc_strat['cost'].mean()
        cost_difference = soc_mean_cost - hc_mean_cost

        hc_mean_qaly = hc_strat['qalys'].mean()
        soc_mean_qaly = soc_strat['qalys'].mean()
        qaly_difference = soc_mean_qaly - hc_mean_qaly

        hc_mean_nmb = hc_strat['nmb'].mean()
        soc_mean_nmb = soc_strat['nmb'].mean()
        nmb_difference = soc_mean_nmb - hc_mean_nmb

        hc_prob_ce = (hc_strat['nmb'] > 0).mean()
        soc_prob_ce = (soc_strat['nmb'] > 0).mean()
        prob_ce_difference = soc_prob_ce - hc_prob_ce

        # Calculate cost components
        societal_cost_breakdown = {
            'Productivity Loss': 5 * (2000 if country == 'AU' else 1800),  # 5 years
            'Informal Care': 5 * (10000 if country == 'AU' else 9000),    # 5 years
            'OOP Costs': 8 * (400 if country == 'AU' else 350) if strategy == 'ECT' else
                        8 * (100 if country == 'AU' else 90)  # Ketamine/OOP
        }

        total_societal_cost = sum(societal_cost_breakdown.values())

        comparison_results.append({
            'Strategy': strategy,
            'HC_Mean_Cost': hc_mean_cost,
            'Soc_Mean_Cost': soc_mean_cost,
            'Cost_Difference': cost_difference,
            'HC_Mean_QALY': hc_mean_qaly,
            'Soc_Mean_QALY': soc_mean_qaly,
            'QALY_Difference': qaly_difference,
            'HC_Mean_NMB': hc_mean_nmb,
            'Soc_Mean_NMB': soc_mean_nmb,
            'NMB_Difference': nmb_difference,
            'HC_Prob_CE': hc_prob_ce,
            'Soc_Prob_CE': soc_prob_ce,
            'Prob_CE_Difference': prob_ce_difference,
            'Total_Societal_Cost': total_societal_cost,
            'Productivity_Loss': societal_cost_breakdown['Productivity Loss'],
            'Informal_Care': societal_cost_breakdown['Informal Care'],
            'OOP_Costs': societal_cost_breakdown['OOP Costs']
        })

    # Save results
    df = pd.DataFrame(comparison_results)
    df.to_csv(f'perspective_comparison_{country}.csv', index=False)

    # Create comparison plots
    create_comparison_plots(df, country)

    print(f"Saved perspective_comparison_{country}.csv")

    # Print summary
    print(f"\nPerspective Comparison Summary for {country}:")
    print(f"Currency: {'AUD' if country == 'AU' else 'NZD'}")

    for _, row in df.iterrows():
        print(f"\n{row['Strategy']}:")
        print(".0f")
        print(".3f")
        print(".0f")
        print(".1%")
        print(".1%")
        print("+.1%")

def create_comparison_plots(df, country):
    """Create comparison plots"""

    strategies = df['Strategy'].values
    x = np.arange(len(strategies))

    # Cost comparison
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 3, 1)
    plt.bar(x - 0.2, df['HC_Mean_Cost'], 0.4, label='Healthcare', alpha=0.8)
    plt.bar(x + 0.2, df['Soc_Mean_Cost'], 0.4, label='Societal', alpha=0.8)
    plt.xlabel('Strategy')
    plt.ylabel(f'Mean Cost ({"AUD" if country == "AU" else "NZD"})')
    plt.title('Mean Costs by Perspective')
    plt.xticks(x, strategies)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # NMB comparison
    plt.subplot(2, 3, 2)
    plt.bar(x - 0.2, df['HC_Mean_NMB'], 0.4, label='Healthcare', alpha=0.8)
    plt.bar(x + 0.2, df['Soc_Mean_NMB'], 0.4, label='Societal', alpha=0.8)
    plt.xlabel('Strategy')
    plt.ylabel('Mean NMB ($)')
    plt.title('Mean Net Monetary Benefit (NMB) by Perspective')
    plt.xticks(x, strategies)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Probability CE comparison
    plt.subplot(2, 3, 3)
    plt.bar(x - 0.2, df['HC_Prob_CE']*100, 0.4, label='Healthcare', alpha=0.8)
    plt.bar(x + 0.2, df['Soc_Prob_CE']*100, 0.4, label='Societal', alpha=0.8)
    plt.xlabel('Strategy')
    plt.ylabel('Probability Cost-Effective (%)')
    plt.title('Probability of Cost-Effectiveness by Perspective')
    plt.xticks(x, strategies)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Cost difference
    plt.subplot(2, 3, 4)
    plt.bar(x, df['Cost_Difference'], color='red', alpha=0.7)
    plt.xlabel('Strategy')
    plt.ylabel(f'Cost Difference (Societal - Healthcare)\n({"AUD" if country == "AU" else "NZD"})')
    plt.title('Incremental Societal Costs')
    plt.xticks(x, strategies)
    plt.grid(True, alpha=0.3)

    # NMB difference
    plt.subplot(2, 3, 5)
    colors = ['green' if x > 0 else 'red' for x in df['NMB_Difference']]
    plt.bar(x, df['NMB_Difference'], color=colors, alpha=0.7)
    plt.xlabel('Strategy')
    plt.ylabel('NMB Difference (Societal - Healthcare) ($)')
    plt.title('Impact on NMB')
    plt.xticks(x, strategies)
    plt.grid(True, alpha=0.3)

    # Societal cost breakdown
    plt.subplot(2, 3, 6)
    bottom = np.zeros(len(strategies))
    components = ['Productivity_Loss', 'Informal_Care', 'OOP_Costs']
    labels = ['Productivity Loss', 'Informal Care', 'Out-of-Pocket']
    colors = ['lightblue', 'lightgreen', 'lightcoral']

    for i, (comp, label, color) in enumerate(zip(components, labels, colors)):
        plt.bar(x, df[comp], bottom=bottom, label=label, color=color, alpha=0.8)
        bottom += df[comp]

    plt.xlabel('Strategy')
    plt.ylabel(f'Societal Cost Components\n({"AUD" if country == "AU" else "NZD"})')
    plt.title('Societal Cost Breakdown')
    plt.xticks(x, strategies)
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.suptitle(f'Healthcare vs Societal Perspective Comparison - {country}', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'perspective_comparison_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Additional plot: Cost-effectiveness plane comparison
    create_ce_plane_comparison(country)

def create_ce_plane_comparison(country):
    """Create CE plane comparison between perspectives"""

    hc_file = f"psa_results_{country}_healthcare.csv"
    soc_file = f"psa_results_{country}_societal.csv"

    hc_data = pd.read_csv(hc_file)
    soc_data = pd.read_csv(soc_file)

    plt.figure(figsize=(16, 8))

    strategies = ['Ketamine', 'Esketamine', 'Psilocybin']
    colors = ['blue', 'red', 'green']

    for i, strategy in enumerate(strategies):
        # Healthcare perspective
        plt.subplot(1, 2, 1)
        hc_strat = hc_data[hc_data['strategy'] == strategy]
        plt.scatter(hc_strat['inc_qalys'], hc_strat['inc_cost'],
                   alpha=0.6, s=30, color=colors[i], edgecolors='black', linewidth=0.5,
                   label=strategy)

        # Societal perspective
        plt.subplot(1, 2, 2)
        soc_strat = soc_data[soc_data['strategy'] == strategy]
        plt.scatter(soc_strat['inc_qalys'], soc_strat['inc_cost'],
                   alpha=0.6, s=30, color=colors[i], edgecolors='black', linewidth=0.5,
                   label=strategy)

    # Add WTP line to both subplots
    wtp = 50000 if country == 'AU' else 45000
    qaly_range = np.linspace(-1, 1, 100)
    cost_line = wtp * qaly_range

    for subplot in [1, 2]:
        plt.subplot(1, 2, subplot)
        plt.plot(qaly_range, cost_line, color='black', linestyle='--', linewidth=2,
                label=f'WTP = ${wtp:,} per QALY')
        plt.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        plt.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        plt.xlabel('Incremental QALYs')
        plt.ylabel(f'Incremental Cost ({"AUD" if country == "AU" else "NZD"})')
        plt.grid(True, alpha=0.3)
        plt.legend()

    plt.subplot(1, 2, 1)
    plt.title(f'Healthcare Perspective - {country}')
    plt.subplot(1, 2, 2)
    plt.title(f'Societal Perspective - {country}')

    plt.suptitle(f'Cost-Effectiveness Planes: Healthcare vs Societal Perspectives - {country}', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'ce_planes_comparison_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    for country in ["AU", "NZ"]:
        compare_perspectives(country)

if __name__ == "__main__":
    main()