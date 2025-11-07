"""Reusable helpers for building numeric grids used in analysis scripts."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class GridSpec:
    """Specification describing a numeric grid."""

    minimum: float
    maximum: float
    step: float
    inclusive: bool = True

    def validate(self) -> None:
        if not np.isfinite(self.minimum):
            raise ValueError("Grid minimum must be finite")
        if not np.isfinite(self.maximum):
            raise ValueError("Grid maximum must be finite")
        if not np.isfinite(self.step):
            raise ValueError("Grid step must be finite")
        if self.step <= 0:
            raise ValueError("Grid step must be positive")
        if self.maximum < self.minimum:
            raise ValueError("Grid maximum must be >= minimum")

    def build(self) -> np.ndarray:
        """Construct the numeric grid as a :class:`numpy.ndarray`."""

        self.validate()
        span = self.maximum - self.minimum
        if span == 0:
            return np.array([float(self.minimum)])

        n_steps = int(math.floor(span / self.step + 1e-9))
        grid = self.minimum + self.step * np.arange(n_steps + 1)
        if self.inclusive and (grid.size == 0 or grid[-1] < self.maximum - 1e-9):
            grid = np.append(grid, self.maximum)
        return np.round(grid, 10)


def build_grid(minimum: float, maximum: float, step: float, inclusive: bool = True) -> np.ndarray:
    """Convenience wrapper returning a numeric grid."""

    spec = GridSpec(minimum=minimum, maximum=maximum, step=step, inclusive=inclusive)
    return spec.build()


def ensure_strictly_increasing(values: Sequence[float]) -> None:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size < 1:
        raise ValueError("Grid must be a non-empty 1-D sequence")
    if not np.all(np.isfinite(array)):
        raise ValueError("Grid contains non-finite values")
    if np.any(np.diff(array) <= 0):
        raise ValueError("Grid must be strictly increasing")


def lambda_grid(minimum: float, maximum: float, step: float) -> np.ndarray:
    """Build a willingness-to-pay grid ensuring strictly increasing output."""

    grid = build_grid(minimum, maximum, step)
    ensure_strictly_increasing(np.unique(grid))
    return grid


def price_grid(minimum: float, maximum: float, step: float) -> np.ndarray:
    """Build a price grid with the same validation as :func:`lambda_grid`."""

    grid = build_grid(minimum, maximum, step)
    ensure_strictly_increasing(np.unique(grid))
    return grid


def combine_grids(*grids: Iterable[float]) -> np.ndarray:
    """Merge multiple grids and return a sorted array of unique values."""

    concatenated = np.concatenate([np.asarray(g, dtype=float) for g in grids if g is not None])
    ensure_strictly_increasing(np.unique(concatenated))
    return np.unique(concatenated)
