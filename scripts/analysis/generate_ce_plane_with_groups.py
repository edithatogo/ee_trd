#!/usr/bin/env python
"""Generate CE Plane with Grouping Ellipses Around Strategy Clusters"""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.plotting import JournalStandards  # noqa: E402
from analysis.plotting.publication import (  # noqa: E402
    figure_context, save_multiformat, add_reference_line,
    format_axis_currency, add_wtp_threshold
)
from scripts.run_v4_analysis import load_psa_data


def plot_ce_plane_with_groups(
    costs, effects, reference_strategy, output_path,
    wtp=50000, currency='A$', title=None, standards=None,
    ylim=None, strategy_groups=None
):
    """
    Create cost-effectiveness plane with grouping ellipses.
    
    Args:
        costs: DataFrame with strategies as columns, draws as rows
        effects: DataFrame with strategies as columns, draws as rows
        reference_strategy: Reference strategy name
        output_path: Output file path
        wtp: Willingness-to-pay threshold
        currency: Currency symbol
        title: Optional custom title
        standards: Journal standards
        ylim: Optional tuple of (ymin, ymax) for y-axis limits
        strategy_groups: Dict mapping group names to lists of strategies
    """
    if title is None:
        title = "Cost-Effectiveness Plane"
    
    if standards is None:
        standards = JournalStandards()
    
    # Calculate incremental costs and effects
    inc_costs = costs.subtract(costs[reference_strategy], axis=0)
    inc_effects = effects.subtract(effects[reference_strategy], axis=0)
    
    # Define default groups if none provided
    if strategy_groups is None:
        strategy_groups = {
            'Standard Care': ['UC', 'UC+Li', 'UC+AA'],
            'Novel Therapies': ['IV-KA', 'IN-EKA', 'PO-KA', 'PO-PSI'],
            'Established Alternatives': ['ECT', 'KA-ECT', 'rTMS']
        }
    
    # Group colors (semi-transparent)
    group_colors = {
        'Standard Care': '#FFA07A',      # Light salmon
        'Novel Therapies': '#98FB98',    # Pale green
        'Established Alternatives': '#87CEEB'  # Sky blue
    }
    
    with figure_context(
        title=title,
        xlabel="Incremental QALYs",
        ylabel=f"Incremental Cost ({currency})",
        standards=standards
    ) as (fig, ax):
        
        # First, draw grouping ellipses (behind the points)
        for group_name, strategies in strategy_groups.items():
            # Get data for strategies in this group
            group_effects = []
            group_costs = []
            
            for strategy in strategies:
                if strategy in inc_effects.columns and strategy != reference_strategy:
                    group_effects.extend(inc_effects[strategy].values)
                    group_costs.extend(inc_costs[strategy].values)
            
            if len(group_effects) > 0:
                # Calculate ellipse parameters (mean and std)
                mean_x = np.mean(group_effects)
                mean_y = np.mean(group_costs)
                std_x = np.std(group_effects)
                std_y = np.std(group_costs)
                
                # Create ellipse (2 standard deviations)
                ellipse = Ellipse(
                    xy=(mean_x, mean_y),
                    width=4 * std_x,   # 2 std in each direction
                    height=4 * std_y,
                    angle=0,
                    facecolor=group_colors.get(group_name, '#CCCCCC'),
                    alpha=0.15,
                    edgecolor=group_colors.get(group_name, '#999999'),
                    linewidth=2,
                    linestyle='--',
                    zorder=1
                )
                ax.add_patch(ellipse)
                
                # Add group label
                ax.text(
                    mean_x, mean_y + 2 * std_y + 2000,
                    group_name,
                    fontsize=10,
                    fontweight='bold',
                    ha='center',
                    va='bottom',
                    color=group_colors.get(group_name, '#666666'),
                    bbox=dict(
                        boxstyle='round,pad=0.3',
                        facecolor='white',
                        edgecolor=group_colors.get(group_name, '#999999'),
                        alpha=0.8
                    ),
                    zorder=10
                )
        
        # Plot each strategy scatter (on top of ellipses)
        for strategy in inc_costs.columns:
            if strategy == reference_strategy:
                continue
            
            ax.scatter(
                inc_effects[strategy],
                inc_costs[strategy],
                alpha=0.4,
                s=12,
                label=strategy,
                zorder=5
            )
        
        # Add reference lines
        add_reference_line(ax, 0, 'horizontal', color='gray', alpha=0.5)
        add_reference_line(ax, 0, 'vertical', color='gray', alpha=0.5)
        
        # Add WTP threshold
        add_wtp_threshold(ax, wtp, currency)
        
        # Format axes
        format_axis_currency(ax, 'y', currency)
        
        # Place legend below the plot
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            ncol=3,
            frameon=True,
            fancybox=False,
            shadow=False
        )
        
        # Apply tight layout first
        fig.tight_layout()
        
        # Set y-axis limits if specified
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def main():
    """Generate CE plane figures with grouping ellipses."""
    
    print("=" * 70)
    print("Generating CE Plane Figures with Strategy Groupings")
    print("=" * 70)
    
    base_dir = Path('outputs_v4/run_latest')
    analyses = [
        ('AU', 'healthcare'),
        ('AU', 'societal'),
        ('NZ', 'healthcare'),
        ('NZ', 'societal')
    ]
    
    standards = JournalStandards()
    
    # Define strategy groups
    strategy_groups = {
        'Standard Care': ['UC', 'UC+Li', 'UC+AA'],
        'Novel Therapies': ['IV-KA', 'IN-EKA', 'PO-KA', 'PO-PSI'],
        'Established Alternatives': ['ECT', 'KA-ECT', 'rTMS']
    }
    
    for jur, persp in analyses:
        print(f"\n{jur} - {persp}...")
        
        figures_dir = base_dir / 'figures' / jur / persp
        data_path = Path(f'data/sample/psa_sample_{jur}_{persp}.csv')
        
        if not data_path.exists():
            print("  ✗ Skipping - no PSA data found")
            continue
        
        # Load PSA data
        psa = load_psa_data(data_path, persp, jur)
        costs = psa.table.pivot(index='draw', columns='strategy', values='cost')
        effects = psa.table.pivot(index='draw', columns='strategy', values='effect')
        
        # Generate CE plane with groupings
        output_path = figures_dir / 'ce_plane_grouped'
        try:
            plot_ce_plane_with_groups(
                costs=costs,
                effects=effects,
                reference_strategy='UC',
                output_path=output_path,
                wtp=50000,
                currency='A$',
                title=f"Cost-Effectiveness Plane with Strategy Groups ({jur} {persp.title()})",
                standards=standards,
                ylim=(-5000, 55000),
                strategy_groups=strategy_groups
            )
            print("  ✓ Generated ce_plane_grouped.svg, .pdf, .png")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✓ Grouped CE Plane Generation Complete!")
    print("=" * 70)
    print(f"\nLocation: {base_dir}/figures/*/*/ce_plane_grouped.*")
    print("\nGroups displayed:")
    for group_name, strategies in strategy_groups.items():
        print(f"  • {group_name}: {', '.join(strategies)}")


if __name__ == '__main__':
    main()
