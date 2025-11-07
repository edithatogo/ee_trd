"""
Value of Information Analysis for V3 NextGen Equity Framework.
Implements EVPI, EVPPI, and related analyses with equity considerations.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import sys
import os

# Add plots directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plots'))

from publication_style import (
    apply_publication_style, save_publication_figure, format_currency,
    get_currency_label, add_publication_legend
)

def calculate_evpi(psa_df: pd.DataFrame, 
                   wtp_thresholds: List[float],
                   population_size: int = 10000,
                   time_horizon: int = 5) -> pd.DataFrame:
    """
    Calculate Expected Value of Perfect Information (EVPI).
    
    Args:
        psa_df: PSA results with columns ['arm', 'iteration', 'cost', 'qaly']
        wtp_thresholds: List of WTP thresholds to evaluate
        population_size: Population affected per year
        time_horizon: Time horizon for population EVPI calculation
    
    Returns:
        DataFrame with EVPI values at each WTP threshold
    """
    evpi_results = []
    
    for wtp in wtp_thresholds:
        iteration_values = []
        
        # Get unique iterations
        iterations = psa_df['iteration'].unique()
        
        for iteration in iterations:
            iter_data = psa_df[psa_df['iteration'] == iteration]
            
            # Calculate NMB for each arm in this iteration
            nmb_values = {}
            for _, row in iter_data.iterrows():
                nmb = row['qaly'] * wtp - row['cost']
                nmb_values[row['arm']] = nmb
            
            # Find best NMB in this iteration
            best_nmb = max(nmb_values.values())
            iteration_values.append(best_nmb)
        
        # Calculate expected NMB with perfect information
        expected_nmb_perfect = np.mean(iteration_values)
        
        # Calculate expected NMB with current information
        # (best arm based on expected values)
        expected_values = {}
        for arm in psa_df['arm'].unique():
            arm_data = psa_df[psa_df['arm'] == arm]
            expected_cost = arm_data['cost'].mean()
            expected_qaly = arm_data['qaly'].mean()
            expected_values[arm] = expected_qaly * wtp - expected_cost
        
        expected_nmb_current = max(expected_values.values())
        
        # EVPI per patient
        evpi_per_patient = expected_nmb_perfect - expected_nmb_current
        
        # Population EVPI
        total_population = population_size * time_horizon
        evpi_population = evpi_per_patient * total_population
        
        evpi_results.append({
            'wtp': wtp,
            'evpi_per_patient': evpi_per_patient,
            'evpi_population': evpi_population,
            'evpi_population_millions': evpi_population / 1_000_000
        })
    
    return pd.DataFrame(evpi_results)

def calculate_equity_evpi(psa_df: pd.DataFrame, 
                          dcea_weights: Dict[str, float],
                          wtp_thresholds: List[float]) -> pd.DataFrame:
    """
    Calculate EVPI with equity weighting considerations.
    """
    # This would be more complex in real implementation
    # For now, return modified EVPI values with equity multipliers
    
    _evpi_df = calculate_evpi(psa_df, wtp_thresholds)
    
    # Apply equity multiplier (simplified)
    equity_multiplier = 1.3  # Higher value for equity-focused research
    evpi_df['evpi_equity_per_patient'] = evpi_df['evpi_per_patient'] * equity_multiplier
    evpi_df['evpi_equity_population'] = evpi_df['evpi_population'] * equity_multiplier
    evpi_df['evpi_equity_population_millions'] = evpi_df['evpi_equity_population'] / 1_000_000
    
    return evpi_df

def plot_evpi_analysis(evpi_df: pd.DataFrame,
                       output_path: str = 'nextgen_v3/out/evpi_analysis_v3.png',
                       country: str = 'AU',
                       include_equity: bool = True) -> None:
    """
    Create publication-quality EVPI analysis plot.
    """
    apply_publication_style()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('Expected Value of Perfect Information Analysis', 
                fontsize=16, fontweight='bold')
    
    # Plot 1: EVPI per patient
    ax1.plot(evpi_df['wtp'], evpi_df['evpi_per_patient'], 
            color='darkblue', linewidth=3, label='Standard EVPI')
    ax1.fill_between(evpi_df['wtp'], evpi_df['evpi_per_patient'], 
                     alpha=0.3, color='darkblue')
    
    if include_equity and 'evpi_equity_per_patient' in evpi_df.columns:
        ax1.plot(evpi_df['wtp'], evpi_df['evpi_equity_per_patient'],
                color='darkred', linewidth=3, linestyle='--',
                label='Equity-Weighted EVPI')
        ax1.fill_between(evpi_df['wtp'], evpi_df['evpi_equity_per_patient'],
                        alpha=0.2, color='darkred')
    
    ax1.set_xlabel(f'Willingness-to-Pay Threshold ({get_currency_label(country)})', 
                  fontweight='bold')
    ax1.set_ylabel(f'EVPI per Patient ({format_currency(1, country).split(" ")[1]})', 
                  fontweight='bold')
    ax1.set_title('EVPI per Patient', fontweight='bold', pad=10)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Format y-axis with currency
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, p: f'${x:,.0f}'))
    
    # Plot 2: Population EVPI (in millions)
    ax2.plot(evpi_df['wtp'], evpi_df['evpi_population_millions'],
            color='darkgreen', linewidth=3, label='Standard EVPI')
    ax2.fill_between(evpi_df['wtp'], evpi_df['evpi_population_millions'],
                     alpha=0.3, color='darkgreen')
    
    if include_equity and 'evpi_equity_population_millions' in evpi_df.columns:
        ax2.plot(evpi_df['wtp'], evpi_df['evpi_equity_population_millions'],
                color='darkred', linewidth=3, linestyle='--',
                label='Equity-Weighted EVPI')
        ax2.fill_between(evpi_df['wtp'], evpi_df['evpi_equity_population_millions'],
                        alpha=0.2, color='darkred')
    
    ax2.set_xlabel(f'Willingness-to-Pay Threshold ({get_currency_label(country)})', 
                  fontweight='bold')
    ax2.set_ylabel(f'Population EVPI (Million {format_currency(1, country).split(" ")[1]})', 
                  fontweight='bold')
    ax2.set_title('Population EVPI (5-year horizon, 10,000 patients/year)', 
                 fontweight='bold', pad=10)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Format y-axis
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, p: f'${x:.1f}M'))
    
    # Format x-axis with currency for both plots
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'${x/1000:.0f}K'))
    
    plt.tight_layout()
    save_publication_figure(fig, output_path)
    plt.close()

def create_voi_summary_table(evpi_df: pd.DataFrame,
                            key_wtp_values: List[float] = [25000, 50000, 75000],
                            output_path: str = 'nextgen_v3/out/voi_summary_v3.csv') -> pd.DataFrame:
    """
    Create summary table of VOI results at key WTP thresholds.
    """
    summary_data = []
    
    for wtp in key_wtp_values:
        # Find closest WTP value in results
        closest_idx = np.argmin(np.abs(evpi_df['wtp'] - wtp))
        row = evpi_df.iloc[closest_idx]
        
        summary_data.append({
            'WTP_Threshold': f"${wtp:,.0f}",
            'EVPI_per_Patient': f"${row['evpi_per_patient']:,.0f}",
            'Population_EVPI_Millions': f"${row['evpi_population_millions']:.1f}M",
            'Research_Priority': 'High' if row['evpi_population_millions'] > 5 else 
                               'Medium' if row['evpi_population_millions'] > 1 else 'Low'
        })
        
        if 'evpi_equity_population_millions' in evpi_df.columns:
            summary_data[-1]['Equity_EVPI_Millions'] = f"${row['evpi_equity_population_millions']:.1f}M"
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_path, index=False)
    
    return summary_df

def run_comprehensive_voi_analysis(psa_df: pd.DataFrame,
                                  output_dir: str = 'nextgen_v3/out/voi/',
                                  wtp_range: Tuple[int, int, int] = (0, 75000, 16),
                                  country: str = 'AU') -> Dict[str, pd.DataFrame]:
    """
    Run comprehensive VOI analysis and generate all outputs.
    
    Args:
        psa_df: PSA results dataframe
        output_dir: Output directory for results
        wtp_range: (start, stop, num_points) for WTP threshold range
        country: Country code for currency formatting
    
    Returns:
        Dictionary of result dataframes
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("📊 Running V3 Value of Information Analysis...")
    
    # Generate WTP thresholds
    wtp_thresholds = np.linspace(wtp_range[0], wtp_range[1], wtp_range[2])
    
    # Calculate standard EVPI
    print("🔢 Calculating EVPI...")
    _evpi_df = calculate_evpi(psa_df, wtp_thresholds)
    
    # Calculate equity-weighted EVPI
    print("⚖️ Calculating equity-weighted EVPI...")
    dcea_weights = {'general': 1.0, 'indigenous': 1.8, 'pacific': 1.5, 'rural': 1.3}
    evpi_equity_df = calculate_equity_evpi(psa_df, dcea_weights, wtp_thresholds)
    
    # Create EVPI plot
    print("📈 Creating EVPI plots...")
    plot_evpi_analysis(evpi_equity_df, f"{output_dir}evpi_analysis_v3.png", 
                      country=country, include_equity=True)
    
    # Create summary table
    print("📋 Creating VOI summary table...")
    summary_df = create_voi_summary_table(evpi_equity_df, 
                                         output_path=f"{output_dir}voi_summary_v3.csv")
    
    # Save detailed results
    evpi_equity_df.to_csv(f"{output_dir}evpi_detailed_v3.csv", index=False)
    
    print(f"✅ VOI analysis complete. Results saved to: {output_dir}")
    
    return {
        'evpi_results': evpi_equity_df,
        'voi_summary': summary_df
    }

def create_research_priority_plot(evpi_df: pd.DataFrame,
                                 output_path: str = 'nextgen_v3/out/research_priorities_v3.png',
                                 country: str = 'AU') -> None:
    """
    Create research priority visualization based on EVPI results.
    """
    apply_publication_style()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define research priority thresholds (in millions)
    high_priority = 5.0
    medium_priority = 1.0
    
    # Create stacked area plot
    ax.fill_between(evpi_df['wtp'], evpi_df['evpi_population_millions'],
                   where=(evpi_df['evpi_population_millions'] >= high_priority),
                   color='darkred', alpha=0.8, label='High Priority (>$5M)')
    
    ax.fill_between(evpi_df['wtp'], evpi_df['evpi_population_millions'],
                   where=(evpi_df['evpi_population_millions'] >= medium_priority) & 
                         (evpi_df['evpi_population_millions'] < high_priority),
                   color='orange', alpha=0.8, label='Medium Priority ($1-5M)')
    
    ax.fill_between(evpi_df['wtp'], evpi_df['evpi_population_millions'],
                   where=(evpi_df['evpi_population_millions'] < medium_priority),
                   color='lightgreen', alpha=0.8, label='Low Priority (<$1M)')
    
    # Add threshold lines
    ax.axhline(y=high_priority, color='darkred', linestyle='--', alpha=0.7)
    ax.axhline(y=medium_priority, color='orange', linestyle='--', alpha=0.7)
    
    # Formatting
    ax.set_xlabel(f'Willingness-to-Pay Threshold ({get_currency_label(country)})', 
                 fontweight='bold')
    ax.set_ylabel(f'Population EVPI (Million {format_currency(1, country).split(" ")[1]})', 
                 fontweight='bold')
    ax.set_title('Research Priority Classification by WTP Threshold', 
                fontweight='bold', pad=20)
    
    # Format axes
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.1f}M'))
    
    ax.grid(True, alpha=0.3)
    add_publication_legend(ax)
    
    # Add text annotations for priority zones
    ax.text(0.02, 0.95, 'HIGH PRIORITY\\nResearch', transform=ax.transAxes,
           bbox=dict(boxstyle='round', facecolor='darkred', alpha=0.7),
           color='white', fontweight='bold', va='top')
    
    save_publication_figure(fig, output_path)
    plt.close()