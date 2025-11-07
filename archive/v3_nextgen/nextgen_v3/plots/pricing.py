import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from .publication_style import (
    apply_publication_style, get_therapy_color, get_therapy_label,
    save_publication_figure, configure_pricing_plot, add_publication_legend
)

def plot_pricing(psa_df, arms=['ECT_ket_anaesthetic', 'Esketamine', 'Psilocybin', 'Oral_ketamine'], 
                wtp_grid=[0, 25000, 50000], output_path='nextgen_v3/out/pricing_thresholds_v3.png', 
                csv_path='nextgen_v3/out/pricing_thresholds_v3.csv', max_price=50000, country='AU'):
    """Plot threshold price where INMB=0 with PSA bands and publication styling."""
    apply_publication_style()
    
    # Filter to specified jurisdiction and perspective for clarity
    df = psa_df[(psa_df['jurisdiction'] == country) & (psa_df['perspective'] == 'societal')].copy()
    
    results = []
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for arm in arms:
        if arm not in df['arm'].unique():
            continue
            
        arm_data = df[df['arm'] == arm].set_index('iteration')
        base_data = df[df['arm'] == 'ECT_std'].set_index('iteration')
        
        wtp_values = []
        mean_prices = []
        lower_cis = []
        upper_cis = []
        
        for wtp in wtp_grid:
            inc_qaly = arm_data['qaly'] - base_data['qaly']
            inc_cost = arm_data['cost'] - base_data['cost']
            # Threshold price where INMB=0: inc_qaly * wtp - inc_cost = price
            prices = inc_qaly * wtp - inc_cost
            
            mean_price = prices.mean()
            lower = np.percentile(prices, 2.5)
            upper = np.percentile(prices, 97.5)
            
            # Only include if within reasonable range
            if 0 <= mean_price <= max_price:
                wtp_values.append(wtp)
                mean_prices.append(mean_price)
                lower_cis.append(max(0, lower))
                upper_cis.append(min(max_price, upper))
            
            results.append({
                'wtp': wtp, 'arm': arm, 'mean_price': mean_price, 
                'lower_95': lower, 'upper_95': upper
            })
        
        # Plot with confidence intervals
        if wtp_values:
            color = get_therapy_color(arm)
            label = get_therapy_label(arm)
            
            ax.plot(wtp_values, mean_prices, color=color, label=label, linewidth=2.5)
            ax.fill_between(wtp_values, lower_cis, upper_cis, alpha=0.3, color=color)
    
    # Save data
    results_df = pd.DataFrame(results)
    results_df.to_csv(csv_path, index=False)
    
    # Configure plot
    configure_pricing_plot(ax, max_price, country)
    ax.set_title(f'Price-Probability Curves ({country} Societal Perspective)', fontweight='bold', pad=20)
    
    # Add professional legend
    add_publication_legend(ax)
    
    # Save with high quality
    save_publication_figure(fig, output_path)
    plt.close()
    for arm in arms:
        arm_res = results_df[results_df['arm'] == arm]
        plt.plot(arm_res['wtp'], arm_res['mean_price'], label=arm)
        plt.fill_between(arm_res['wtp'], arm_res['lower_95'], arm_res['upper_95'], alpha=0.3)
    
    plt.xlabel('WTP ($/QALY)')
    plt.ylabel('Threshold Price ($)')
    plt.legend()
    plt.savefig(output_path)
    plt.close()