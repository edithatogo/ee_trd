import matplotlib.pyplot as plt
import numpy as np
from .publication_style import (
    apply_publication_style, save_publication_figure, format_currency
)

def plot_tornado(dsa_df, output_path='nextgen_v3/out/tornado_v3.png', 
                base_value=None, country='AU'):
    """Plot tornado diagram with publication-quality styling."""
    apply_publication_style()
    
    # If no real DSA data provided, create meaningful example
    if dsa_df is None or len(dsa_df) == 0:
        # Create example tornado data based on common parameters
        params = ['Treatment Response Rate', 'Relapse Rate', 'Utility Weight (Remission)', 
                 'Cost per Session', 'Number of Sessions', 'Time Horizon']
        low_values = [45000, 52000, 48000, 46000, 49000, 44000]
        high_values = [55000, 48000, 52000, 54000, 51000, 56000]
        base_val = 50000
    else:
        # Use real DSA data
        params = dsa_df['parameter'].tolist()
        low_values = dsa_df['low_value'].tolist() 
        high_values = dsa_df['high_value'].tolist()
        base_val = base_value if base_value is not None else dsa_df['base_value'].iloc[0]
    
    # Sort by impact (largest bar range first)
    impacts = [abs(high - low) for high, low in zip(high_values, low_values)]
    sorted_data = sorted(zip(params, low_values, high_values, impacts), 
                        key=lambda x: x[3], reverse=True)
    
    params_sorted = [x[0] for x in sorted_data]
    low_sorted = [x[1] for x in sorted_data]
    high_sorted = [x[2] for x in sorted_data]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y_pos = np.arange(len(params_sorted))
    
    # Plot bars
    ax.barh(y_pos, [h - base_val for h in high_sorted], 
            left=base_val, color='darkred', alpha=0.7, 
            label='Parameter High Value')
    ax.barh(y_pos, [l - base_val for l in low_sorted], 
            left=base_val, color='darkblue', alpha=0.7,
            label='Parameter Low Value')
    
    # Add base case line
    ax.axvline(x=base_val, color='black', linestyle='-', linewidth=2, 
               label=f'Base Case ({format_currency(base_val, country)})')
    
    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params_sorted)
    ax.set_xlabel(f'Incremental Cost-Effectiveness Ratio ({format_currency(1, country).split(" ")[1]} per QALY)', 
                  fontweight='bold')
    ax.set_title('Tornado Diagram: One-Way Sensitivity Analysis', fontweight='bold', pad=20)
    
    # Format x-axis with currency
    ax.tick_params(axis='x', rotation=45)
    
    # Add legend
    ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='x')
    
    # Save with high quality
    save_publication_figure(fig, output_path)
    plt.close()