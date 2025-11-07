#!/usr/bin/env python3
"""
Cost Threshold Analysis for IV Ketamine vs ECT
Determines breakeven points where IV ketamine becomes cost-effective.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def cost_threshold_analysis(country):
    """Perform cost threshold analysis for IV ketamine vs ECT."""
    _base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Base parameters - adjusted for realistic cost threshold analysis
    base_params = {
        'AU': {
            'ect_cost': 1000,
            'ketamine_cost': 300,
            'ect_remission': 0.50,  # Slightly lower ECT effectiveness
            'ketamine_remission': 0.55,  # Slightly higher ketamine effectiveness
            'wtp': 50000
        },
        'NZ': {
            'ect_cost': 1000,
            'ketamine_cost': 350,
            'ect_remission': 0.50,
            'ketamine_remission': 0.55,
            'wtp': 45000
        }
    }

    params = base_params[country]

    # Create cost ranges
    ect_costs = np.linspace(500, 2000, 20)
    ketamine_costs = np.linspace(200, 800, 20)

    results = []

    for ect_cost in ect_costs:
        for ketamine_cost in ketamine_costs:
            # Calculate incremental outcomes
            inc_cost = ketamine_cost - ect_cost
            inc_qalys = params['ketamine_remission'] - params['ect_remission']
            nmb = inc_qalys * params['wtp'] - inc_cost

            cost_effective = nmb > 0

            results.append({
                'ECT_Cost': ect_cost,
                'Ketamine_Cost': ketamine_cost,
                'Incremental_Cost': inc_cost,
                'Incremental_QALYs': inc_qalys,
                'NMB': nmb,
                'Cost_Effective': cost_effective
            })

    return pd.DataFrame(results)

def find_breakeven_points(df, country):
    """Find breakeven cost combinations."""
    # Find where NMB = 0 (breakeven)
    breakeven = df[np.abs(df['NMB']) < 100]  # Within $100 of breakeven

    if len(breakeven) > 0:
        avg_ect_cost = breakeven['ECT_Cost'].mean()
        avg_ketamine_cost = breakeven['Ketamine_Cost'].mean()
        return avg_ect_cost, avg_ketamine_cost
    else:
        # Estimate from data
        cost_effective_region = df[df['Cost_Effective']]
        if len(cost_effective_region) > 0:
            return cost_effective_region['ECT_Cost'].max(), cost_effective_region['Ketamine_Cost'].min()
        return None, None

def main():
    """Run cost threshold analysis for both countries."""
    countries = ['AU', 'NZ']

    for country in countries:
        print(f"\nAnalyzing cost thresholds for {country}...")

        # Run analysis
        results_df = cost_threshold_analysis(country)

        # Find breakeven points
        ect_breakeven, ketamine_breakeven = find_breakeven_points(results_df, country)

        print(f"Breakeven point for {country}:")
        if ect_breakeven is not None and ketamine_breakeven is not None:
            print(f"  ECT cost threshold: ${ect_breakeven:,.0f}")
            print(f"  Ketamine cost threshold: ${ketamine_breakeven:,.0f}")
        else:
            print("  No clear breakeven point found in the analyzed range")
            # Show the most favorable region
            cost_effective = results_df[results_df['Cost_Effective']]
            if len(cost_effective) > 0:
                print("  Ketamine becomes cost-effective when:")
                print(f"    ECT cost > ${cost_effective['ECT_Cost'].max():,.0f}")
                print(f"    Ketamine cost < ${cost_effective['Ketamine_Cost'].min():,.0f}")

        # Save detailed results
        output_file = Path(f'/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/cost_threshold_analysis_{country}.csv')
        results_df.to_csv(output_file, index=False)

        # Create contour plot
        plt.figure(figsize=(10, 8))

        # Create meshgrid for contour plot
        ect_range = np.linspace(results_df['ECT_Cost'].min(), results_df['ECT_Cost'].max(), 20)
        ketamine_range = np.linspace(results_df['Ketamine_Cost'].min(), results_df['Ketamine_Cost'].max(), 20)
        ECT_grid, KETAMINE_grid = np.meshgrid(ect_range, ketamine_range)

        # Interpolate NMB values
        from scipy.interpolate import griddata
        NMB_grid = griddata(
            (results_df['ECT_Cost'], results_df['Ketamine_Cost']),
            results_df['NMB'],
            (ECT_grid, KETAMINE_grid),
            method='linear'
        )

        # Create contour plot
        cs = plt.contourf(ECT_grid, KETAMINE_grid, NMB_grid, levels=20, cmap='RdYlGn')
        plt.colorbar(cs, label='Net Monetary Benefit ($)')
        plt.contour(ECT_grid, KETAMINE_grid, NMB_grid, levels=[0], colors='black', linewidths=2)

        plt.xlabel('ECT Cost ($ per session)')
        plt.ylabel('IV Ketamine Cost ($ per session)')
        plt.title(f'{country} - Cost Threshold Analysis: IV Ketamine vs ECT\nBlack line shows breakeven (NMB = 0)')

        # Mark breakeven point
        if ect_breakeven and ketamine_breakeven:
            plt.plot(ect_breakeven, ketamine_breakeven, 'ro', markersize=10, label='Breakeven Point')
            plt.legend()

        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plot_file = Path(f'/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/cost_threshold_analysis_{country}.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"Contour plot saved to: {plot_file}")

        plt.close()

if __name__ == "__main__":
    main()