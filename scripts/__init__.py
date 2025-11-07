"""
TRD CEA Toolkit - Health Economic Evaluation Tools

This package provides tools for conducting health economic evaluations
comparing psychedelic therapies and other interventions for treatment-resistant depression (TRD).
"""

__version__ = "0.4.0"
__author__ = "Research Team"
__license__ = "MIT"

# Import main modules to make them available at package level
from . import core
from . import models
from . import analysis
from . import plotting

# Define what gets imported with "from trd_cea import *"
__all__ = ["core", "models", "analysis", "plotting"]