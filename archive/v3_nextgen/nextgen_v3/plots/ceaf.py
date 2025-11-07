import matplotlib.pyplot as plt
from .publication_style import (
    apply_publication_style, get_therapy_color, get_therapy_label,
    save_publication_figure, configure_ceaf_plot, add_publication_legend
)

def plot_ceaf(ceaf_df, output_path='nextgen_v3/out/ceaf_v3.png', 
              max_wtp=75000, country='AU'):
    """Plot CEAF with publication-quality styling."""
    apply_publication_style()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot with proper therapy names and colors
    for arm in ceaf_df['arm'].unique():
        arm_data = ceaf_df[ceaf_df['arm'] == arm]
        ax.plot(arm_data['wtp'], arm_data['prob_optimal'], 
                label=get_therapy_label(arm), 
                color=get_therapy_color(arm),
                linewidth=2.5)
    
    # Configure plot with optimized settings
    configure_ceaf_plot(ax, max_wtp, country)
    
    # Add professional legend
    add_publication_legend(ax)
    
    # Save with high quality
    save_publication_figure(fig, output_path)
    plt.close()