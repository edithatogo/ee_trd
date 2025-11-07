#!/usr/bin/env python3
"""
Two-way DSA Table Generator
Generates Table 10: Two-way sensitivity analysis results for CHEERS 2022 compliance.
"""

import pandas as pd
from pathlib import Path

def generate_two_way_dsa_table(country):
    """Generate two-way DSA summary table for a specific country."""
    base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Read two-way DSA data
    two_way_file = base_path / f'two_way_dsa_{country}.csv'
    if not two_way_file.exists():
        print(f"Warning: Two-way DSA file not found for {country}: {two_way_file}")
        return None

    df = pd.read_csv(two_way_file)

    # Get parameter names from columns
    param_cols = [col for col in df.columns if col not in ['Incremental_NMB', 'Cost_effective']]
    param1, param2 = param_cols

    # Create summary statistics
    total_combinations = len(df)
    cost_effective_combinations = len(df[df['Cost_effective'] == 'Yes'])
    cost_effective_percentage = (cost_effective_combinations / total_combinations) * 100

    # Find threshold values where cost-effectiveness changes
    # Group by param1 and find where cost-effectiveness switches
    threshold_analysis = []

    for param1_val in df[param1].unique():
        subset = df[df[param1] == param1_val].sort_values(param2)
        ce_changes = subset['Cost_effective'].ne(subset['Cost_effective'].shift()).cumsum()
        change_points = subset.groupby(ce_changes).first()

        if len(change_points) > 1:
            # Find the transition point
            ce_start = change_points.iloc[0]['Cost_effective']
            for i in range(1, len(change_points)):
                if change_points.iloc[i]['Cost_effective'] != ce_start:
                    threshold_val = change_points.iloc[i][param2]
                    threshold_analysis.append({
                        'Param1_Value': param1_val,
                        'Threshold_Param2': threshold_val,
                        'Cost_Effective': change_points.iloc[i]['Cost_effective']
                    })
                    break

    # Create summary table
    summary_data = {
        'Country': country,
        'Parameter_1': param1.replace('_', ' ').title(),
        'Parameter_2': param2.replace('_', ' ').title(),
        'Total_Combinations': total_combinations,
        'Cost_Effective_Combinations': cost_effective_combinations,
        'Cost_Effective_Percentage': f"{cost_effective_percentage:.1f}%"
    }

    # Add key threshold information
    if threshold_analysis:
        # Take the most representative threshold (middle range)
        mid_threshold = threshold_analysis[len(threshold_analysis)//2]
        summary_data['Key_Threshold_Param1'] = mid_threshold['Param1_Value']
        summary_data['Key_Threshold_Param2'] = mid_threshold['Threshold_Param2']
        summary_data['Cost_Effective_Region'] = 'Above threshold' if mid_threshold['Cost_Effective'] == 'Yes' else 'Below threshold'

    return pd.DataFrame([summary_data])

def main():
    """Generate two-way DSA summary table for both countries."""
    countries = ['AU', 'NZ']

    # Generate two-way DSA tables
    two_way_tables = []
    for country in countries:
        table = generate_two_way_dsa_table(country)
        if table is not None:
            two_way_tables.append(table)

    if two_way_tables:
        combined_table = pd.concat(two_way_tables, ignore_index=True)
        print("\nTwo-way DSA Results Table (Table 10):")
        print("=" * 100)
        print(combined_table.to_markdown(index=False))

        # Save to markdown file
        two_way_md_file = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/docs/two_way_dsa_table.md')
        with open(two_way_md_file, 'w') as f:
            f.write("# Two-way Sensitivity Analysis Results (Table 10)\n\n")
            f.write("Two-way sensitivity analysis showing cost-effectiveness regions for combinations of two parameters.\n\n")
            f.write(combined_table.to_markdown(index=False))
        print(f"Two-way DSA table saved to: {two_way_md_file}")

if __name__ == "__main__":
    main()