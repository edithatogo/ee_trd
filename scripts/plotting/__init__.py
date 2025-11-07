"""
V4 Plotting Framework

Publication-quality visualization for health economic evaluation.
"""

from analysis.plotting.publication import (
    JournalStandards,
    FigureArtifacts,
    journal_style,
    figure_context,
    save_multiformat,
    add_reference_line,
    format_axis_currency,
    format_axis_percentage,
    add_wtp_threshold,
    create_legend,
)

from analysis.plotting.cea_plots import (
    plot_ce_plane,
    plot_ceac,
    plot_ceaf,
    plot_inmb_distribution,
    plot_tornado,
)

from analysis.plotting.dcea_plots import (
    plot_equity_impact_plane,
    plot_atkinson_index,
    plot_ede_qalys,
    plot_distributional_ceac,
    plot_subgroup_comparison,
)

from analysis.plotting.voi_plots import (
    plot_evpi_curve,
    plot_evppi_bars,
    plot_evsi_curve,
    plot_voi_tornado,
)

from analysis.plotting.comparison_plots import (
    plot_perspective_comparison,
    plot_jurisdiction_comparison,
    plot_comprehensive_dashboard,
    plot_strategy_comparison_grid,
)

from analysis.plotting.advanced_plots import (
    plot_3d_sensitivity_surface,
    plot_parameter_interaction_heatmap,
    plot_pathway_network,
    plot_multi_dimensional_projection,
)

from analysis.plotting.vbp_plots import (
    plot_vbp_curve,
    plot_threshold_price,
    plot_price_elasticity,
    plot_multi_indication_vbp,
    plot_risk_sharing_scenarios,
)

from analysis.plotting.bia_plots import (
    plot_annual_budget_impact,
    plot_cumulative_budget_impact,
    plot_market_share_evolution,
    plot_budget_impact_breakdown,
    plot_population_impact,
    plot_affordability_analysis,
    plot_scenario_comparison,
)

__all__ = [
    # Publication framework
    "JournalStandards",
    "FigureArtifacts",
    "journal_style",
    "figure_context",
    "save_multiformat",
    "add_reference_line",
    "format_axis_currency",
    "format_axis_percentage",
    "add_wtp_threshold",
    "create_legend",
    # CEA plots
    "plot_ce_plane",
    "plot_ceac",
    "plot_ceaf",
    "plot_inmb_distribution",
    "plot_tornado",
    # DCEA plots
    "plot_equity_impact_plane",
    "plot_atkinson_index",
    "plot_ede_qalys",
    "plot_distributional_ceac",
    "plot_subgroup_comparison",
    # VOI plots
    "plot_evpi_curve",
    "plot_evppi_bars",
    "plot_evsi_curve",
    "plot_voi_tornado",
    # Comparison plots
    "plot_perspective_comparison",
    "plot_jurisdiction_comparison",
    "plot_comprehensive_dashboard",
    "plot_strategy_comparison_grid",
    # Advanced plots
    "plot_3d_sensitivity_surface",
    "plot_parameter_interaction_heatmap",
    "plot_pathway_network",
    "plot_multi_dimensional_projection",
    # VBP plots
    "plot_vbp_curve",
    "plot_threshold_price",
    "plot_price_elasticity",
    "plot_multi_indication_vbp",
    "plot_risk_sharing_scenarios",
    # BIA plots
    "plot_annual_budget_impact",
    "plot_cumulative_budget_impact",
    "plot_market_share_evolution",
    "plot_budget_impact_breakdown",
    "plot_population_impact",
    "plot_affordability_analysis",
    "plot_scenario_comparison",
]
