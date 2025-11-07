"""
Generate Tornado Diagrams from DSA Results
- Creates visual tornado diagrams showing parameter impact
- Outputs tornado_diagrams_{country}.png
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

def create_tornado_diagram(country="AU"):
    # Load DSA results
    dsa_file = f"dsa_results_{country}.csv"
    if not os.path.exists(dsa_file):
        print(f"DSA results not found: {dsa_file}")
        return

    dsa_data = pd.read_csv(dsa_file)

    # Calculate impact for each parameter (absolute difference from base)
    dsa_data['Impact'] = np.abs(dsa_data['NMB_high'] - dsa_data['NMB_base'])

    # Sort by impact (descending)
    dsa_sorted = dsa_data.sort_values('Impact', ascending=True)

    # Create tornado diagram
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot bars
    y_pos = np.arange(len(dsa_sorted))
    _bars_low = ax.barh(y_pos, dsa_sorted['NMB_low'] - dsa_sorted['NMB_base'],
                       left=dsa_sorted['NMB_base'], height=0.8,
                       color='lightcoral', alpha=0.7, label='Low value')
    _bars_high = ax.barh(y_pos, dsa_sorted['NMB_high'] - dsa_sorted['NMB_base'],
                        left=dsa_sorted['NMB_base'], height=0.8,
                        color='lightgreen', alpha=0.7, label='High value')

    # Add base case line
    ax.axvline(x=dsa_sorted['NMB_base'].iloc[0], color='black', linestyle='--',
               linewidth=1, label='Base case')

    # Customize plot
    ax.set_yticks(y_pos)
    ax.set_yticklabels(dsa_sorted['Parameter'])
    ax.set_xlabel('Incremental NMB ($)')
    ax.set_title(f'Tornado Diagram: Parameter Impact on Cost-Effectiveness\n{country}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add impact values on the right
    for i, (idx, row) in enumerate(dsa_sorted.iterrows()):
        impact = row['Impact']
        ax.text(ax.get_xlim()[1] * 0.02, i, f'±${impact:.0f}',
                va='center', ha='left', fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'tornado_diagrams_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved tornado_diagrams_{country}.png")

    # Print top 5 most influential parameters
    top_5 = dsa_sorted.tail(5)[['Parameter', 'Impact']].reset_index(drop=True)
    print(f"\nTop 5 most influential parameters in {country}:")
    for i in range(len(top_5)):
        row = top_5.iloc[i]
        print(f"{i+1}. {row['Parameter']}: ±${row['Impact']:.0f}")

def main():
    for country in ["AU", "NZ"]:
        create_tornado_diagram(country)

if __name__ == "__main__":
    main()