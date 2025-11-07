#!/usr/bin/env python3
"""
Value of Information Tables Generator
Generates Table 6 (EVPI) and Table 7 (EVPPI) for the CHEERS 2022 compliance report.
"""

import pandas as pd
from pathlib import Path

def generate_evpi_table(country):
    """Generate EVPI table for a specific country."""
    base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Read EVPI data
    evpi_file = base_path / f'evpi_{country}.csv'
    if not evpi_file.exists():
        print(f"Warning: EVPI file not found for {country}: {evpi_file}")
        return None

    df = pd.read_csv(evpi_file)

    # Select key WTP thresholds (0, 25k, 45k/50k, 75k, 100k)
    key_thresholds = [0, 25000, 45000 if country == 'NZ' else 50000, 75000, 100000]
    evpi_table = df[df['WTP_Threshold'].isin(key_thresholds)].copy()

    # Format for display
    evpi_table['Country'] = country
    evpi_table['WTP_Threshold'] = evpi_table['WTP_Threshold'].apply(lambda x: f"${x:,.0f}")
    evpi_table['EVPI'] = evpi_table['EVPI'].apply(lambda x: f"${x:,.0f}")
    evpi_table['Population_EVPI'] = evpi_table['Population_EVPI'].apply(lambda x: f"${x:,.0f}")

    return evpi_table[['Country', 'WTP_Threshold', 'EVPI', 'Population_EVPI']]

def generate_evppi_table(country):
    """Generate EVPPI table for a specific country."""
    base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Read EVPPI data
    evppi_file = base_path / f'evppi_{country}.csv'
    if not evppi_file.exists():
        print(f"Warning: EVPPI file not found for {country}: {evppi_file}")
        return None

    df = pd.read_csv(evppi_file)

    # Select key WTP thresholds
    key_thresholds = [0, 25000, 45000 if country == 'NZ' else 50000, 75000, 100000]
    evppi_table = df[df['WTP_Threshold'].isin(key_thresholds)].copy()

    # Format for display
    evppi_table['Country'] = country
    evppi_table['WTP_Threshold'] = evppi_table['WTP_Threshold'].apply(lambda x: f"${x:,.0f}")
    evppi_table['EVPPI'] = evppi_table['EVPPI'].apply(lambda x: f"${x:,.0f}")
    evppi_table['Population_EVPPI'] = evppi_table['Population_EVPPI'].apply(lambda x: f"${x:,.0f}")
    evppi_table['Variance_Proportion'] = evppi_table['Variance_Proportion'].apply(lambda x: f"{x:.1%}")

    return evppi_table[['Country', 'Parameter_Group', 'WTP_Threshold', 'EVPPI', 'Population_EVPPI', 'Variance_Proportion']]

def main():
    """Generate EVPI and EVPPI tables for both countries."""
    countries = ['AU', 'NZ']

    # Generate EVPI tables
    evpi_tables = []
    for country in countries:
        table = generate_evpi_table(country)
        if table is not None:
            evpi_tables.append(table)

    if evpi_tables:
        combined_evpi = pd.concat(evpi_tables, ignore_index=True)
        print("\nEVPI Results Table (Table 6):")
        print("=" * 80)
        print(combined_evpi.to_markdown(index=False))

        # Save to markdown file
        evpi_md_file = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/docs/evpi_table.md')
        with open(evpi_md_file, 'w') as f:
            f.write("# EVPI Results (Table 6)\n\n")
            f.write("Expected Value of Perfect Information at different willingness-to-pay thresholds.\n\n")
            f.write(combined_evpi.to_markdown(index=False))
        print(f"EVPI table saved to: {evpi_md_file}")

    # Generate EVPPI tables
    evppi_tables = []
    for country in countries:
        table = generate_evppi_table(country)
        if table is not None:
            evppi_tables.append(table)

    if evppi_tables:
        combined_evppi = pd.concat(evppi_tables, ignore_index=True)
        print("\nEVPPI Results Table (Table 7):")
        print("=" * 80)
        print(combined_evppi.to_markdown(index=False))

        # Save to markdown file
        evppi_md_file = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/docs/evppi_table.md')
        with open(evppi_md_file, 'w') as f:
            f.write("# EVPPI Results (Table 7)\n\n")
            f.write("Expected Value of Partial Perfect Information for parameter groups.\n\n")
            f.write(combined_evppi.to_markdown(index=False))
        print(f"EVPPI table saved to: {evppi_md_file}")

if __name__ == "__main__":
    main()