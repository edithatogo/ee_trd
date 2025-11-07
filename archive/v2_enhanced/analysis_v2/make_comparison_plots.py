"""Create publication-quality comparison plots for analysis_v2."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import load_analysis_inputs

def net_monetary_benefit(effects, costs, lambda_val):
    """Helper function to compute NMB: lambda * effects - costs"""
    return lambda_val * np.array(effects) - np.array(costs)
from analysis_core.plotting import save_multiformat
from utils import set_seed

# Publication color palette for interventions
INTERVENTION_COLORS = {
    'Usual care': '#2E2E2E',
    'ECT': '#1f77b4', 
    'KA-ECT': '#ff7f0e',
    'IV-KA': '#2ca02c', 
    'IN-EKA': '#d62728',
    'PO psilocybin': '#9467bd',
    'PO-KA': '#8c564b',
    # Legacy names for backwards compatibility
    'Therapy A': '#2ca02c', 
    'Therapy B': '#d62728',
    'Therapy C': '#9467bd',
    'Oral ketamine': '#8c564b'
}

PERSPECTIVE_COLORS = {
    'health_system': '#1f77b4',
    'societal': '#ff7f0e'
}

def create_ceaf_comparison_plot(
    psa_df: pd.DataFrame,
    strategies: List[str],
    lambda_range: np.ndarray,
    perspectives: List[str] = ['health_system', 'societal'],
    jurisdiction: str = 'AU',
    outdir: Path = None
) -> None:
    """Create CEAF comparison plot with subplots for each perspective."""
    
    fig, axes = plt.subplots(1, len(perspectives), figsize=(6*len(perspectives), 5), squeeze=False)
    fig.suptitle(f'Cost-Effectiveness Acceptability Frontier Comparison - {jurisdiction}', 
                 fontsize=14, fontweight='bold', y=0.98)
    
    for idx, perspective in enumerate(perspectives):
        ax = axes[0, idx]
        
        # Filter data for this perspective
        persp_df = psa_df[psa_df['perspective'] == perspective].copy()
        
        if persp_df.empty:
            ax.text(0.5, 0.5, f'No data for {perspective}', 
                   transform=ax.transAxes, ha='center', va='center')
            continue
        
        # Calculate CEAF for each lambda value
        ceaf_data = []
        for lam in lambda_range:
            # Calculate NMB for each strategy at this lambda
            strategy_nmbs = {}
            for strategy in strategies:
                strat_data = persp_df[persp_df['strategy'] == strategy]
                if not strat_data.empty:
                    nmb = net_monetary_benefit(strat_data['effect'].values, 
                                             strat_data['cost'].values, lam)
                    strategy_nmbs[strategy] = np.mean(nmb)
            
            # Find optimal strategy
            if strategy_nmbs:
                optimal = max(strategy_nmbs, key=strategy_nmbs.get)
                ceaf_data.append({'lambda': lam, 'optimal_strategy': optimal})
        
        # Plot CEAF frontier
        ceaf_df = pd.DataFrame(ceaf_data)
        if not ceaf_df.empty:
            # Calculate frontier segments
            for strategy in strategies:
                strategy_points = ceaf_df[ceaf_df['optimal_strategy'] == strategy]
                if not strategy_points.empty:
                    color = INTERVENTION_COLORS.get(strategy, '#333333')
                    ax.scatter(strategy_points['lambda'], [1]*len(strategy_points), 
                             color=color, s=20, alpha=0.8, label=strategy)
        
        # Formatting
        ax.set_xlabel('Willingness-to-Pay Threshold ($/QALY)', fontsize=11)
        ax.set_ylabel('Optimal Strategy', fontsize=11)
        ax.set_title(f'{perspective.replace("_", " ").title()} Perspective', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    plt.tight_layout()
    
    if outdir:
        save_multiformat(fig, outdir, f'v2_ceaf_comparison_allperspectives_{jurisdiction.lower()}', 
                         formats=['png', 'pdf', 'svg'], dpi=300)
    
    return fig

def create_ce_plane_comparison_plot(
    psa_df: pd.DataFrame,
    strategies: List[str],
    perspectives: List[str] = ['health_system', 'societal'],
    jurisdiction: str = 'AU',
    wtp_threshold: float = 50000,
    outdir: Path = None
) -> None:
    """Create cost-effectiveness plane comparison with all interventions."""
    
    fig, axes = plt.subplots(1, len(perspectives), figsize=(8*len(perspectives), 6))
    if len(perspectives) == 1:
        axes = [axes]
    
    fig.suptitle(f'Cost-Effectiveness Plane Comparison - {jurisdiction}', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    for idx, perspective in enumerate(perspectives):
        ax = axes[idx]
        
        # Filter data for this perspective
        persp_df = psa_df[psa_df['perspective'] == perspective].copy()
        
        if persp_df.empty:
            continue
        
        # Plot each intervention
        for strategy in strategies:
            strat_data = persp_df[persp_df['strategy'] == strategy]
            if strat_data.empty:
                continue
            
            color = INTERVENTION_COLORS.get(strategy, '#333333')
            
            # Plot PSA cloud
            ax.scatter(strat_data['effect'], strat_data['cost'], 
                      alpha=0.6, s=8, color=color, label=strategy, edgecolors='none')
            
            # Plot mean point
            mean_effect = strat_data['effect'].mean()
            mean_cost = strat_data['cost'].mean()
            ax.scatter(mean_effect, mean_cost, color=color, s=100, 
                      marker='D', edgecolors='white', linewidth=2, zorder=10)
        
        # Add WTP threshold line
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Extend line across the plot
        x_line = np.linspace(xlim[0], xlim[1], 100)
        y_line = wtp_threshold * (x_line - xlim[0])  # Line from bottom-left
        
        # Only show line where it's within plot bounds
        valid_mask = (y_line >= ylim[0]) & (y_line <= ylim[1])
        if np.any(valid_mask):
            ax.plot(x_line[valid_mask], y_line[valid_mask], 
                   'k--', alpha=0.7, linewidth=1.5, 
                   label=f'WTP = ${wtp_threshold:,.0f}/QALY')
        
        # Formatting
        ax.set_xlabel('Effectiveness (QALYs)', fontsize=12)
        ax.set_ylabel('Cost ($)', fontsize=12)
        ax.set_title(f'{perspective.replace("_", " ").title()} Perspective', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        if idx == len(perspectives) - 1:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    plt.tight_layout()
    
    if outdir:
        save_multiformat(fig, outdir, f'v2_ceplane_comparison_allperspectives_{jurisdiction.lower()}',
                         formats=['png', 'pdf', 'svg'], dpi=300)
    
    return fig

def create_vbp_comparison_plot(
    psa_df: pd.DataFrame,
    strategies: List[str],
    perspectives: List[str] = ['health_system', 'societal'],
    jurisdiction: str = 'AU',
    price_range: np.ndarray = None,
    lambda_threshold: float = 50000,
    outdir: Path = None
) -> None:
    """Create value-based pricing comparison across interventions."""
    
    if price_range is None:
        price_range = np.linspace(0, 50000, 101)  # More focused price range
    
    fig, axes = plt.subplots(len(perspectives), 1, figsize=(10, 5*len(perspectives)))
    if len(perspectives) == 1:
        axes = [axes]
    
    fig.suptitle(f'Value-Based Pricing Comparison - {jurisdiction}', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    for idx, perspective in enumerate(perspectives):
        ax = axes[idx]
        
        # Filter data for this perspective
        persp_df = psa_df[psa_df['perspective'] == perspective].copy()
        
        if persp_df.empty:
            continue
        
        # Calculate VBP curves for each intervention
        for strategy in strategies:
            strat_data = persp_df[persp_df['strategy'] == strategy]
            if strat_data.empty or strategy == 'Usual care':
                continue
            
            prob_ce = []
            
            for price in price_range:
                # Modify cost for this price point
                modified_costs = strat_data['cost'].values - strat_data['cost'].mean() + price
                
                # Calculate NMB for all strategies at this price
                strategy_nmbs = {}
                
                # Modified strategy
                nmb_modified = net_monetary_benefit(strat_data['effect'].values, 
                                                  modified_costs, lambda_threshold)
                strategy_nmbs[strategy] = nmb_modified
                
                # Other strategies (unchanged)
                for other_strat in strategies:
                    if other_strat == strategy:
                        continue
                    other_data = persp_df[persp_df['strategy'] == other_strat]
                    if not other_data.empty:
                        nmb_other = net_monetary_benefit(other_data['effect'].values,
                                                       other_data['cost'].values, 
                                                       lambda_threshold)
                        strategy_nmbs[other_strat] = nmb_other
                
                # Calculate probability this strategy is optimal
                if len(strategy_nmbs) > 1:
                    n_sims = len(strat_data)
                    wins = 0
                    for i in range(n_sims):
                        strategy_values = {k: v[i] if len(v) > i else v[0] 
                                        for k, v in strategy_nmbs.items() 
                                        if len(v) > 0}
                        if strategy_values and strategy == max(strategy_values, 
                                                             key=strategy_values.get):
                            wins += 1
                    prob_ce.append(wins / n_sims)
                else:
                    prob_ce.append(0)
            
            # Plot VBP curve
            color = INTERVENTION_COLORS.get(strategy, '#333333')
            ax.plot(price_range, prob_ce, color=color, linewidth=2.5, 
                   label=strategy, alpha=0.8)
        
        # Formatting
        ax.set_xlabel('Price ($)', fontsize=12)
        ax.set_ylabel('Probability Cost-Effective', fontsize=12)
        ax.set_title(f'{perspective.replace("_", " ").title()} Perspective', 
                    fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        if idx == len(perspectives) - 1:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    plt.tight_layout()
    
    if outdir:
        save_multiformat(fig, outdir, f'v2_vbp_comparison_allperspectives_{jurisdiction.lower()}', 
                         formats=['png', 'pdf', 'svg'], dpi=300)
    
    return fig

def create_comprehensive_dashboard(
    psa_df: pd.DataFrame,
    strategies: List[str],
    perspectives: List[str] = ['health_system', 'societal'],
    jurisdiction: str = 'AU',
    outdir: Path = None
) -> None:
    """Create a comprehensive 4-panel dashboard for publication."""
    
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    fig.suptitle(f'Comprehensive Health Economic Analysis Dashboard - {jurisdiction}', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # Panel 1: CE Plane Comparison
    ax1 = fig.add_subplot(gs[0, 0])
    plot_ce_plane_panel(ax1, psa_df, strategies, 'health_system', jurisdiction)
    ax1.set_title('A) Cost-Effectiveness Plane (Health System)', fontsize=12, fontweight='bold')
    
    # Panel 2: CE Plane Societal
    ax2 = fig.add_subplot(gs[0, 1])
    plot_ce_plane_panel(ax2, psa_df, strategies, 'societal', jurisdiction)
    ax2.set_title('B) Cost-Effectiveness Plane (Societal)', fontsize=12, fontweight='bold')
    
    # Panel 3: CEAF Comparison
    ax3 = fig.add_subplot(gs[1, 0])
    plot_ceaf_panel(ax3, psa_df, strategies, perspectives, jurisdiction)
    ax3.set_title('C) Cost-Effectiveness Acceptability Frontier', fontsize=12, fontweight='bold')
    
    # Panel 4: Price-Probability
    ax4 = fig.add_subplot(gs[1, 1])
    plot_price_prob_panel(ax4, psa_df, strategies, 'health_system', jurisdiction)
    ax4.set_title('D) Price-Probability Analysis', fontsize=12, fontweight='bold')
    
    if outdir:
        save_multiformat(fig, outdir, f'v2_dashboard_comprehensive_allperspectives_{jurisdiction.lower()}', 
                         formats=['png', 'pdf', 'svg'], dpi=300)
    
    return fig

def plot_ce_plane_panel(ax, psa_df, strategies, perspective, jurisdiction):
    """Helper function to plot CE plane panel."""
    persp_df = psa_df[psa_df['perspective'] == perspective].copy()
    
    for strategy in strategies:
        strat_data = persp_df[persp_df['strategy'] == strategy]
        if strat_data.empty:
            continue
        
        color = INTERVENTION_COLORS.get(strategy, '#333333')
        ax.scatter(strat_data['effect'], strat_data['cost'], 
                  alpha=0.5, s=6, color=color, label=strategy)
        
        # Mean point
        ax.scatter(strat_data['effect'].mean(), strat_data['cost'].mean(), 
                  color=color, s=80, marker='D', edgecolors='white', 
                  linewidth=1.5, zorder=10)
    
    ax.set_xlabel('Effectiveness (QALYs)')
    ax.set_ylabel('Cost ($)')
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

def plot_ceaf_panel(ax, psa_df, strategies, perspectives, jurisdiction):
    """Helper function to plot CEAF panel."""
    lambda_range = np.linspace(0, 100000, 101)
    
    for perspective in perspectives:
        persp_df = psa_df[psa_df['perspective'] == perspective].copy()
        if persp_df.empty:
            continue
        
        frontier_probs = []
        for lam in lambda_range:
            strategy_nmbs = {}
            for strategy in strategies:
                strat_data = persp_df[persp_df['strategy'] == strategy]
                if not strat_data.empty:
                    nmb = net_monetary_benefit(strat_data['effect'].values, 
                                             strat_data['cost'].values, lam)
                    strategy_nmbs[strategy] = np.mean(nmb)
            
            if strategy_nmbs:
                optimal = max(strategy_nmbs, key=strategy_nmbs.get)
                frontier_probs.append(optimal)
            else:
                frontier_probs.append(None)
        
        # Plot frontier line
        color = PERSPECTIVE_COLORS[perspective]
        ax.plot(lambda_range, [1]*len(lambda_range), color=color, linewidth=2,
               label=perspective.replace('_', ' ').title())
    
    ax.set_xlabel('Willingness-to-Pay ($/QALY)')
    ax.set_ylabel('Frontier Position')
    ax.grid(True, alpha=0.3)

def plot_price_prob_panel(ax, psa_df, strategies, perspective, jurisdiction):
    """Helper function to plot price-probability panel."""
    persp_df = psa_df[psa_df['perspective'] == perspective].copy()
    price_range = np.linspace(0, 150000, 76)  # Every 2000
    wtp_threshold = 50000
    
    for strategy in strategies:
        if strategy == 'Usual care':
            continue
        
        strat_data = persp_df[persp_df['strategy'] == strategy]
        if strat_data.empty:
            continue
        
        prob_ce = []
        for price in price_range:
            # Calculate probability this strategy is cost-effective at this price
            # Adjust the strategy's cost to the given price
            base_cost = strat_data['cost'].mean()
            adjusted_costs = strat_data['cost'].values - base_cost + price
            
            # Calculate NMB for this strategy
            nmb_strategy = net_monetary_benefit(strat_data['effect'].values, 
                                             adjusted_costs, wtp_threshold)
            
            # Calculate NMB for all other strategies (unchanged costs)
            nmb_comparisons = []
            for other_strat in strategies:
                other_data = persp_df[persp_df['strategy'] == other_strat]
                if not other_data.empty and len(other_data) == len(strat_data):
                    nmb_other = net_monetary_benefit(other_data['effect'].values,
                                                   other_data['cost'].values,
                                                   wtp_threshold)
                    nmb_comparisons.append(nmb_other)
            
            if nmb_comparisons:
                # Count how often this strategy has highest NMB
                wins = 0
                for i in range(len(nmb_strategy)):
                    strategy_nmb = nmb_strategy[i]
                    other_nmbs = [comp[i] for comp in nmb_comparisons]
                    if strategy_nmb >= max(other_nmbs):
                        wins += 1
                prob_ce.append(wins / len(nmb_strategy))
            else:
                prob_ce.append(0.5)
        
        color = INTERVENTION_COLORS.get(strategy, '#333333')
        ax.plot(price_range, prob_ce, color=color, linewidth=2, label=strategy)
    
    ax.set_xlabel('Price ($)')
    ax.set_ylabel('Probability Cost-Effective')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Main execution function
def main():
    parser = argparse.ArgumentParser(description="Create comparison plots for analysis_v2")
    parser.add_argument("--psa", type=Path, required=True, help="PSA CSV file")
    parser.add_argument("--strategies-yaml", type=Path, required=True, help="Strategies YAML")
    parser.add_argument("--outdir", type=Path, required=True, help="Output directory")
    parser.add_argument("--jurisdiction", choices=["AU", "NZ"], default="AU")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    set_seed(args.seed)
    
    # Load data
    # Load data for both perspectives
    lambda_grid = np.arange(0, 100001, 1000)
    
    # Load health system perspective data
    hs_data = load_analysis_inputs(
        psa_path=args.psa,
        config_path=args.strategies_yaml,
        perspective='health_system',
        lambda_grid=lambda_grid
    )
    
    # Load societal perspective data  
    soc_data = load_analysis_inputs(
        psa_path=args.psa,
        config_path=args.strategies_yaml,
        perspective='societal',
        lambda_grid=lambda_grid
    )
    
    # Combine data from both perspectives
    psa_df = pd.concat([hs_data.table, soc_data.table])
    
    # Get strategies from config
    strategies = hs_data.config.strategies
    strategy_names = strategies
    
    # Create output directory
    args.outdir.mkdir(parents=True, exist_ok=True)
    
    # Generate all comparison plots
    print("Generating cost-effectiveness plane comparison...")
    create_ce_plane_comparison_plot(psa_df, strategy_names, outdir=args.outdir, 
                                   jurisdiction=args.jurisdiction)
    
    print("Generating CEAF comparison...")
    create_ceaf_comparison_plot(psa_df, strategy_names, np.linspace(0, 100000, 101),
                               outdir=args.outdir, jurisdiction=args.jurisdiction)
    
    print("Generating VBP comparison...")
    create_vbp_comparison_plot(psa_df, strategy_names, outdir=args.outdir,
                              jurisdiction=args.jurisdiction)
    
    print("Generating comprehensive dashboard...")
    create_comprehensive_dashboard(psa_df, strategy_names, outdir=args.outdir,
                                  jurisdiction=args.jurisdiction)
    
    print(f"All comparison plots saved to {args.outdir}")

if __name__ == "__main__":
    main()