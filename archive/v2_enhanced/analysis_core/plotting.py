"""Centralised plotting helpers for analysis outputs."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence, Tuple

import matplotlib.pyplot as plt

__all__ = [
    "DEFAULT_STYLE",
    "DEFAULT_FIGSIZE",
    "DEFAULT_DPI",
    "DEFAULT_FORMATS",
    "FigureArtifacts",
    "journal_style",
    "figure_context",
    "init_figure",
    "save_multiformat",
    "save_figure_multiformat",
    "add_horizontal_reference",
    "add_vertical_reference",
    "ensure_legend",
    "write_caption",
    "write_figure_caption",
]

DEFAULT_STYLE = "seaborn-v0_8-darkgrid"
DEFAULT_FIGSIZE: Tuple[float, float] = (8.0, 5.0)
DEFAULT_DPI = 300
DEFAULT_FORMATS = ("png", "svg", "pdf")


@dataclass
class FigureArtifacts:
    """Metadata about saved figures."""

    base_path: Path
    formats: Sequence[str]

    @property
    def paths(self) -> List[Path]:
        return [self.base_path.with_suffix(f".{fmt}") for fmt in self.formats]


@contextmanager
def journal_style(style: str = DEFAULT_STYLE) -> Iterator[None]:
    """Temporarily apply the configured Matplotlib style."""

    original = plt.rcParams.copy()
    plt.style.use(style)
    # Set journal-appropriate font sizes
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 11,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
    })
    try:
        yield
    finally:
        plt.rcParams.update(original)


@contextmanager
def figure_context(
    title: str,
    xlabel: str,
    ylabel: str,
    *,
    figsize: Tuple[float, float] = DEFAULT_FIGSIZE,
    dpi: int = DEFAULT_DPI,
    style: str = DEFAULT_STYLE,
) -> Iterator[tuple[plt.Figure, plt.Axes]]:
    """Provide a styled figure/axes pair and restore style afterwards."""

    with journal_style(style):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(labelsize=10)
        yield fig, ax


def init_figure(
    title: str,
    xlabel: str,
    ylabel: str,
    *,
    figsize: Tuple[float, float] = DEFAULT_FIGSIZE,
    dpi: int = DEFAULT_DPI,
) -> tuple[plt.Figure, plt.Axes]:
    """Create a figure/axes pair without modifying global style."""

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(labelsize=10)
    return fig, ax


def save_multiformat(
    fig: plt.Figure,
    outdir: Path,
    filename_stem: str,
    *,
    formats: Iterable[str] = DEFAULT_FORMATS,
    dpi: int = DEFAULT_DPI,
    bbox_inches: str = "tight",
) -> FigureArtifacts:
    """Persist a figure to ``outdir`` in multiple formats."""

    outdir.mkdir(parents=True, exist_ok=True)
    unique_formats = tuple(dict.fromkeys(formats))
    base_path = outdir / filename_stem
    for fmt in unique_formats:
        target = base_path.with_suffix(f".{fmt}")
        fig.savefig(target, dpi=dpi, bbox_inches=bbox_inches)
    return FigureArtifacts(base_path=base_path, formats=unique_formats)


def save_figure_multiformat(
    fig: plt.Figure,
    outdir: Path,
    figure_name: str,
    *,
    formats: Iterable[str] = DEFAULT_FORMATS,
    dpi: int = DEFAULT_DPI,
    bbox_inches: str = "tight",
) -> FigureArtifacts:
    """Persist a figure to ``outdir`` with 'Figure_' prefix for journal submissions."""
    filename_stem = f"Figure_{figure_name}"
    return save_multiformat(fig, outdir, filename_stem, formats=formats, dpi=dpi, bbox_inches=bbox_inches)


def add_horizontal_reference(
    ax: plt.Axes,
    y: float,
    *,
    label: str,
    color: str = "#d62728",
    linestyle: str = "--",
    linewidth: float = 1.5,
) -> None:
    ax.axhline(y, color=color, linestyle=linestyle, linewidth=linewidth, label=label)


def add_vertical_reference(
    ax: plt.Axes,
    x: float,
    *,
    label: str,
    color: str = "#d62728",
    linestyle: str = ":",
    linewidth: float = 1.5,
) -> None:
    ax.axvline(x, color=color, linestyle=linestyle, linewidth=linewidth, label=label)


def ensure_legend(ax: plt.Axes, *, frameon: bool = False, location: str | int | None = None) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, frameon=frameon, loc=location)


def write_caption(outdir: Path, filename: str, text: str) -> Path:
    """Write a Markdown caption file alongside figure outputs."""

    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / filename
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def write_figure_caption(
    outdir: Path,
    figure_name: str,
    *,
    perspective: str,
    lambda_value: float | None = None,
    comparator: str,
    interpretation: str,
    additional_notes: str = "",
) -> Path:
    """Write a journal-ready caption file for a figure."""
    filename = f"Figure_{figure_name}.caption.md"
    
    caption_parts = [
        f"**Figure {figure_name}.**",
        f"Analysis conducted from a {perspective} perspective.",
    ]
    
    if lambda_value is not None:
        caption_parts.append(f"Willingness-to-pay threshold (λ) set at {lambda_value:,.0f} per unit of effect.")
    
    caption_parts.append(f"Comparator: {comparator}.")
    caption_parts.append(interpretation)
    
    if additional_notes:
        caption_parts.append(additional_notes)
    
    caption = " ".join(caption_parts)
    return write_caption(outdir, filename, caption)