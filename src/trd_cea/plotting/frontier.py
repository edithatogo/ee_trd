import matplotlib.pyplot as plt
from .publication_style import (
    apply_publication_style, get_therapy_color, get_therapy_label,
    save_publication_figure, add_wtp_threshold_line, add_publication_legend,
    format_currency
)

def plot_frontier(cea_df, output_path='nextgen_v3/out/frontier_v3.png'):
    """Plot efficiency frontier."""
    apply_publication_style()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # TODO: Identify non-dominated arms
    ax.scatter(cea_df['total_qaly'], cea_df['total_cost'])
    ax.set_xlabel('QALYs', fontweight='bold')
    ax.set_ylabel('Cost', fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    save_publication_figure(fig, output_path)
    plt.close()

def plot_ce_plane(psa_df, output_path='nextgen_v3/out/ce_plane_v3.png', 
                 wtp_threshold=50000, country='AU', perspective='health_system'):
    """Plot cost-effectiveness plane with PSA uncertainty."""
    apply_publication_style()
    
    # Filter data
    df = psa_df[(psa_df['jurisdiction'] == country) & 
                (psa_df['perspective'] == perspective)].copy()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get base case (ECT_std)
    base_data = df[df['arm'] == 'ECT_std']
    base_cost = base_data['cost'].mean()
    base_qaly = base_data['qaly'].mean()
    
    # Plot each therapy
    for arm in df['arm'].unique():
        if arm == 'ECT_std':
            continue  # Skip base case
            
        arm_data = df[df['arm'] == arm]
        
        # Calculate incremental values
        inc_cost = arm_data['cost'] - base_cost
        inc_qaly = arm_data['qaly'] - base_qaly
        
        # Plot PSA scatter
        ax.scatter(inc_qaly, inc_cost, 
                  color=get_therapy_color(arm), 
                  alpha=0.6, s=30,
                  label=get_therapy_label(arm))
    
    # Add WTP threshold line
    add_wtp_threshold_line(ax, wtp_threshold, country)
    
    # Add quadrant lines
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Formatting
    ax.set_xlabel('Incremental QALYs', fontweight='bold')
    ax.set_ylabel(f'Incremental Cost ({format_currency(1, country).split(" ")[1]})', fontweight='bold')
    ax.set_title(f'Cost-Effectiveness Plane ({country} {perspective.title()} Perspective)', 
                fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    # Add legend
    add_publication_legend(ax)
    
    # Save with high quality
    save_publication_figure(fig, output_path)
    plt.close()

def plot_regret_curves(regret_df, output_path='nextgen_v3/out/regret_curves_v3.png',
                      max_wtp=75000, country='AU'):
    """Plot regret curves with publication styling."""
    apply_publication_style()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for arm in regret_df['arm'].unique():
        arm_data = regret_df[regret_df['arm'] == arm]
        ax.plot(arm_data['wtp'], arm_data['expected_regret'], 
                label=get_therapy_label(arm),
                color=get_therapy_color(arm),
                linewidth=2.5)
    
    ax.set_xlim(0, max_wtp)
    ax.set_xlabel(f'Willingness-to-Pay Threshold ({format_currency(1, country).split(" ")[1]} per QALY)', 
                  fontweight='bold')
    ax.set_ylabel('Expected Regret', fontweight='bold')
    ax.set_title('Expected Value of Perfect Information', fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    add_publication_legend(ax)
    
    save_publication_figure(fig, output_path)
    plt.close()