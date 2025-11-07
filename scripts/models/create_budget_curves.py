#!/usr/bin/env python3
"""
Generate Budget Impact Curves from BIA Results
- Creates line charts showing cumulative budget impact over time
- Outputs budget_impact_curves_{country}.png
"""
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def create_budget_impact_curve(country="AU"):
    logger.info(f"Starting budget impact curve generation for {country}")

    # Load BIA results
    bia_file = f"bia_results_{country}.csv"
    if not os.path.exists(bia_file):
        logger.warning(f"BIA results not found: {bia_file}")
        print(f"BIA results not found: {bia_file}")
        return

    bia_data = pd.read_csv(bia_file)

    # Calculate cumulative impact
    bia_data['cumulative_impact'] = bia_data['net_impact'].cumsum()

    # Create budget impact curve
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Annual impact
    ax1.bar(bia_data['year'], bia_data['net_impact'], color='skyblue', alpha=0.7,
            label='Annual Impact')
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Budget Impact ($)')
    ax1.set_title(f'Annual Budget Impact\n{country}')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Add value labels on bars
    for i, v in enumerate(bia_data['net_impact']):
        ax1.text(i+1, v + (50000 if v >= 0 else -50000), f'${v:,.0f}',
                ha='center', va='bottom' if v >= 0 else 'top', fontweight='bold')

    # Cumulative impact
    ax2.plot(bia_data['year'], bia_data['cumulative_impact'], 'b-', linewidth=3,
             marker='o', markersize=8, label='Cumulative Impact')
    ax2.fill_between(bia_data['year'], 0, bia_data['cumulative_impact'],
                     alpha=0.3, color='blue')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Cumulative Budget Impact ($)')
    ax2.set_title(f'Cumulative Budget Impact\n{country}')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Add value labels on line
    for i, v in enumerate(bia_data['cumulative_impact']):
        ax2.text(i+1, v + (100000 if v >= 0 else -100000), f'${v:,.0f}',
                ha='center', va='bottom' if v >= 0 else 'top', fontweight='bold')

    plt.suptitle(f'Budget Impact Analysis: Ketamine vs ECT\n{country}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'budget_impact_curves_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved budget_impact_curves_{country}.png")

    # Print summary
    total_savings = bia_data['net_impact'].sum()
    print(f"Total 5-year budget impact in {country}: ${total_savings:,.0f}")
    print("Annual breakdown:")
    for _, row in bia_data.iterrows():
        print(f"  Year {int(row['year'])}: ${row['net_impact']:,.0f}")
    logger.info(".2f")

def main():
    for country in ["AU", "NZ"]:
        create_budget_impact_curve(country)

if __name__ == "__main__":
    main()
