"""
TRD CEA Analysis Toolkit.

A comprehensive toolkit for conducting health economic evaluations comparing 
psychedelic therapies against electroconvulsive therapy (ECT) for treatment-resistant depression (TRD).
"""

__version__ = "0.4.0"
__author__ = "TRD CEA Development Team"
__email__ = "trd-cea-dev@example.com"
__license__ = "Apache 2.0"
__maintainer__ = "TRD CEA Development Team"
__status__ = "Development"
__copyright__ = "2025, NSW Health Department"

# Import key modules to make them available at package level
from . import core
from . import models
from . import analysis
from . import plotting

# Define what gets imported with "from trd_cea import *"
__all__ = ["core", "models", "analysis", "plotting"]