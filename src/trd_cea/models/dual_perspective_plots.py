#!/usr/bin/env python3
"""
Dual-Perspective Plot Generator
Creates comprehensive economic evaluation plots for both health system and societal perspectives
Covers CUA, DCEA, BIA, VOI, VBP methods with consistent naming convention
"""

import sys
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Suppress matplotlib deprecation warnings
import warnings
warnings.filterwarnings("ignore", message=".*matplotlib.*", category=FutureWarning)

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from trd_cea.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

# Configure matplotlib and seaborn
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# Set reproducible seed
SEED = int(os.environ.get('SEED', 20250929))
np.random.seed(SEED)
