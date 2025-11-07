#!/usr/bin/env python3
"""
Subgroup and Scenario Analysis Tables Generator
Generates Table 8 (subgroup analysis) and Table 9 (scenario analysis) for CHEERS 2022 compliance.
"""

import pandas as pd
from pathlib import Path

def generate_subgroup_table(country):
    """Generate subgroup analysis table for a specific country."""
    base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Read subgroup analysis data
    subgroup_file = base_path / f'subgroup_analysis_{country}.csv'
    if not subgroup_file.exists():
        print(f"Warning: Subgroup analysis file not found for {country}: {subgroup_file}")
        return None

    df = pd.read_csv(subgroup_file)

    # Format the table for display
    df['Country'] = country
    df['Mean_NMB'] = df['Mean_NMB'].apply(lambda x: f"${x:,.0f}")
    df['Mean_Inc_Cost'] = df['Mean_Inc_Cost'].apply(lambda x: f"${x:,.0f}")
    df['Mean_Inc_QALY'] = df['Mean_Inc_QALY'].apply(lambda x: f"{x:.3f}")
    df['Prob_Cost_Effective'] = df['Prob_Cost_Effective'].apply(lambda x: f"{x:.1%}")

    # Select relevant columns
    result_df = df[['Country', 'Subgroup', 'Strategy', 'Mean_NMB', 'Mean_Inc_Cost', 'Mean_Inc_QALY', 'Prob_Cost_Effective']]

    return result_df

def generate_scenario_table(country):
    """Generate scenario analysis table for a specific country."""
    base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Read scenario analysis data
    scenario_file = base_path / f'scenario_analysis_{country}.csv'
    if not scenario_file.exists():
        print(f"Warning: Scenario analysis file not found for {country}: {scenario_file}")
        return None

    df = pd.read_csv(scenario_file)

    # Format the table for display
    df['Country'] = country
    df['Mean_NMB'] = df['Mean_NMB'].apply(lambda x: f"${x:,.0f}")
    df['Mean_Inc_Cost'] = df['Mean_Inc_Cost'].apply(lambda x: f"${x:,.0f}")
    df['Mean_Inc_QALY'] = df['Mean_Inc_QALY'].apply(lambda x: f"{x:.3f}")
    df['Prob_Cost_Effective'] = df['Prob_Cost_Effective'].apply(lambda x: f"{x:.1%}")

    # Select relevant columns
    result_df = df[['Country', 'Scenario', 'Description', 'Strategy', 'Mean_NMB', 'Mean_Inc_Cost', 'Mean_Inc_QALY', 'Prob_Cost_Effective']]

    return result_df

def main():
    """Generate subgroup and scenario analysis tables for both countries."""
    countries = ['AU', 'NZ']

    # Generate subgroup analysis tables
    subgroup_tables = []
    for country in countries:
        table = generate_subgroup_table(country)
        if table is not None:
            subgroup_tables.append(table)

    if subgroup_tables:
        combined_subgroup = pd.concat(subgroup_tables, ignore_index=True)
        print("\nSubgroup Analysis Results Table (Table 8):")
        print("=" * 100)
        print(combined_subgroup.to_markdown(index=False))

        # Save to markdown file
        subgroup_md_file = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/docs/subgroup_analysis_table.md')
        with open(subgroup_md_file, 'w') as f:
            f.write("# Subgroup Analysis Results (Table 8)\n\n")
            f.write("Subgroup analysis results showing cost-effectiveness by age, gender, and severity subgroups.\n\n")
            f.write(combined_subgroup.to_markdown(index=False))
        print(f"Subgroup analysis table saved to: {subgroup_md_file}")

    # Generate scenario analysis tables
    scenario_tables = []
    for country in countries:
        table = generate_scenario_table(country)
        if table is not None:
            scenario_tables.append(table)

    if scenario_tables:
        combined_scenario = pd.concat(scenario_tables, ignore_index=True)
        print("\nScenario Analysis Results Table (Table 9):")
        print("=" * 100)
        print(combined_scenario.to_markdown(index=False))

        # Save to markdown file
        scenario_md_file = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/docs/scenario_analysis_table.md')
        with open(scenario_md_file, 'w') as f:
            f.write("# Scenario Analysis Results (Table 9)\n\n")
            f.write("Scenario analysis results showing cost-effectiveness under different assumptions.\n\n")
            f.write(combined_scenario.to_markdown(index=False))
        print(f"Scenario analysis table saved to: {scenario_md_file}")

if __name__ == "__main__":
    main()