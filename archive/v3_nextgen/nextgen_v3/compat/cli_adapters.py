#!/usr/bin/env python3
"""
CLI adapters for v1/v2 compatibility.
Translates legacy CLI arguments to v3 format.
"""

import argparse
from typing import Dict, List, Any, Optional

def adapt_v1_bia_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v1 bia_model.py arguments to v3 format."""
    v3_args = {
        'command': 'run_bia',
        'jurisdiction': args.jur if hasattr(args, 'jur') else 'both',
        'perspectives': getattr(args, 'perspectives', ['health_system', 'societal']),
        'output_dir': getattr(args, 'output_dir', 'results/bia'),
        'config_file': getattr(args, 'config', 'config/analysis_v2_defaults.yml'),
    }

    # Map legacy flags
    if hasattr(args, 'country'):
        v3_args['jurisdiction'] = args.country

    return v3_args

def adapt_v1_cea_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v1 cea_model.py arguments to v3 format."""
    v3_args = {
        'command': 'run_cea',
        'jurisdiction': args.jur if hasattr(args, 'jur') else 'both',
        'perspectives': getattr(args, 'perspectives', ['health_system', 'societal']),
        'output_dir': getattr(args, 'output_dir', 'results/cea'),
        'lambda_value': getattr(args, 'lambda', 50000),
        'config_file': getattr(args, 'config', 'config/analysis_v2_defaults.yml'),
    }

    return v3_args

def adapt_v1_psa_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v1 psa_cea_model.py arguments to v3 format."""
    v3_args = {
        'command': 'run_psa',
        'jurisdiction': args.jur if hasattr(args, 'jur') else 'both',
        'perspectives': getattr(args, 'perspectives', ['health_system', 'societal']),
        'output_dir': getattr(args, 'output_dir', 'results/psa'),
        'iterations': getattr(args, 'n_sim', 1000),
        'config_file': getattr(args, 'config', 'config/analysis_v2_defaults.yml'),
    }

    return v3_args

def adapt_v2_make_ce_plane_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v2 make_ce_plane.py arguments to v3 format."""
    v3_args = {
        'command': 'run_plots',
        'plot_types': ['ce_plane'],
        'jurisdiction': args.jur if hasattr(args, 'jur') else 'both',
        'perspectives': [args.perspective] if hasattr(args, 'perspective') else ['health_system'],
        'output_dir': getattr(args, 'outdir', 'results/plots'),
        'lambda_value': getattr(args, 'lambda', 50000),
        'psa_file': getattr(args, 'psa', None),
    }

    return v3_args

def adapt_v2_make_bia_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v2 make_bia.py arguments to v3 format."""
    v3_args = {
        'command': 'run_bia',
        'jurisdiction': args.jur if hasattr(args, 'jur') else 'both',
        'perspectives': getattr(args, 'perspectives', ['health_system', 'societal']),
        'output_dir': getattr(args, 'outdir', 'results/bia'),
        'config_file': getattr(args, 'config', 'config/analysis_v2_defaults.yml'),
    }

    return v3_args

def adapt_v2_run_pipeline_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v2 run_pipeline.py arguments to v3 format."""
    v3_args = {
        'command': 'run_pipeline',
        'jurisdiction': args.jur if hasattr(args, 'jur') else 'both',
        'perspectives': getattr(args, 'perspectives', ['health_system', 'societal']),
        'output_dir': getattr(args, 'outdir_root', 'results/pipeline'),
        'config_file': getattr(args, 'config', 'config/analysis_v2_defaults.yml'),
        'psa_file': getattr(args, 'psa', None),
    }

    return v3_args

def adapt_v3_run_pipeline_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Adapt v3 run_pipeline.py arguments (mainly for orchestration compatibility)."""
    v3_args = {
        'command': 'run_pipeline',
        'jurisdiction': getattr(args, 'jur', 'both'),
        'perspectives': getattr(args, 'perspectives', ['health_system', 'societal']),
        'output_dir': getattr(args, 'output_dir', None),
        'config_file': getattr(args, 'config', 'nextgen_v3/config/settings.yaml'),
        'skip_sourcing': getattr(args, 'skip_sourcing', False),
        'skip_comparisons': getattr(args, 'skip_comparisons', False),
        'skip_voi': getattr(args, 'skip_voi', False),
    }

    return v3_args

def get_adapter_for_script(script_name: str) -> Optional[callable]:
    """Get the appropriate adapter function for a script name."""
    adapters = {
        # V1 adapters
        'bia_model.py': adapt_v1_bia_args,
        'cea_model.py': adapt_v1_cea_args,
        'psa_cea_model.py': adapt_v1_psa_args,

        # V2 adapters
        'make_ce_plane.py': adapt_v2_make_ce_plane_args,
        'make_bia.py': adapt_v2_make_bia_args,
        'run_pipeline.py': adapt_v2_run_pipeline_args,
        
        # V3 adapters (for orchestration compatibility)
        'nextgen_v3/cli/run_pipeline.py': adapt_v3_run_pipeline_args,
    }

    return adapters.get(script_name)

def create_legacy_parser(script_name: str) -> argparse.ArgumentParser:
    """Create an argument parser that accepts legacy arguments."""
    parser = argparse.ArgumentParser(description=f"Legacy adapter for {script_name}")

    # Common arguments that most scripts accept
    parser.add_argument('--jur', choices=['AU', 'NZ', 'both'], default='both',
                       help='Jurisdiction')
    parser.add_argument('--perspectives', nargs='+',
                       default=['health_system', 'societal'],
                       help='Perspectives')
    parser.add_argument('--output-dir', '--outdir', '--outdir-root',
                       help='Output directory')
    parser.add_argument('--config', help='Config file')
    parser.add_argument('--lambda', type=float, default=50000,
                       help='Willingness to pay threshold')
    parser.add_argument('--n-sim', type=int, default=1000,
                       help='Number of PSA iterations')
    parser.add_argument('--psa', help='PSA results file')
    parser.add_argument('--perspective', choices=['health_system', 'societal'],
                       default='health_system', help='Single perspective')

    return parser

def adapt_legacy_command(script_name: str, legacy_args: List[str]) -> Dict[str, Any]:
    """Adapt a legacy command to v3 format."""
    adapter = get_adapter_for_script(script_name)
    if not adapter:
        raise ValueError(f"No adapter available for {script_name}")

    # Parse legacy arguments
    parser = create_legacy_parser(script_name)
    args = parser.parse_args(legacy_args)

    # Adapt to v3 format
    return adapter(args)

def demo() -> Dict[str, Any]:
    """Demo function showing example adaptations."""
    examples = {}

    # V1 bia_model example
    examples['v1_bia'] = adapt_legacy_command('bia_model.py', [
        '--jur', 'AU', '--perspectives', 'health_system', '--output-dir', 'results/bia'
    ])

    # V1 cea_model example
    examples['v1_cea'] = adapt_legacy_command('cea_model.py', [
        '--jur', 'both', '--lambda', '30000', '--output-dir', 'results/cea'
    ])

    # V2 make_ce_plane example
    examples['v2_ce_plane'] = adapt_legacy_command('make_ce_plane.py', [
        '--jur', 'NZ', '--perspective', 'societal', '--lambda', '40000',
        '--outdir', 'results/plots', '--psa', 'data/psa_results.csv'
    ])

    # V2 run_pipeline example
    examples['v2_pipeline'] = adapt_legacy_command('run_pipeline.py', [
        '--jur', 'both', '--perspectives', 'health_system', 'societal',
        '--outdir-root', 'results/full_analysis', '--psa', 'data/psa_extended.csv'
    ])

    return examples

if __name__ == "__main__":
    # Demo when run directly
    examples = demo()
    print("CLI Adapter Examples:")
    for name, adapted_args in examples.items():
        print(f"\n{name}:")
        for key, value in adapted_args.items():
            print(f"  {key}: {value}")