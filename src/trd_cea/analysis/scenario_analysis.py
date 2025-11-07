"""
Scenario Analysis for Psychedelic Therapies vs ECT
- Tests alternative assumptions about key parameters
- Scenarios: Base case, Optimistic, Pessimistic, High cost, Low efficacy, etc.
- Outputs scenario_analysis_{country}.csv and plots
"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def run_scenario_analysis(country="AU"):
    """Run scenario analysis with alternative assumptions"""
    logger.info(f"Starting scenario analysis for {country}")

    # Load base case PSA results
    psa_file = f"psa_results_{country}.csv"
    if not os.path.exists(psa_file):
        logger.warning(f"PSA results not found: {psa_file}")
        return

    psa_data = pd.read_csv(psa_file)

    # Define scenarios with parameter modifications
    scenarios = {
        'Base_Case': {
            'name': 'Base Case',
            'effect_multiplier': 1.0,
            'cost_multiplier': 1.0,
            'description': 'Base case assumptions'
        },
        'Optimistic': {
            'name': 'Optimistic',
            'effect_multiplier': 1.5,  # 50% better efficacy
            'cost_multiplier': 0.8,   # 20% lower costs
            'description': 'Higher efficacy, lower costs'
        },
        'Pessimistic': {
            'name': 'Pessimistic',
            'effect_multiplier': 0.7,  # 30% worse efficacy
            'cost_multiplier': 1.3,   # 30% higher costs
            'description': 'Lower efficacy, higher costs'
        },
        'High_Cost': {
            'name': 'High Cost Scenario',
            'effect_multiplier': 1.0,
            'cost_multiplier': 1.5,   # 50% higher costs
            'description': 'All treatment costs 50% higher'
        },
        'Low_Efficacy': {
            'name': 'Low Efficacy Scenario',
            'effect_multiplier': 0.6,  # 40% lower efficacy
            'cost_multiplier': 1.0,
            'description': '40% lower treatment efficacy'
        },
        'Societal_Perspective': {
            'name': 'Societal Perspective',
            'effect_multiplier': 1.0,
            'cost_multiplier': 0.9,   # Include productivity gains
            'description': 'Includes societal benefits'
        },
        'Short_Time_Horizon': {
            'name': 'Short Time Horizon (2 years)',
            'effect_multiplier': 0.8,  # Effects diminish over time
            'cost_multiplier': 1.0,
            'description': '2-year time horizon'
        },
        'Long_Time_Horizon': {
            'name': 'Long Time Horizon (10 years)',
            'effect_multiplier': 1.2,  # Sustained benefits
            'cost_multiplier': 1.0,
            'description': '10-year time horizon'
        }
    }

    scenario_results = []

    for scenario_key, scenario_info in scenarios.items():
        logger.info(f"Running scenario: {scenario_info['name']}")

        # Apply scenario modifications to PSA data
        scenario_data = psa_data.copy()

        # Modify incremental outcomes based on scenario
        effect_mult = scenario_info['effect_multiplier']
        cost_mult = scenario_info['cost_multiplier']

        scenario_data['inc_qalys'] = scenario_data['inc_qalys'] * effect_mult
        scenario_data['inc_cost'] = scenario_data['inc_cost'] * cost_mult

        # Recalculate NMB
        wtp = 50000
        scenario_data['nmb'] = scenario_data['inc_qalys'] * wtp - scenario_data['inc_cost']

        # Calculate results for each strategy
        for strategy in ['Ketamine', 'Esketamine', 'Psilocybin']:
            strat_data = scenario_data[scenario_data['strategy'] == strategy]

            mean_nmb = strat_data['nmb'].mean()
            mean_inc_cost = strat_data['inc_cost'].mean()
            mean_inc_qaly = strat_data['inc_qalys'].mean()
            prob_ce = (strat_data['nmb'] > 0).mean()

            # Calculate ICER if incremental cost and QALY are both positive
            if mean_inc_qaly > 0 and mean_inc_cost > 0:
                icer = mean_inc_cost / mean_inc_qaly
            else:
                icer = np.nan

            scenario_results.append({
                'Scenario': scenario_info['name'],
                'Description': scenario_info['description'],
                'Strategy': strategy,
                'Mean_NMB': mean_nmb,
                'Mean_Inc_Cost': mean_inc_cost,
                'Mean_Inc_QALY': mean_inc_qaly,
                'Prob_Cost_Effective': prob_ce,
                'ICER': icer,
                'Effect_Multiplier': effect_mult,
                'Cost_Multiplier': cost_mult
            })

    logger.info("Completed scenario analysis calculations")
    return pd.DataFrame(scenario_results)

def create_scenario_plots(results_df, country="AU"):
    """Create plots for scenario analysis results"""
    logger.info(f"Creating scenario plots for {country}")

    # Plot NMB by scenario and strategy
    plt.figure(figsize=(14, 10))

    scenarios = results_df['Scenario'].unique()
    strategies = results_df['Strategy'].unique()

    x = np.arange(len(scenarios))
    width = 0.25

    for i, strategy in enumerate(strategies):
        strat_data = results_df[results_df['Strategy'] == strategy]
        plt.bar(x + i*width, strat_data['Mean_NMB'], width,
               label=strategy, alpha=0.8)

    plt.xlabel('Scenarios')
    plt.ylabel('Mean Net Monetary Benefit ($)')
    plt.title(f'Net Monetary Benefit (NMB) by Scenario and Strategy\n{country}')
    plt.xticks(x + width, list(scenarios), rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    nmb_plot = f'scenario_analysis_nmb_{country}.png'
    plt.savefig(nmb_plot, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved NMB plot: {nmb_plot}")

    # Plot probability cost-effective
    plt.figure(figsize=(14, 10))

    for i, strategy in enumerate(strategies):
        strat_data = results_df[results_df['Strategy'] == strategy]
        plt.bar(x + i*width, strat_data['Prob_Cost_Effective']*100, width,
               label=strategy, alpha=0.8)

    plt.xlabel('Scenarios')
    plt.ylabel('Probability Cost-Effective (%)')
    plt.title(f'Probability Cost-Effective by Scenario\n{country}')
    plt.xticks(x + width, list(scenarios), rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    prob_plot = f'scenario_analysis_prob_ce_{country}.png'
    plt.savefig(prob_plot, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved probability CE plot: {prob_plot}")

    # Plot ICER for scenarios where it's calculable
    icer_data = results_df.dropna(subset=['ICER'])
    if not icer_data.empty:
        plt.figure(figsize=(12, 8))

        for strategy in strategies:
            strat_icer = icer_data[icer_data['Strategy'] == strategy]
            if not strat_icer.empty:
                plt.scatter(strat_icer['Scenario'], strat_icer['ICER']/1000,
                           label=strategy, s=100, alpha=0.7)

        plt.xlabel('Scenarios')
        plt.ylabel('ICER ($ thousands per QALY)')
        plt.title(f'Incremental Cost-Effectiveness Ratios by Scenario\n{country}')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Add WTP threshold line
        plt.axhline(y=50, color='red', linestyle='--', alpha=0.7,
                   label='WTP Threshold ($50k/QALY)')
        plt.legend()

        plt.tight_layout()
        icer_plot = f'scenario_analysis_icer_{country}.png'
        plt.savefig(icer_plot, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved ICER plot: {icer_plot}")
    else:
        logger.info("No ICER data available for plotting")

def analyze_scenarios(country="AU"):
    """Perform scenario analysis and create outputs"""
    logger.info(f"Starting scenario analysis for {country}")

    results_df = run_scenario_analysis(country)
    if results_df is None:
        logger.error(f"Could not perform scenario analysis for {country} - no PSA data")
        return

    # Save results
    output_file = f'scenario_analysis_{country}.csv'
    results_df.to_csv(output_file, index=False)
    logger.info(f"Saved scenario analysis results: {output_file}")

    # Create plots
    create_scenario_plots(results_df, country)

    logger.info(f"Completed scenario analysis for {country}")

    # Print summary
    logger.info(f"Scenario Analysis Summary for {country}:")
    for scenario in results_df['Scenario'].unique():
        scenario_data = results_df[results_df['Scenario'] == scenario]
        logger.info(f"{scenario}:")

        base_case = scenario_data[scenario_data['Strategy'] == 'Ketamine']
        if not base_case.empty:
            logger.info(f"  Base case NMB: ${base_case['Mean_NMB'].iloc[0]:.0f}")

        for _, row in scenario_data.iterrows():
            if row['Strategy'] != 'Ketamine':  # Show incremental results
                logger.info(f"  {row['Strategy']}: NMB=${row['Mean_NMB']:.0f}, "
                           f"P(CE)={row['Prob_Cost_Effective']:.1%}")

def main():
    """Run scenario analysis for both countries"""
    logger.info("Starting scenario analysis for AU and NZ")

    for country in ["AU", "NZ"]:
        analyze_scenarios(country)

    logger.info("Scenario analysis completed for both countries")

if __name__ == "__main__":
    main()
