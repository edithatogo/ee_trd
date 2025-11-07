"""
Advanced Visualization Features

3D plots, interactive visualizations, and network diagrams.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple, Dict
import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D

from analysis.plotting.publication import (
    journal_style, save_multiformat, JournalStandards, _get_cmap
)

# Module logger for diagnostics
logger = logging.getLogger(__name__)


# Use the centrally defined _get_cmap from publication.py for compatibility

__all__ = [
    "plot_3d_sensitivity_surface",
    "plot_parameter_interaction_heatmap",
    "plot_pathway_network",
    "plot_multi_dimensional_projection",
    "plot_three_way_sensitivity_analysis",
    "plot_step_care_flow_diagram",
]


def plot_3d_sensitivity_surface(
    param1_values: np.ndarray,
    param2_values: np.ndarray,
    outcome_grid: np.ndarray,
    param1_name: str,
    param2_name: str,
    outcome_name: str,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
    interactive: bool = False,
    create_animation: bool = False,
    param3_values: Optional[np.ndarray] = None,
) -> Path:
    """
    Create 3D surface plot for two-way sensitivity analysis.

    Args:
        param1_values: Array of parameter 1 values
        param2_values: Array of parameter 2 values
        outcome_grid: 2D array of outcome values
        param1_name: Name of parameter 1
        param2_name: Name of parameter 2
        outcome_name: Name of outcome
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
        interactive: If True, create interactive HTML version
        create_animation: If True, create rotating animation

    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"3D Sensitivity Analysis: {param1_name} vs {param2_name} - Ketamine vs Electroconvulsive Therapy"

    if standards is None:
        standards = JournalStandards()

    # Create meshgrid
    X, Y = np.meshgrid(param1_values, param2_values)

    # Ensure outcome_grid has shape (len(param2_values), len(param1_values))
    # np.meshgrid(x, y) returns arrays with shape (len(y), len(x)) so outcome_grid
    # should match that orientation. If not, try transposing and warn the user.
    expected_shape = (len(param2_values), len(param1_values))
    if outcome_grid.shape != expected_shape:
        if outcome_grid.T.shape == expected_shape:
            outcome_grid = outcome_grid.T.copy()
            logger.warning(f"Transposed outcome_grid to match meshgrid shape {expected_shape}")
        else:
            raise ValueError(
                f"outcome_grid shape {outcome_grid.shape} does not match expected "
                f"{expected_shape} (or its transpose). Please provide a 2D array"
            )

    if interactive:
        # Create interactive Plotly version
        try:
            import plotly.graph_objects as go
            import plotly.io as pio

            # Create surface plot
            fig = go.Figure(data=[go.Surface(
                x=X, y=Y, z=outcome_grid,
                colorscale='Viridis',
                name='Sensitivity Surface',
                hovertemplate=(
                    f'{param1_name}: %{{x:.3f}}<br>'
                    f'{param2_name}: %{{y:.3f}}<br>'
                    f'{outcome_name}: %{{z:.3f}}<extra></extra>'
                )
            )])

            # Add contour lines at bottom
            fig.add_trace(go.Contour(
                x=param1_values, y=param2_values, z=outcome_grid,
                colorscale='Viridis',
                showscale=False,
                contours=dict(showlines=False),
                hoverinfo='skip'
            ))

            # Update layout
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5, y=0.95,
                    xanchor='center', yanchor='top',
                    font=dict(size=16, family='Arial, sans-serif')
                ),
                scene=dict(
                    xaxis_title=param1_name,
                    yaxis_title=param2_name,
                    zaxis_title=outcome_name,
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                ),
                width=800, height=600,
                margin=dict(l=0, r=0, b=0, t=40)
            )

            # Save interactive HTML
            html_path = output_path.with_suffix('.html')
            pio.write_html(fig, str(html_path), include_plotlyjs='cdn')

            # Also save static version
            static_path = output_path.with_suffix('.png')
            fig.write_image(str(static_path), width=800, height=600)

            return html_path

        except ImportError:
            # No logger import here, fall back without logging
            interactive = False

    # Matplotlib version (enhanced)
    with journal_style(standards):
        fig = plt.figure(figsize=(12, 9), dpi=standards.min_dpi)
        ax = fig.add_subplot(111, projection='3d')

        # Plot surface with enhanced styling
        surf = ax.plot_surface(
            X, Y, outcome_grid,
            cmap='viridis',
            alpha=0.8,
            edgecolor='none',
            antialiased=True,
            rstride=1, cstride=1
        )

        # Add filled contour projection at the bottom (avoid clipping by
        # offsetting slightly below the minimum outcome value)
        z_min = float(outcome_grid.min())
        z_max = float(outcome_grid.max())
        z_range = max(1e-6, z_max - z_min)
        contour_offset = z_min - 0.02 * z_range

        ax.contourf(
            X, Y, outcome_grid,
            zdir='z',
            offset=contour_offset,
            cmap='viridis',
            alpha=0.6,
            levels=15
        )

        # Ensure z-limits include the surface and the contour projection offset
        ax.set_zlim(contour_offset, z_max)

        # Set labels with better formatting
        ax.set_xlabel(f'{param1_name}', fontsize=11, fontweight='bold', labelpad=10)
        ax.set_ylabel(f'{param2_name}', fontsize=11, fontweight='bold', labelpad=10)
        ax.set_zlabel(f'{outcome_name}', fontsize=11, fontweight='bold', labelpad=10)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Add colorbar with better positioning
        cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=10, pad=0.1)
        cbar.set_label(f'{outcome_name}', rotation=270, labelpad=20, fontsize=10)

        # Enhanced viewing angles - create multiple perspectives
        _viewing_angles = [
            (20, 45, "Standard View"),
            (60, 45, "Top-Down View"),
            (20, 135, "Side View"),
            (0, 45, "Aerial View")
        ]

        if create_animation:
            # Create animation frames
            angles = np.linspace(0, 360, 36)  # 36 frames for smooth animation
            animation_frames = []

            for angle in angles:
                ax.view_init(elev=30, azim=angle)
                frame_path = output_path.parent / f"frame_{int(angle):03d}.png"
                fig.savefig(frame_path, dpi=150, bbox_inches='tight')
                animation_frames.append(frame_path)

            # Create GIF animation
            try:
                from PIL import Image
                frames = [Image.open(frame) for frame in animation_frames]
                gif_path = output_path.with_suffix('.gif')
                frames[0].save(
                    str(gif_path),
                    save_all=True,
                    append_images=frames[1:],
                    duration=100,  # 100ms per frame = 10 fps
                    loop=0
                )

                # Clean up frame files
                for frame in animation_frames:
                    frame.unlink()

                # Animation saved successfully

            except ImportError:
                # PIL not available for animation creation
                pass

        # Set optimal viewing angle for static plot
        ax.view_init(elev=30, azim=45)

        # Adjust layout
        plt.tight_layout()

        # Save figure in multiple formats
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

    return artifacts.base_path


def plot_parameter_interaction_heatmap(
    interaction_matrix: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create heatmap showing parameter interactions.
    
    Args:
        interaction_matrix: DataFrame with parameter interactions
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Parameter Interaction Heatmap: Ketamine vs Electroconvulsive Therapy"
    
    if standards is None:
        standards = JournalStandards()
    
    with journal_style(standards):
        fig, ax = plt.subplots(
            figsize=(10, 8),
            dpi=standards.min_dpi
        )
        
        # Create heatmap
        mat = interaction_matrix.values
        # Handle empty matrix case first to avoid numpy reduction errors.
        if mat.size == 0:
            ax.text(0.5, 0.5, 'No data provided for interaction matrix', ha='center', va='center', transform=ax.transAxes)
            im = None
        else:
            # If the matrix contains only NaNs or is constant (min == max)
            # imshow may raise warnings/errors about identical axis limits or
            # numpy reduction on all-NaN slices. Handle these degenerate cases
            # gracefully by showing an informative text instead of a heatmap.
            if np.isnan(mat).all():
                ax.text(0.5, 0.5, 'No valid numeric data in interaction matrix', ha='center', va='center', transform=ax.transAxes)
                im = None
            else:
                try:
                    mat_min = np.nanmin(mat)
                    mat_max = np.nanmax(mat)
                except (ValueError, TypeError):
                    # Fallback: treat as non-plotable
                    ax.text(0.5, 0.5, 'Unable to compute interaction ranges', ha='center', va='center', transform=ax.transAxes)
                    im = None
                else:
                    if mat_min == mat_max:
                        ax.text(0.5, 0.5, 'No variation in interaction matrix', ha='center', va='center', transform=ax.transAxes)
                        im = None
                    else:
                        im = ax.imshow(
                            mat,
                            cmap='RdBu_r',
                            aspect='auto',
                            vmin=-1,
                            vmax=1
                        )
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(interaction_matrix.columns)))
        ax.set_yticks(np.arange(len(interaction_matrix.index)))
        ax.set_xticklabels(interaction_matrix.columns, rotation=45, ha='right')
        ax.set_yticklabels(interaction_matrix.index)
        
        # Add colorbar (only if an image was created)
        if im is not None:
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label('Interaction Strength', rotation=270, labelpad=20)
        
        # Add value annotations
        for i in range(len(interaction_matrix.index)):
            for j in range(len(interaction_matrix.columns)):
                value = interaction_matrix.iloc[i, j]
                _text = ax.text(
                    j, i, f'{value:.2f}',
                    ha='center', va='center',
                    color='white' if abs(value) > 0.5 else 'black',
                    fontsize=8
                )
        
        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def _create_force_directed_layout(pathways: List[List[str]], treatments: List[str]) -> Dict[str, Tuple[float, float]]:
    """Create force-directed layout for treatment network."""
    # Simple force-directed layout implementation
    positions = {}
    n_treatments = len(treatments)

    # Place treatments in a circle initially
    for i, treatment in enumerate(treatments):
        angle = 2 * np.pi * i / n_treatments
        positions[treatment] = (np.cos(angle), np.sin(angle))

    # Apply simple force-directed iterations
    for _ in range(10):  # Limited iterations for simplicity
        new_positions = {}
        for treatment in treatments:
            # Calculate repulsive forces from other treatments
            fx, fy = 0, 0
            for other in treatments:
                if other != treatment:
                    dx = positions[treatment][0] - positions[other][0]
                    dy = positions[treatment][1] - positions[other][1]
                    dist = max(0.1, np.sqrt(dx*dx + dy*dy))
                    force = 1.0 / (dist * dist)
                    fx += force * dx / dist
                    fy += force * dy / dist

            # Calculate attractive forces from connected treatments
            for pathway in pathways:
                if treatment in pathway:
                    idx = pathway.index(treatment)
                    # Connect to previous treatment in pathway
                    if idx > 0:
                        prev_treatment = pathway[idx-1]
                        dx = positions[prev_treatment][0] - positions[treatment][0]
                        dy = positions[prev_treatment][1] - positions[treatment][1]
                        dist = max(0.1, np.sqrt(dx*dx + dy*dy))
                        force = dist * 0.1  # Attractive force
                        fx += force * dx / dist
                        fy += force * dy / dist

            # Update position
            new_positions[treatment] = (
                positions[treatment][0] + fx * 0.01,
                positions[treatment][1] + fy * 0.01
            )

        positions = new_positions

    return positions


def _create_hierarchical_layout(pathways: List[List[str]], treatments: List[str]) -> Dict[str, Tuple[float, float]]:
    """Create hierarchical layout for treatment network."""
    positions = {}

    # Find maximum pathway length for layout height
    _max_length = max(len(pathway) for pathway in pathways)

    # Group treatments by their typical position in pathways
    treatment_levels = {}
    for treatment in treatments:
        positions_in_pathways = []
        for pathway in pathways:
            if treatment in pathway:
                positions_in_pathways.append(pathway.index(treatment))
        if positions_in_pathways:
            treatment_levels[treatment] = np.mean(positions_in_pathways)
        else:
            treatment_levels[treatment] = 0

    # Sort treatments by level
    sorted_treatments = sorted(treatment_levels.items(), key=lambda x: x[1])

    # Assign positions
    level_counts = {}
    for treatment, level in sorted_treatments:
        level = int(level)
        if level not in level_counts:
            level_counts[level] = 0
        positions[treatment] = (level_counts[level], level)
        level_counts[level] += 1

    # Normalize positions
    if positions:
        x_coords = [pos[0] for pos in positions.values()]
        y_coords = [pos[1] for pos in positions.values()]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        for treatment in positions:
            x, y = positions[treatment]
            x_norm = (x - x_min) / max(1, x_max - x_min) * 2 - 1
            y_norm = (y - y_min) / max(1, y_max - y_min) * 2 - 1
            positions[treatment] = (x_norm, y_norm)

    return positions


def _create_circular_layout(treatments: List[str]) -> Dict[str, Tuple[float, float]]:
    """Create circular layout for treatment network."""
    positions = {}
    n_treatments = len(treatments)

    for i, treatment in enumerate(treatments):
        angle = 2 * np.pi * i / n_treatments
        positions[treatment] = (np.cos(angle), np.sin(angle))

    return positions


def plot_pathway_network(
    pathways: List[List[str]],
    pathway_names: List[str],
    pathway_costs: List[float],
    pathway_effects: List[float],
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
    interactive: bool = False,
    layout_algorithm: str = 'force_directed',
) -> Path:
    """
    Create enhanced network diagram showing treatment pathways.

    Args:
        pathways: List of treatment sequences
        pathway_names: Names for each pathway
        pathway_costs: Costs for each pathway
        pathway_effects: Effects for each pathway
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
        interactive: If True, create interactive HTML version
        layout_algorithm: Layout method ('force_directed', 'hierarchical', 'circular')

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Treatment Pathway Network Analysis"

    if standards is None:
        standards = JournalStandards()

    if interactive:
        # Interactive network visualization not yet implemented
        raise NotImplementedError("Interactive pathway network visualization is not yet implemented")

    # Enhanced matplotlib version
    with journal_style(standards):
        fig, ax = plt.subplots(
            figsize=(16, 10),
            dpi=standards.min_dpi
        )

        # Get unique treatments and create node positions
        all_treatments = set()
        for pathway in pathways:
            all_treatments.update(pathway)
        all_treatments = sorted(all_treatments)

        # Create positions based on layout algorithm
        if layout_algorithm == 'hierarchical':
            node_positions = _create_hierarchical_layout(pathways, all_treatments)
        elif layout_algorithm == 'circular':
            node_positions = _create_circular_layout(all_treatments)
        else:  # force_directed (default)
            node_positions = _create_force_directed_layout(pathways, all_treatments)

        # Calculate pathway statistics for coloring
        pathway_stats = []
        for cost, effect in zip(pathway_costs, pathway_effects):
            # Calculate incremental cost-effectiveness ratio (ICER) relative to baseline
            if len(pathway_costs) > 1:
                min_cost_idx = np.argmin(pathway_costs)
                min_cost, min_effect = pathway_costs[min_cost_idx], pathway_effects[min_cost_idx]
                if effect > min_effect and cost > min_cost:
                    icer = (cost - min_cost) / (effect - min_effect)
                    pathway_stats.append({
                        'cost': cost, 'effect': effect, 'icer': icer,
                        'dominated': False, 'icer_value': icer
                    })
                else:
                    pathway_stats.append({
                        'cost': cost, 'effect': effect, 'icer': None,
                        'dominated': cost > min_cost and effect <= min_effect,
                        'icer_value': float('inf') if cost > min_cost else 0
                    })
            else:
                pathway_stats.append({
                    'cost': cost, 'effect': effect, 'icer': None,
                    'dominated': False, 'icer_value': 0
                })

        # Create color map based on ICER values
        icer_values = [s['icer_value'] for s in pathway_stats if s['icer_value'] != float('inf')]
        if icer_values:
            norm_icer = Normalize(vmin=min(icer_values), vmax=max(icer_values))
            colors = _get_cmap('RdYlGn_r')(norm_icer(icer_values))
        else:
            colors = _get_cmap('tab10')(np.linspace(0, 1, len(pathways)))

        # Draw pathways with enhanced styling
        pathway_artists = []
        for pathway_idx, (pathway, name, stats) in enumerate(
            zip(pathways, pathway_names, pathway_stats)
        ):
            if stats['dominated']:
                color = 'lightgray'
                alpha = 0.3
                linewidth = 1
                linestyle = '--'
            else:
                if icer_values and stats['icer_value'] != float('inf'):
                    color = colors[len([s for s in pathway_stats[:pathway_idx] if not s['dominated']])]
                else:
                    color = _get_cmap('tab10')(pathway_idx / len(pathways))
                alpha = 0.8
                linewidth = 3
                linestyle = '-'

            # Draw pathway line with smooth curves
            x_coords = [node_positions[treatment][0] for treatment in pathway]
            y_coords = [node_positions[treatment][1] for treatment in pathway]

            # Create smooth path using spline interpolation
            if len(pathway) > 3:  # Need at least 4 points for cubic spline
                from scipy import interpolate
                tck, u = interpolate.splprep([x_coords, y_coords], s=0)
                unew = np.arange(0, 1.01, 0.01)
                out = interpolate.splev(unew, tck)
                line = ax.plot(out[0], out[1], color=color, linewidth=linewidth,
                             alpha=alpha, linestyle=linestyle, zorder=1)[0]
            else:
                line = ax.plot(x_coords, y_coords, color=color, linewidth=linewidth,
                             alpha=alpha, linestyle=linestyle, zorder=1)[0]

            pathway_artists.append(line)

            # Draw nodes with enhanced styling
        for treatment, (x, y) in node_positions.items():
            # Calculate node properties based on usage
            usage_count = sum(1 for pathway in pathways if treatment in pathway)
            node_size = 300 + usage_count * 200  # Size based on usage
            node_color = _get_cmap('Blues')(0.3 + usage_count * 0.1)  # Color based on usage

            # Draw node (use `color=` when using a single color to avoid
            # ambiguous `c=` mapping behavior warnings)
            _node = ax.scatter(x, y, s=node_size, color=node_color, alpha=0.8,
                              edgecolor='darkblue', linewidth=2, zorder=3)

            # Add treatment label with better positioning
            ax.text(x, y + 0.05, treatment, ha='center', va='bottom',
                   fontsize=9, fontweight='bold', bbox=dict(
                       boxstyle='round,pad=0.3', facecolor='white',
                       alpha=0.8, edgecolor='none'))

            # Add usage count
            ax.text(x, y - 0.05, f'n={usage_count}', ha='center', va='top',
                   fontsize=7, alpha=0.7)

        # Add pathway labels and statistics
        legend_elements = []
        for pathway_idx, (name, stats) in enumerate(zip(pathway_names, pathway_stats)):
            cost, effect = stats['cost'], stats['effect']

            if stats['dominated']:
                label = f'{name}: DOMINATED\nCost=${cost:,.0f}, Effect={effect:.2f}'
                color = 'lightgray'
            else:
                icer_text = f', ICER=${stats.get("icer", 0):,.0f}/QALY' if stats.get('icer') else ''
                label = f'{name}\nCost=${cost:,.0f}, Effect={effect:.2f}{icer_text}'
                if icer_values and stats['icer_value'] != float('inf'):
                    color = colors[len([s for s in pathway_stats[:pathway_idx] if not s['dominated']])]
                else:
                    color = _get_cmap('tab10')(pathway_idx / len(pathways))

            legend_elements.append(Line2D([0], [0], color=color, linewidth=3,
                                            label=label))

        # Enhanced legend
        legend = ax.legend(
            handles=legend_elements,
            loc='upper left',
            bbox_to_anchor=(1.02, 1),
            fontsize=8,
            title='Treatment Pathways',
            title_fontsize=10
        )
        legend.get_frame().set_alpha(0.9)

        # Set labels and title
        ax.set_xlabel('Treatment Sequence Position', fontsize=11, fontweight='bold')
        ax.set_ylabel('Treatment Hierarchy', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Remove axes for cleaner look
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # Add statistics annotation
        total_pathways = len(pathways)
        dominated_count = sum(1 for s in pathway_stats if s['dominated'])
        stats_text = f'Total Pathways: {total_pathways}\nDominated: {dominated_count}\nEfficient: {total_pathways - dominated_count}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        plt.tight_layout()

        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

    return artifacts.base_path


def plot_multi_dimensional_projection(
    data: pd.DataFrame,
    dimensions: List[str],
    output_path: Path,
    color_by: Optional[str] = None,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
    interactive: bool = False,
    normalize_method: str = 'minmax',
) -> Path:
    """
    Create enhanced multi-dimensional projection plot (parallel coordinates).

    Args:
        data: DataFrame with multiple dimensions
        dimensions: List of dimension names to plot
        output_path: Output file path
        color_by: Optional column name for coloring
        title: Optional custom title
        standards: Journal standards
        interactive: If True, create interactive HTML version
        normalize_method: Normalization method ('minmax', 'robust', 'standard')

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Multi-Dimensional Parameter Space Projection"

    if standards is None:
        standards = JournalStandards()

    # Enhanced normalization with multiple methods
    normalized_data = data[dimensions].copy()
    normalization_info = {}

    for dim in dimensions:
        values = normalized_data[dim].values
        if normalize_method == 'minmax':
            min_val, max_val = np.min(values), np.max(values)
            if max_val > min_val:
                normalized_data[dim] = (values - min_val) / (max_val - min_val)
                normalization_info[dim] = {'min': min_val, 'max': max_val, 'method': 'minmax'}
            else:
                normalized_data[dim] = 0.5
                normalization_info[dim] = {'value': min_val, 'method': 'constant'}
        elif normalize_method == 'robust':
            q25, q75 = np.percentile(values, [25, 75])
            iqr = q75 - q25
            if iqr > 0:
                normalized_data[dim] = (values - q25) / iqr
                normalization_info[dim] = {'q25': q25, 'iqr': iqr, 'method': 'robust'}
            else:
                normalized_data[dim] = (values - np.median(values)) + 0.5
                normalization_info[dim] = {'median': np.median(values), 'method': 'robust_constant'}
        elif normalize_method == 'standard':
            mean_val, std_val = np.mean(values), np.std(values)
            if std_val > 0:
                normalized_data[dim] = (values - mean_val) / std_val
                # Rescale to [0, 1] for visualization
                norm_vals = normalized_data[dim].values
                min_norm, max_norm = np.min(norm_vals), np.max(norm_vals)
                normalized_data[dim] = (norm_vals - min_norm) / (max_norm - min_norm)
                normalization_info[dim] = {'mean': mean_val, 'std': std_val, 'method': 'standard'}
            else:
                normalized_data[dim] = 0.5
                normalization_info[dim] = {'value': mean_val, 'method': 'constant'}

    if interactive:
        # Create interactive Plotly version
        try:
            import plotly.graph_objects as go
            import plotly.io as pio
            from plotly.colors import qualitative

            # Prepare data for Plotly
            _plot_data = []
            color_values = data[color_by] if color_by else None

            if color_values is not None:
                unique_colors = color_values.unique()
                color_map = {val: qualitative.Set1[i % len(qualitative.Set1)]
                           for i, val in enumerate(unique_colors)}
            else:
                color_map = None

            # Create parallel coordinates plot
            dimensions_plotly = []
            for dim in dimensions:
                dim_info = normalization_info[dim]
                if dim_info['method'] == 'minmax':
                    ticktext = [f"{dim_info['min']:.3f}", f"{dim_info['max']:.3f}"]
                    tickvals = [0, 1]
                elif dim_info['method'] == 'robust':
                    if 'q25' in dim_info:
                        ticktext = [f"{dim_info['q25']:.3f}", f"{dim_info['q25'] + dim_info['iqr']:.3f}"]
                        tickvals = [0, 1]
                    else:
                        ticktext = [f"{dim_info['median']:.3f}"]
                        tickvals = [0.5]
                else:
                    ticktext = [f"{dim_info.get('value', 0):.3f}"]
                    tickvals = [0.5]

                dimensions_plotly.append(dict(
                    label=dim,
                    values=normalized_data[dim],
                    tickvals=tickvals,
                    ticktext=ticktext
                ))

            if color_values is not None:
                fig = go.Figure(data=go.Parcoords(
                    line=dict(
                        color=color_values.map(color_map).map(lambda x: qualitative.Set1.index(x) if x in qualitative.Set1 else 0),
                        colorscale='Set1'
                    ),
                    dimensions=dimensions_plotly
                ))
            else:
                fig = go.Figure(data=go.Parcoords(
                    line=dict(color='blue', showscale=False),
                    dimensions=dimensions_plotly
                ))

            # Update layout
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5, y=0.95,
                    xanchor='center', yanchor='top',
                    font=dict(size=16, family='Arial, sans-serif')
                ),
                width=1000, height=600,
                margin=dict(l=50, r=50, b=50, t=100)
            )

            # Save interactive HTML
            html_path = output_path.with_suffix('.html')
            pio.write_html(fig, str(html_path), include_plotlyjs='cdn')

            # Also save static version
            static_path = output_path.with_suffix('.png')
            fig.write_image(str(static_path), width=1000, height=600)

            return html_path

        except ImportError:
            # Plotly not available, falling back to matplotlib
            interactive = False

    # Enhanced matplotlib version
    with journal_style(standards):
        fig, ax = plt.subplots(
            figsize=(14, 8),
            dpi=standards.min_dpi
        )

        # Set up x-axis positions
        x_positions = np.arange(len(dimensions))

        # Enhanced color handling
        if color_by and color_by in data.columns:
            unique_values = data[color_by].unique()
            colors = _get_cmap('tab10')(np.linspace(0, 1, len(unique_values)))
            color_map = dict(zip(unique_values, colors))
        else:
            color_map = None

        # Plot each data point as a line with enhanced styling
        lines = []
        for idx, row in normalized_data.iterrows():
            y_values = [row[dim] for dim in dimensions]

            if color_map:
                color = color_map[data.loc[idx, color_by]]
                label = data.loc[idx, color_by] if idx == 0 else None
                line = ax.plot(x_positions, y_values, color=color, linewidth=2, alpha=0.8,
                             label=label, zorder=2)[0]
            else:
                line = ax.plot(x_positions, y_values, color='blue', linewidth=2, alpha=0.8, zorder=2)[0]

            lines.append(line)

        # Set x-ticks and labels
        ax.set_xticks(x_positions)
        ax.set_xticklabels(dimensions, rotation=45, ha='right')

        # Add color legend if applicable
        if color_by and color_by in data.columns:
            handles, _labels = [], []
            for value, color in color_map.items():
                from matplotlib.lines import Line2D
                handles.append(Line2D([0], [0], color=color, linewidth=2, label=value))
            ax.legend(handles=handles, title=color_by, fontsize=9, title_fontsize=10)

        # Set title and labels
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Parameters', fontsize=11, fontweight='bold')
        ax.set_ylabel('Normalized Value', fontsize=11, fontweight='bold')

        # Tight layout
        plt.tight_layout()

        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

    return artifacts.base_path


def plot_three_way_sensitivity_analysis(
    param1_values: np.ndarray,
    param2_values: np.ndarray,
    param3_values: np.ndarray,
    outcome_grid: np.ndarray,
    param1_name: str,
    param2_name: str,
    param3_name: str,
    outcome_name: str,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
    interactive: bool = False,
) -> Path:
    """
    Create 3D scatter plot with color coding for three-way sensitivity analysis.

    Args:
        param1_values: Array of parameter 1 values
        param2_values: Array of parameter 2 values
        param3_values: Array of parameter 3 values
        outcome_grid: 2D array of outcome values
        param1_name: Name of parameter 1
        param2_name: Name of parameter 2
        param3_name: Name of parameter 3
        outcome_name: Name of outcome
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
        interactive: If True, create interactive HTML version

    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"Three-Way Sensitivity Analysis: {param1_name}, {param2_name}, {param3_name}"

    if standards is None:
        standards = JournalStandards()

    # Create meshgrid for color mapping
    X, Y, Z = np.meshgrid(param1_values, param2_values, param3_values, indexing='ij')
    _grid_shape = X.shape

    if interactive:
        # Create interactive Plotly version
        try:
            import plotly.graph_objects as go
            import plotly.io as pio

            # Flatten the grid for Plotly
            x_flat = X.flatten()
            y_flat = Y.flatten()
            z_flat = Z.flatten()
            outcome_flat = outcome_grid.flatten()

            # Build a simple Plotly 3D scatter figure
            fig = go.Figure(data=[
                go.Scatter3d(
                    x=x_flat, y=y_flat, z=z_flat,
                    mode='markers',
                    marker=dict(
                        size=5,
                        color=outcome_flat,
                        colorscale='Viridis',
                        colorbar=dict(title=outcome_name),
                        opacity=0.8,
                    ),
                    hovertemplate=(
                        f'{param1_name}: %{{x:.3f}}<br>'
                        f'{param2_name}: %{{y:.3f}}<br>'
                        f'{param3_name}: %{{z:.3f}}<br>'
                        f'{outcome_name}: %{{marker.color:.3f}}<extra></extra>'
                    ),
                )
            ])

            # Update layout
            fig.update_layout(
                title=dict(text=title, x=0.5, y=0.95, xanchor='center', yanchor='top'),
                scene=dict(
                    xaxis_title=param1_name,
                    yaxis_title=param2_name,
                    zaxis_title=param3_name,
                    camera=dict(eye=dict(x=1.2, y=1.2, z=1.2)),
                ),
                width=800, height=600,
                margin=dict(l=0, r=0, b=0, t=40),
            )

            # Save interactive HTML and a static PNG
            html_path = output_path.with_suffix('.html')
            pio.write_html(fig, str(html_path), include_plotlyjs='cdn')
            static_path = output_path.with_suffix('.png')
            fig.write_image(str(static_path), width=800, height=600)

            return html_path

        except ImportError:
            print("⚠️  Plotly not available, falling back to matplotlib")
            interactive = False

    # Matplotlib version (enhanced)
    with journal_style(standards):
        fig = plt.figure(figsize=(12, 9), dpi=standards.min_dpi)
        ax = fig.add_subplot(111, projection='3d')

        # Flatten the outcome grid for scatter plot
        x_flat = X.flatten()
        y_flat = Y.flatten()
        z_flat = Z.flatten()
        outcome_flat = outcome_grid.flatten()

        # Scatter plot with color mapping (vector of values -> c= is correct).
        # Guard against ambiguous cases where `outcome_flat` could be a
        # length-3/4 numeric sequence that Matplotlib interprets as an
        # RGB(A) color rather than a sequence of values to map. Build the
        # scatter color argument defensively.
        outcome_arr = np.asarray(outcome_flat)
        n_points = x_flat.size
        if outcome_arr.size == 1:
            # single scalar -> use uniform color
            color_kwargs = {"color": float(outcome_arr.item())}
        elif outcome_arr.ndim == 1 and outcome_arr.size in (3, 4) and outcome_arr.size != n_points:
            # ambiguous numeric RGB(A) sequence -> treat as a single color tuple
            color_kwargs = {"color": tuple(outcome_arr.tolist())}
        else:
            # vector of values mapping to colormap
            color_kwargs = {"c": outcome_arr, "cmap": "viridis"}

        scatter = ax.scatter(
            x_flat, y_flat, z_flat,
            s=50,
            edgecolor='k',
            alpha=0.7,
            **color_kwargs
        )

        # Set labels
        ax.set_xlabel(f'{param1_name}', fontsize=11, fontweight='bold', labelpad=10)
        ax.set_ylabel(f'{param2_name}', fontsize=11, fontweight='bold', labelpad=10)
        ax.set_zlabel(f'{param3_name}', fontsize=11, fontweight='bold', labelpad=10)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Add colorbar
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, aspect=10, pad=0.1)
        cbar.set_label(f'{outcome_name}', rotation=270, labelpad=20, fontsize=10)

        # Adjust layout
        plt.tight_layout()

        # Save figure in multiple formats
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

    return artifacts.base_path


def plot_step_care_flow_diagram(
    recommendations: List[Tuple[str, str, float]],
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create step-care flow diagram showing treatment recommendations.

    Args:
        recommendations: List of treatment recommendations (from, to, weight)
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if standards is None:
        standards = JournalStandards()

    if title is None:
        title = "Step-care flow diagram"

    with journal_style(standards):
        fig, ax = plt.subplots(
            figsize=(12, 8),
            dpi=standards.min_dpi
        )

        # Extract unique treatments for axes
        all_treatments = list(set([rec[0] for rec in recommendations] + [rec[1] for rec in recommendations]))
        all_treatments.sort()

        # Create color map (use centralized helper for compatibility)
        cmap_name = 'tab10' if len(all_treatments) <= 10 else 'tab20'
        cmap = _get_cmap(cmap_name)
        _sampled_colors = cmap(np.linspace(0, 1, max(len(all_treatments), 10)))

        # Plot arrows for each recommendation
        for i, (frm, to, weight) in enumerate(recommendations):
            frm_idx = all_treatments.index(frm)
            to_idx = all_treatments.index(to)

            # Determine arrow properties
            if weight > 0:
                color = cmap(frm_idx)
                alpha = 0.8
                linewidth = 2
            else:
                color = 'lightgray'
                alpha = 0.3
                linewidth = 1

            # Draw arrow
            ax.annotate(
                '',
                xy=(to_idx, 1), xycoords='data',
                xytext=(frm_idx, 0), textcoords='data',
                arrowprops=dict(
                    arrowstyle="->",
                    color=color,
                    lw=linewidth,
                    alpha=alpha,
                    connectionstyle="arc3,rad=0.2"
                )
            )

        # Set x-ticks and labels
        ax.set_xticks(range(len(all_treatments)))
        ax.set_xticklabels(all_treatments, rotation=45, ha='right', fontsize=10)
        ax.set_yticks([])
        ax.set_ylim(0, 1)

        # Add title
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # Tight layout
        plt.tight_layout()

        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

    return artifacts.base_path
