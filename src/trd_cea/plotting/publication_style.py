"""
Publication-quality styling and utilities for V3 NextGen plots.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Union

# Publication style configuration
PUBLICATION_STYLE = {
    'figure.figsize': (12, 8),
    'figure.dpi': 300,
    'font.family': 'Arial',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 11,
    'lines.linewidth': 2.5,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white'
}

# Therapy color scheme (matching V2 enhanced system)
THERAPY_COLORS = {
    'ECT_std': '#1f77b4',
    'ECT_ket_anaesthetic': '#ff7f0e', 
    'Ketamine_IV': '#2ca02c',
    'Esketamine': '#d62728',
    'Psilocybin': '#9467bd',
    'Oral_ketamine': '#8c564b'
}

# Therapy labels for publication
THERAPY_LABELS = {
    'ECT_std': 'ECT',
    'ECT_ket_anaesthetic': 'KA-ECT',
    'Ketamine_IV': 'IV-KA',
    'Esketamine': 'IN-EKA', 
    'Psilocybin': 'PO psilocybin',
    'Oral_ketamine': 'PO-KA'
}

def apply_publication_style():
    """Apply publication-quality styling to matplotlib."""
    plt.rcParams.update(PUBLICATION_STYLE)

def get_therapy_color(therapy: str) -> str:
    """Get the standardized color for a therapy."""
    return THERAPY_COLORS.get(therapy, '#333333')

def get_therapy_label(therapy: str) -> str:
    """Get the publication-ready label for a therapy."""
    return THERAPY_LABELS.get(therapy, therapy)

def format_currency(value: Union[float, int], country: str = 'AU', 
                   include_thousands_sep: bool = True) -> str:
    """Format currency for publication display."""
    if country.upper() == 'AU':
        currency_symbol = 'AUD'
    elif country.upper() == 'NZ':
        currency_symbol = 'NZD'
    else:
        currency_symbol = 'USD'
    
    if include_thousands_sep:
        return f"${value:,.0f} {currency_symbol}"
    else:
        return f"${value:.0f} {currency_symbol}"

def get_currency_label(country: str = 'AU') -> str:
    """Get currency label for axis labels."""
    if country.upper() == 'AU':
        return 'AUD per QALY'
    elif country.upper() == 'NZ':
        return 'NZD per QALY'
    else:
        return 'USD per QALY'

def save_publication_figure(fig, filepath: str, **kwargs):
    """Save figure with publication-quality settings."""
    default_kwargs = {
        'dpi': 300,
        'bbox_inches': 'tight',
        'facecolor': 'white',
        'edgecolor': 'none',
        'pad_inches': 0.1
    }
    default_kwargs.update(kwargs)
    fig.savefig(filepath, **default_kwargs)

def create_comparison_grid(n_plots: int, n_cols: int = 2) -> tuple:
    """Create subplot grid for comparison plots."""
    n_rows = int(np.ceil(n_plots / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 4*n_rows))
    
    # Ensure axes is always a list
    if n_plots == 1:
        axes = [axes]
    elif n_rows == 1:
        axes = axes.flatten()
    else:
        axes = axes.flatten()
    
    # Hide unused subplots
    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)
    
    return fig, axes[:n_plots]

def add_publication_legend(ax, **kwargs):
    """Add publication-quality legend to plot."""
    default_kwargs = {
        'frameon': True,
        'fancybox': True,
        'shadow': True,
        'framealpha': 0.9,
        'loc': 'best'
    }
    default_kwargs.update(kwargs)
    return ax.legend(**default_kwargs)

def format_axis_labels(ax, xlabel: str = None, ylabel: str = None, 
                      title: str = None):
    """Apply consistent axis labeling."""
    if xlabel:
        ax.set_xlabel(xlabel, fontweight='bold')
    if ylabel:
        ax.set_ylabel(ylabel, fontweight='bold')
    if title:
        ax.set_title(title, fontweight='bold', pad=20)

def add_wtp_threshold_line(ax, wtp_threshold: float, country: str = 'AU',
                          linestyle: str = '--', alpha: float = 0.7):
    """Add WTP threshold reference line to CE plane plots."""
    # Add diagonal line for WTP threshold
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Calculate line endpoints
    x_range = np.linspace(xlim[0], xlim[1], 100)
    y_line = wtp_threshold * x_range
    
    # Only plot within y limits
    mask = (y_line >= ylim[0]) & (y_line <= ylim[1])
    if np.any(mask):
        ax.plot(x_range[mask], y_line[mask], 
                linestyle=linestyle, color='gray', alpha=alpha,
                label=f'WTP = {format_currency(wtp_threshold, country)}')

def configure_ceaf_plot(ax, max_wtp: float = 75000, country: str = 'AU'):
    """Configure CEAF plot with optimal settings."""
    ax.set_xlim(0, max_wtp)
    ax.set_ylim(0, 1)
    ax.set_xlabel(f'Willingness-to-Pay Threshold ({get_currency_label(country)})')
    ax.set_ylabel('Probability of Being Optimal')
    ax.grid(True, alpha=0.3)

def configure_pricing_plot(ax, max_price: float = 50000, country: str = 'AU'):
    """Configure pricing plot with optimal settings."""
    ax.set_xlim(0, max_price)
    ax.set_xlabel(f'Maximum Price ({get_currency_label(country)})')
    ax.set_ylabel('Probability Cost-Effective')
    ax.grid(True, alpha=0.3)