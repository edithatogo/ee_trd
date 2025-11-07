"""
V4 Core Utilities

Core utilities used across all V4 analysis types.
Consolidates and enhances functionality from V2 analysis_core and V3 utils.
"""

__version__ = "4.0.0"

# Import all core modules
from . import io
from . import nmb
from . import deltas
from . import config
from . import validation

__all__ = [
    "io",
    "nmb",
    "deltas",
    "config",
    "validation",
]
