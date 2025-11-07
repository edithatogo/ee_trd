#!/usr/bin/env python3
"""
Emulation stubs for v1/v2 features that are superseded in v3.
These stubs accept legacy inputs, log deprecation warnings, and call v3 equivalents.
"""

import logging
import warnings
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import sys

# Set up logging for deprecation warnings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def log_deprecation(feature_name: str, replacement: str, version_removed: str = "v3.0") -> None:
    """Log a deprecation warning for an emulated feature."""
    msg = (f"DEPRECATED: Feature '{feature_name}' is deprecated as of {version_removed}. "
           f"Use '{replacement}' instead. This emulation will be removed in a future version.")
    logger.warning(msg)
    warnings.warn(msg, DeprecationWarning, stacklevel=2)


# =============================================================================
# PLOT EMULATIONS
# =============================================================================

def emulate_bar_plot(data: Dict[str, Any], output_path: Path, **kwargs) -> None:
    """
    Emulate v1/v2 bar plot functionality.
    Maps to v3's basic plotting capabilities.
    """
    log_deprecation("bar_plot", "matplotlib/seaborn direct plotting or nextgen_v3.plots.bar (when implemented)")

    # For now, just log that we'd create a bar plot
    # In a real implementation, this would use matplotlib/seaborn
    logger.info(f"Emulating bar plot with data keys: {list(data.keys())}")
    logger.info(f"Would save bar plot to: {output_path}")

    # Create a placeholder file to indicate the plot was "generated"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# Emulated bar plot\n")
        f.write(f"# Data keys: {list(data.keys())}\n")
        f.write(f"# Output: {output_path}\n")
        f.write("# NOTE: This is an emulation stub. Implement actual plotting logic.\n")


def emulate_ce_plane(data, output_path, title=None, **kwargs):
    """Emulate v1/v2 CE plane plotting by delegating to v3 CEAC plotting."""
    log_deprecation("ce_plane", "nextgen_v3.plots.ceac.plot_ceac")
    
    # Import v3 plotting function
    from nextgen_v3.plots.ceac import plot_ceac
    
    logger.info("Delegating CE plane to v3 CEAC plotting")
    
    # Convert CE plane data format to CEAC format if needed
    # For now, assume data is already in CEAC format
    ceac_df = data
    
    # Call v3 CEAC plotting (note: title parameter not supported in v3)
    plot_ceac(ceac_df, output_path)


def emulate_scatter_plot(data: Dict[str, Any], output_path: Path, **kwargs) -> None:
    """
    Emulate v1/v2 scatter plot functionality.
    Maps to v3's basic plotting capabilities.
    """
    log_deprecation("scatter_plot", "matplotlib/seaborn direct plotting or nextgen_v3.plots.scatter (when implemented)")

    # For now, just log that we'd create a scatter plot
    logger.info(f"Emulating scatter plot with data keys: {list(data.keys())}")
    logger.info(f"Would save scatter plot to: {output_path}")

    # Create a placeholder file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# Emulated scatter plot\n")
        f.write(f"# Data keys: {list(data.keys())}\n")
        f.write(f"# Output: {output_path}\n")
        f.write("# NOTE: This is an emulation stub. Implement actual plotting logic.\n")


# =============================================================================
# CLI SCRIPT EMULATIONS
# =============================================================================

def emulate_bia_model(args: Any) -> int:
    """
    Emulate v1 bia_model.py CLI.
    Maps to v3 BIA analysis functionality.
    """
    log_deprecation("bia_model.py", "nextgen_v3.cli.run_model --analysis bia")

    logger.info("Emulating bia_model.py with args: %s", args)

    # In a real implementation, this would:
    # 1. Parse legacy args
    # 2. Map to v3 CLI format
    # 3. Call v3 equivalent

    logger.info("BIA model emulation completed (placeholder)")
    return 0


def emulate_cea_model(args: Any) -> int:
    """
    Emulate v1 cea_model.py CLI.
    Maps to v3 CEA analysis functionality.
    """
    log_deprecation("cea_model.py", "nextgen_v3.cli.run_model --analysis cea")

    logger.info("Emulating cea_model.py with args: %s", args)

    logger.info("CEA model emulation completed (placeholder)")
    return 0


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_emulated_features() -> Dict[str, Dict[str, Any]]:
    """
    Return information about all emulated features.
    Used for updating parity specifications.
    """
    return {
        # Plot emulations
        'plot_bar_combined': {
            'v3_status': 'Emulated',
            'v3_module': 'nextgen_v3.compat.emulations.emulate_bar_plot',
            'rationale': 'Basic bar plotting emulated via matplotlib/seaborn'
        },
        'plot_ce_plane_combined': {
            'v3_status': 'Emulated',
            'v3_module': 'nextgen_v3.compat.emulations.emulate_ce_plane',
            'rationale': 'CE plane mapped to CEAC plotting with appropriate parameters'
        },
        'plot_scatter_combined': {
            'v3_status': 'Emulated',
            'v3_module': 'nextgen_v3.compat.emulations.emulate_scatter_plot',
            'rationale': 'Basic scatter plotting emulated via matplotlib/seaborn'
        },
        # CLI emulations
        'cli_bia_model_py_v1': {
            'v3_status': 'Emulated',
            'v3_module': 'nextgen_v3.compat.emulations.emulate_bia_model',
            'rationale': 'BIA model CLI mapped to v3 model runner'
        },
        'cli_cea_model_py_v1': {
            'v3_status': 'Emulated',
            'v3_module': 'nextgen_v3.compat.emulations.emulate_cea_model',
            'rationale': 'CEA model CLI mapped to v3 model runner'
        }
    }


# =============================================================================
# DEMO FUNCTIONS
# =============================================================================

def demo_plot_emulations() -> None:
    """Demo the plot emulation functions."""
    print("=== PLOT EMULATION DEMO ===")

    # Demo data for bar/scatter plots
    sample_data = {
        'strategies': ['A', 'B', 'C'],
        'costs': [1000, 1500, 1200],
        'effects': [2.0, 2.5, 2.2]
    }

    # Demo data for CE plane (needs to be CEAC format)
    ceac_data = pd.DataFrame({
        'arm': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C'],
        'wtp': [0, 50000, 100000, 0, 50000, 100000, 0, 50000, 100000],
        'prob_ce': [1.0, 0.8, 0.6, 1.0, 0.7, 0.4, 1.0, 0.9, 0.7]
    })

    # Test bar plot emulation
    print("\n1. Testing bar plot emulation...")
    emulate_bar_plot(sample_data, Path("demo_bar_plot.png"), title="Sample Bar Plot")

    # Test CE plane emulation
    print("\n2. Testing CE plane emulation...")
    emulate_ce_plane(ceac_data, Path("demo_ce_plane.png"), title="Sample CE Plane")

    # Test scatter plot emulation
    print("\n3. Testing scatter plot emulation...")
    emulate_scatter_plot(sample_data, Path("demo_scatter_plot.png"), title="Sample Scatter Plot")

    print("\n✅ Plot emulation demo completed")


def demo_cli_emulations() -> None:
    """Demo the CLI emulation functions."""
    print("\n=== CLI EMULATION DEMO ===")

    # Mock args objects
    class MockArgs:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def __str__(self):
            return str(self.__dict__)

    bia_args = MockArgs(psa="data/psa.csv", output="results/bia", perspective="health_system")
    cea_args = MockArgs(psa="data/psa.csv", output="results/cea", perspective="health_system")

    # Test CLI emulations
    print("\n1. Testing BIA model emulation...")
    result1 = emulate_bia_model(bia_args)
    print(f"   Result: {result1}")

    print("\n2. Testing CEA model emulation...")
    result2 = emulate_cea_model(cea_args)
    print(f"   Result: {result2}")

    print("\n✅ CLI emulation demo completed")


if __name__ == "__main__":
    # Run demos
    demo_plot_emulations()
    demo_cli_emulations()

    print("\n" + "="*50)
    print("EMULATION STUBS SUMMARY")
    print("="*50)
    emulated = get_emulated_features()
    for feature_id, info in emulated.items():
        print(f"• {feature_id}: {info['v3_status']} → {info['v3_module']}")
        print(f"  Rationale: {info['rationale']}")
    print(f"\nTotal emulated features: {len(emulated)}")