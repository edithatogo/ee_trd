import matplotlib.pyplot as plt
from .publication_style import (
    apply_publication_style, get_therapy_color, get_therapy_label,
    save_publication_figure, get_currency_label, add_publication_legend
)

def plot_ceac(ceac_df, output_path='nextgen_v3/out/ceac_v3.png',
              max_wtp=75000, country='AU'):
    """Plot CEAC with publication-quality styling."""
    apply_publication_style()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot with proper therapy names and colors
    for arm in ceac_df['arm'].unique():
        arm_data = ceac_df[ceac_df['arm'] == arm]
        ax.plot(arm_data['wtp'], arm_data['prob_ce'], 
                label=get_therapy_label(arm),
                color=get_therapy_color(arm),
                linewidth=2.5)
    
    # Configure axes
    ax.set_xlim(0, max_wtp)
    ax.set_ylim(0, 1)
    ax.set_xlabel(f'Willingness-to-Pay Threshold ({get_currency_label(country)})', fontweight='bold')
    ax.set_ylabel('Probability Cost-Effective', fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add professional legend
    add_publication_legend(ax)
    
    # Save with high quality
    save_publication_figure(fig, output_path)
    plt.close()