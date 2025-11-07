#!/usr/bin/env python3
"""
PSA Summary Statistics Generator
Generates Table 4: PSA summary statistics with mean, SD, and 95% CI
for incremental costs, QALYs, and NMB across all interventions.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def calculate_psa_summary(psa_file_path, country):
    """Calculate PSA summary statistics for a given country."""
    # Read PSA results
    df = pd.read_csv(psa_file_path)

    # Group by strategy and calculate statistics
    strategies = df['strategy'].unique()
    summary_data = []

    for strategy in strategies:
        strategy_data = df[df['strategy'] == strategy]

        # Calculate statistics for each metric
        for metric in ['inc_cost', 'inc_qalys', 'nmb']:
            values = strategy_data[metric].values
            mean_val = np.mean(values)
            std_val = np.std(values, ddof=1)  # Sample standard deviation
            ci_lower = np.percentile(values, 2.5)
            ci_upper = np.percentile(values, 97.5)

            summary_data.append({
                'Country': country,
                'Strategy': strategy,
                'Metric': metric,
                'Mean': mean_val,
                'SD': std_val,
                '95% CI Lower': ci_lower,
                '95% CI Upper': ci_upper
            })

    return pd.DataFrame(summary_data)

def format_psa_table(summary_df):
    """Format the summary dataframe into a readable table."""
    # Pivot the data for better presentation
    formatted_df = summary_df.pivot_table(
        index=['Country', 'Strategy'],
        columns='Metric',
        values=['Mean', 'SD', '95% CI Lower', '95% CI Upper']
    ).round(2)

    # Flatten column names
    formatted_df.columns = [f'{col[0]} ({col[1]})' for col in formatted_df.columns]
    formatted_df = formatted_df.reset_index()

    return formatted_df

def main():
    """Main function to generate PSA summary tables."""
    base_path = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT')

    # Process both countries
    countries = ['AU', 'NZ']
    all_summaries = []

    for country in countries:
        psa_file = base_path / f'psa_results_{country}_healthcare.csv'
        if psa_file.exists():
            print(f"Processing PSA results for {country}...")
            summary_df = calculate_psa_summary(psa_file, country)
            all_summaries.append(summary_df)
        else:
            print(f"Warning: PSA file not found for {country}: {psa_file}")

    if all_summaries:
        # Combine all summaries
        combined_df = pd.concat(all_summaries, ignore_index=True)

        # Save detailed summary
        output_file = base_path / 'psa_summary_statistics.csv'
        combined_df.to_csv(output_file, index=False)
        print(f"PSA summary statistics saved to: {output_file}")

        # Format and display table
        formatted_df = format_psa_table(combined_df)
        print("\nPSA Summary Statistics Table:")
        print("=" * 80)
        print(formatted_df.to_string(index=False))

        # Save formatted table as markdown
        markdown_file = base_path / 'docs' / 'psa_summary_table.md'
        with open(markdown_file, 'w') as f:
            f.write("# PSA Summary Statistics (Table 4)\n\n")
            f.write("Probabilistic sensitivity analysis results showing mean, standard deviation, and 95% confidence intervals for incremental costs, QALYs, and net monetary benefit.\n\n")
            f.write(formatted_df.to_markdown(index=False))
        print(f"Markdown table saved to: {markdown_file}")

if __name__ == "__main__":
    main()