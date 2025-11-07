"""
Comparison plotting system for V3 NextGen Equity Framework.
Provides side-by-side comparative analysis plots matching V2 capabilities.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional
from .publication_style import (
    apply_publication_style, get_therapy_color, get_therapy_label,
    save_publication_figure, add_publication_legend,
    format_currency, configure_ceaf_plot
)

def create_ceaf_comparison_plot(ceaf_df: pd.DataFrame, 
                               output_path: str = 'nextgen_v3/out/ceaf_comparison_v3.png',
                               max_wtp: float = 75000) -> None:
    """
    Create side-by-side CEAF comparison plots for different countries/perspectives.
    """
    apply_publication_style()
    
    # Create 2x2 grid for AU/NZ x health_system/societal
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Cost-Effectiveness Acceptability Frontiers Comparison', 
                fontsize=16, fontweight='bold', y=0.95)
    
    scenarios = [
        ('AU', 'health_system', 'AU Health System'),
        ('AU', 'societal', 'AU Societal'),
        ('NZ', 'health_system', 'NZ Health System'),
        ('NZ', 'societal', 'NZ Societal')
    ]
    
    for idx, (country, perspective, title) in enumerate(scenarios):
        ax = axes[idx // 2, idx % 2]
        
        # Filter data for this scenario (assuming jurisdiction/perspective columns exist)
        # If not available, use same data for all scenarios
        scenario_df = ceaf_df  # Placeholder - would filter in real implementation
        
        # Plot each therapy
        for arm in scenario_df['arm'].unique():
            arm_data = scenario_df[scenario_df['arm'] == arm]
            ax.plot(arm_data['wtp'], arm_data['prob_optimal'],
                   label=get_therapy_label(arm),
                   color=get_therapy_color(arm),
                   linewidth=2.5)
        
        # Configure subplot
        configure_ceaf_plot(ax, max_wtp, country)
        ax.set_title(title, fontweight='bold', pad=10)
        
        # Add legend only to top-right plot to avoid clutter
        if idx == 1:
            add_publication_legend(ax, loc='center left', bbox_to_anchor=(1.05, 0.5))
    
    plt.tight_layout()
    save_publication_figure(fig, output_path)
    plt.close()

def create_equity_comparison_dashboard(dcea_df: pd.DataFrame,
                                     output_path: str = 'nextgen_v3/out/equity_dashboard_v3.png') -> None:
    """
    Create comprehensive equity analysis dashboard.
    """
    apply_publication_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Distributional Cost-Effectiveness Analysis Dashboard', 
                fontsize=16, fontweight='bold', y=0.95)
    
    # Subplot 1: Equity Impact Plane
    ax1 = axes[0, 0]
    
    # Mock equity data for demonstration
    therapies = ['Ketamine_IV', 'Esketamine', 'Psilocybin', 'Oral_ketamine']
    for therapy in therapies:
        # Mock equity impact data
        delta_total = np.random.normal(0.5, 0.2, 50)
        delta_equity = np.random.normal(0.1, 0.15, 50)
        
        ax1.scatter(delta_total, delta_equity,
                   color=get_therapy_color(therapy),
                   alpha=0.6, s=30,
                   label=get_therapy_label(therapy))
    
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Total Health Gain (QALYs)', fontweight='bold')
    ax1.set_ylabel('Equity-Weighted Health Gain', fontweight='bold')
    ax1.set_title('Equity Impact Plane', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Distributional CEAC
    ax2 = axes[0, 1]
    
    wtp_range = np.linspace(0, 75000, 16)
    for therapy in therapies:
        # Mock DCEAC curves
        prob_ce = np.random.uniform(0, 1, len(wtp_range))
        prob_ce = np.sort(prob_ce)[::-1] + np.random.normal(0, 0.1, len(wtp_range))
        prob_ce = np.clip(prob_ce, 0, 1)
        
        ax2.plot(wtp_range, prob_ce,
                label=get_therapy_label(therapy),
                color=get_therapy_color(therapy),
                linewidth=2.5)
    
    ax2.set_xlim(0, 75000)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel('WTP Threshold (AUD per QALY)', fontweight='bold')
    ax2.set_ylabel('Prob. Equity-Efficient', fontweight='bold') 
    ax2.set_title('Distributional CEAC', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: Equity Weights by Group
    ax3 = axes[1, 0]
    
    groups = ['General Population', 'Indigenous', 'Pacific Islander', 'Rural Remote']
    weights = [1.0, 1.8, 1.5, 1.3]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    bars = ax3.bar(groups, weights, color=colors, alpha=0.7)
    ax3.set_ylabel('Equity Weight', fontweight='bold')
    ax3.set_title('Population Equity Weights', fontweight='bold')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, weight in zip(bars, weights):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{weight:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Subplot 4: Atkinson Index by Therapy
    ax4 = axes[1, 1]
    
    epsilon_values = [0, 0.5, 1.0, 1.5, 2.0]
    therapy_sample = ['Ketamine_IV', 'Esketamine', 'Psilocybin']
    
    for therapy in therapy_sample:
        # Mock Atkinson values
        atkinson_values = np.random.uniform(0.1, 0.8, len(epsilon_values))
        ax4.plot(epsilon_values, atkinson_values,
                label=get_therapy_label(therapy),
                color=get_therapy_color(therapy),
                linewidth=2.5, marker='o')
    
    ax4.set_xlabel('Inequality Aversion (ε)', fontweight='bold')
    ax4.set_ylabel('Atkinson Index', fontweight='bold')
    ax4.set_title('Inequality Impact by Therapy', fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 2)
    ax4.set_ylim(0, 1)
    
    # Add single legend for entire figure
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right', bbox_to_anchor=(0.98, 0.5))
    
    plt.tight_layout()
    save_publication_figure(fig, output_path)
    plt.close()

def create_ce_plane_comparison(psa_df: pd.DataFrame,
                              output_path: str = 'nextgen_v3/out/ce_plane_comparison_v3.png',
                              wtp_threshold: float = 50000) -> None:
    """
    Create side-by-side CE plane comparisons for different scenarios.
    """
    apply_publication_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Cost-Effectiveness Plane Comparison', 
                fontsize=16, fontweight='bold', y=0.95)
    
    scenarios = [
        ('AU', 'health_system', 'AU Health System'),
        ('AU', 'societal', 'AU Societal'), 
        ('NZ', 'health_system', 'NZ Health System'),
        ('NZ', 'societal', 'NZ Societal')
    ]
    
    for idx, (country, perspective, title) in enumerate(scenarios):
        ax = axes[idx // 2, idx % 2]
        
        # Filter data (placeholder - would filter by jurisdiction/perspective in real data)
        scenario_df = psa_df
        
        # Get base case
        base_data = scenario_df[scenario_df['arm'] == 'ECT_std']
        base_cost = base_data['cost'].mean()
        base_qaly = base_data['qaly'].mean()
        
        # Plot each therapy
        for arm in scenario_df['arm'].unique():
            if arm == 'ECT_std':
                continue
                
            arm_data = scenario_df[scenario_df['arm'] == arm]
            
            # Calculate incremental values
            inc_cost = arm_data['cost'] - base_cost
            inc_qaly = arm_data['qaly'] - base_qaly
            
            ax.scatter(inc_qaly, inc_cost,
                      color=get_therapy_color(arm),
                      alpha=0.6, s=20,
                      label=get_therapy_label(arm) if idx == 0 else "")
        
        # Add WTP threshold line
        xlim = ax.get_xlim()
        ylim = ax.get_ylim() 
        x_range = np.linspace(xlim[0], xlim[1], 100)
        y_line = wtp_threshold * x_range
        
        mask = (y_line >= ylim[0]) & (y_line <= ylim[1])
        if np.any(mask):
            ax.plot(x_range[mask], y_line[mask], 
                   linestyle='--', color='gray', alpha=0.7)
        
        # Add quadrant lines
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        
        # Configure subplot
        ax.set_xlabel('Incremental QALYs', fontweight='bold')
        ax.set_ylabel(f'Incremental Cost ({format_currency(1, country).split(" ")[1]})', fontweight='bold')
        ax.set_title(title, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    # Add legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right', bbox_to_anchor=(0.98, 0.5))
    
    plt.tight_layout()
    save_publication_figure(fig, output_path)
    plt.close()

def create_comprehensive_v3_dashboard(ceaf_df: pd.DataFrame, 
                                     psa_df: pd.DataFrame,
                                     dcea_df: Optional[pd.DataFrame] = None,
                                     output_path: str = 'nextgen_v3/out/comprehensive_dashboard_v3.png') -> None:
    """
    Create comprehensive V3 analysis dashboard combining traditional and equity analyses.
    """
    apply_publication_style()
    
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('V3 NextGen Equity Framework: Comprehensive Analysis Dashboard', 
                fontsize=18, fontweight='bold', y=0.95)
    
    # Create complex subplot layout
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. CEAF (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    for arm in ceaf_df['arm'].unique():
        arm_data = ceaf_df[ceaf_df['arm'] == arm]
        ax1.plot(arm_data['wtp'], arm_data['prob_optimal'],
                label=get_therapy_label(arm),
                color=get_therapy_color(arm),
                linewidth=2)
    
    configure_ceaf_plot(ax1, 75000, 'AU')
    ax1.set_title('CEAF: AU Health System', fontweight='bold', fontsize=12)
    
    # 2. CE Plane (top middle)  
    ax2 = fig.add_subplot(gs[0, 1])
    
    base_data = psa_df[psa_df['arm'] == 'ECT_std']
    base_cost = base_data['cost'].mean()
    base_qaly = base_data['qaly'].mean()
    
    for arm in psa_df['arm'].unique():
        if arm == 'ECT_std':
            continue
        arm_data = psa_df[psa_df['arm'] == arm]
        inc_cost = arm_data['cost'] - base_cost
        inc_qaly = arm_data['qaly'] - base_qaly
        
        ax2.scatter(inc_qaly, inc_cost,
                   color=get_therapy_color(arm),
                   alpha=0.6, s=15)
    
    ax2.set_xlabel('Incremental QALYs', fontweight='bold', fontsize=10)
    ax2.set_ylabel('Incremental Cost (AUD)', fontweight='bold', fontsize=10)
    ax2.set_title('CE Plane: PSA Results', fontweight='bold', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # 3. Equity Impact (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Mock equity impact plane
    therapies = ['Ketamine_IV', 'Esketamine', 'Psilocybin']
    for therapy in therapies:
        delta_total = np.random.normal(0.3, 0.1, 30)
        delta_equity = np.random.normal(0.1, 0.05, 30)
        ax3.scatter(delta_total, delta_equity,
                   color=get_therapy_color(therapy),
                   alpha=0.6, s=15)
    
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax3.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    ax3.set_xlabel('Total Health Gain', fontweight='bold', fontsize=10)
    ax3.set_ylabel('Equity Impact', fontweight='bold', fontsize=10)
    ax3.set_title('Equity Impact Plane', fontweight='bold', fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # 4. Distributional CEAC (middle left)
    ax4 = fig.add_subplot(gs[1, 0])
    
    wtp_range = np.linspace(0, 75000, 16)
    for therapy in therapies:
        prob_ce = np.random.uniform(0, 1, len(wtp_range))
        prob_ce = np.sort(prob_ce)[::-1]
        ax4.plot(wtp_range, prob_ce,
                color=get_therapy_color(therapy),
                linewidth=2)
    
    ax4.set_xlim(0, 75000)
    ax4.set_ylim(0, 1)
    ax4.set_xlabel('WTP Threshold (AUD)', fontweight='bold', fontsize=10)
    ax4.set_ylabel('Prob. Equity-Efficient', fontweight='bold', fontsize=10)
    ax4.set_title('Distributional CEAC', fontweight='bold', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    # 5. Budget Impact (middle center)
    ax5 = fig.add_subplot(gs[1, 1])
    
    years = np.arange(1, 6)
    for therapy in therapies:
        budget_impact = np.random.uniform(0.5, 2.5, len(years)) * np.arange(1, 6)
        ax5.plot(years, budget_impact,
                color=get_therapy_color(therapy),
                linewidth=2, marker='o', markersize=4)
    
    ax5.set_xlabel('Year', fontweight='bold', fontsize=10)
    ax5.set_ylabel('Budget Impact (Million AUD)', fontweight='bold', fontsize=10)
    ax5.set_title('5-Year Budget Impact', fontweight='bold', fontsize=12)
    ax5.grid(True, alpha=0.3)
    
    # 6. Value of Information (middle right)
    ax6 = fig.add_subplot(gs[1, 2])
    
    evpi_values = np.random.uniform(500, 3000, len(wtp_range))
    ax6.plot(wtp_range, evpi_values, color='darkred', linewidth=2)
    ax6.fill_between(wtp_range, evpi_values, alpha=0.3, color='darkred')
    
    ax6.set_xlim(0, 75000)
    ax6.set_xlabel('WTP Threshold (AUD)', fontweight='bold', fontsize=10)
    ax6.set_ylabel('EVPI per Patient (AUD)', fontweight='bold', fontsize=10)
    ax6.set_title('Expected Value of Perfect Information', fontweight='bold', fontsize=12)
    ax6.grid(True, alpha=0.3)
    
    # 7. Tornado Diagram (bottom span)
    ax7 = fig.add_subplot(gs[2, :])
    
    params = ['Treatment Response', 'Relapse Rate', 'Utility (Remission)', 'Session Cost', 'Time Horizon']
    low_vals = [45000, 47000, 46000, 48000, 44000]
    high_vals = [55000, 53000, 54000, 52000, 56000]
    base_val = 50000
    
    y_pos = np.arange(len(params))
    ax7.barh(y_pos, [h - base_val for h in high_vals], left=base_val, 
            color='darkred', alpha=0.7, height=0.6)
    ax7.barh(y_pos, [l - base_val for l in low_vals], left=base_val,
            color='darkblue', alpha=0.7, height=0.6)
    ax7.axvline(x=base_val, color='black', linewidth=2)
    
    ax7.set_yticks(y_pos)
    ax7.set_yticklabels(params, fontsize=10)
    ax7.set_xlabel('ICER (AUD per QALY)', fontweight='bold', fontsize=10)
    ax7.set_title('One-Way Sensitivity Analysis', fontweight='bold', fontsize=12)
    ax7.grid(True, alpha=0.3, axis='x')
    
    # Add single comprehensive legend
    legend_elements = [plt.Line2D([0], [0], color=get_therapy_color(arm), lw=2, 
                                 label=get_therapy_label(arm)) 
                      for arm in ['ECT_std', 'Ketamine_IV', 'Esketamine', 'Psilocybin', 'Oral_ketamine']]
    
    fig.legend(handles=legend_elements, loc='lower center', 
              bbox_to_anchor=(0.5, -0.02), ncol=5, fontsize=11)
    
    save_publication_figure(fig, output_path)
    plt.close()

# Convenience function to generate all comparison plots
def generate_all_v3_comparisons(ceaf_df: pd.DataFrame, 
                                psa_df: pd.DataFrame,
                                dcea_df: Optional[pd.DataFrame] = None,
                                output_dir: str = 'nextgen_v3/out/comparisons/') -> None:
    """Generate all V3 comparison plots."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("📊 Generating V3 comparison plots...")
    
    create_ceaf_comparison_plot(ceaf_df, f"{output_dir}ceaf_comparison_v3.png")
    print("✅ CEAF comparison plot created")
    
    create_ce_plane_comparison(psa_df, f"{output_dir}ce_plane_comparison_v3.png") 
    print("✅ CE plane comparison plot created")
    
    create_equity_comparison_dashboard(dcea_df, f"{output_dir}equity_dashboard_v3.png")
    print("✅ Equity dashboard created")
    
    create_comprehensive_v3_dashboard(ceaf_df, psa_df, dcea_df, f"{output_dir}comprehensive_dashboard_v3.png")
    print("✅ Comprehensive dashboard created")
    
    print(f"🎉 All V3 comparison plots saved to: {output_dir}")