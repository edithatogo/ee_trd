#!/usr/bin/env python3
"""
CLI tool to migrate v1/v2 config files to v3 format.
"""

import argparse
import yaml
import sys
from pathlib import Path
from typing import Dict, Any


def load_legacy_config(config_path: Path) -> Dict[str, Any]:
    """Load a legacy v1/v2 config file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def migrate_v1_config(legacy_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v1 config to v3 format."""
    v3_config = {}

    # Basic settings
    v3_config['time_horizon_years'] = 10  # Default, can be overridden
    v3_config['cycle_length_months'] = 1
    v3_config['currency_year'] = 2024
    v3_config['effects_unit'] = legacy_config.get('effects_unit', 'QALYs')

    # Currency
    currency = legacy_config.get('currency', 'AUD')
    v3_config['currency'] = currency

    # Jurisdictions - infer from currency
    if currency == 'AUD':
        v3_config['jurisdictions'] = ['AU']
    elif currency == 'NZD':
        v3_config['jurisdictions'] = ['NZ']
    else:
        v3_config['jurisdictions'] = ['AU']  # Default

    # Perspectives
    perspectives = legacy_config.get('perspectives', [])
    v3_config['perspectives'] = perspectives

    # Discount rates - use defaults based on jurisdiction
    jurisdiction = v3_config['jurisdictions'][0]
    if jurisdiction == 'AU':
        v3_config['discount_costs'] = {'AU': 0.05}
        v3_config['discount_qalys'] = {'AU': 0.05}
    else:  # NZ
        v3_config['discount_costs'] = {'NZ': 0.035}
        v3_config['discount_qalys'] = {'NZ': 0.035}

    # WTP grid
    v3_config['wtp_grid'] = [0, 25000, 50000, 75000, 100000]

    # Arms - map from strategies
    strategies = legacy_config.get('strategies', [])
    base_strategy = legacy_config.get('base')
    if base_strategy and base_strategy not in strategies:
        strategies.insert(0, base_strategy)

    # Map strategy names to v3 arm names using labels
    labels = legacy_config.get('labels', {})
    arms = []
    for strategy in strategies:
        # Try to map using labels, otherwise use strategy name
        display_name = labels.get(strategy, strategy)
        # Convert to v3 naming convention
        if 'IV ketamine' in display_name:
            arms.append('IV_ketamine')
        elif 'Esketamine' in display_name or 'intranasal' in display_name:
            arms.append('Esketamine')
        elif 'Psilocybin' in display_name:
            arms.append('Psilocybin')
        elif 'Oral ketamine' in display_name:
            arms.append('Oral_ketamine')
        elif 'Usual care' in display_name:
            arms.append('ECT_std')  # Default baseline
        else:
            # Keep as-is but clean up
            arm_name = strategy.replace(' ', '_').replace('-', '_')
            arms.append(arm_name)

    v3_config['arms'] = arms

    # Data schemas - basic mapping
    v3_config['data_schemas'] = {
        'clinical_induction': 'data/clinical_inputs.csv',
        'durability_relapse': 'data/clinical_inputs.csv',
        'cognition_ae_seizure': 'data/clinical_inputs.csv',
        'sessions': 'data/clinical_inputs.csv',
        'operations_per_session': 'data/clinical_inputs.csv',
        'cost_inputs_au': 'data/cost_inputs_au.csv',
        'cost_inputs_nz': 'data/cost_inputs_nz.csv',
        'utilities': 'data/clinical_inputs.csv',
        'parameters_psa': 'data/parameters_psa.csv',
        'mcda_weights': 'data/clinical_inputs.csv',
        'mcda_value_functions': 'data/clinical_inputs.csv',
        'dcea_groups': 'data/clinical_inputs.csv',
        'dcea_weights': 'data/clinical_inputs.csv',
        'provenance_sources': 'data/clinical_inputs.csv',
        'grade_certainty': 'data/clinical_inputs.csv',
        'opportunity_cost_shares': 'data/clinical_inputs.csv',
        'ecea_oop_inputs': 'data/clinical_inputs.csv',
        'income_quintiles': 'data/clinical_inputs.csv'
    }

    # Other defaults
    v3_config['correlated_psa'] = True
    v3_config['grade_penalty'] = True

    return v3_config


def migrate_v2_config(legacy_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v2 config to v3 format."""
    # V2 configs are similar to v1 but may have additional analysis defaults
    v3_config = migrate_v1_config(legacy_config)

    # Add v2-specific mappings
    if 'lambda_min' in legacy_config:
        # Update WTP grid based on v2 settings
        lambda_min = legacy_config.get('lambda_min', 0)
        lambda_max = legacy_config.get('lambda_max', 100000)
        _lambda_step = legacy_config.get('lambda_step', 1000)
        # Create a reasonable grid
        v3_config['wtp_grid'] = [lambda_min, lambda_max // 4, lambda_max // 2, (3 * lambda_max) // 4, lambda_max]

    return v3_config


def prompt_for_unmapped_keys(legacy_config: Dict[str, Any], v3_config: Dict[str, Any],
                           version: str) -> Dict[str, Any]:
    """Prompt user for any unmapped keys from legacy config."""
    # Get all keys from legacy config
    legacy_keys = set(legacy_config.keys())

    # Define known mappings
    known_mappings = {
        'base', 'perspectives', 'strategies', 'prices', 'effects_unit',
        'currency', 'labels', 'psa', 'strategies_yaml', 'lambda_min',
        'lambda_max', 'lambda_step', 'lambda_single', 'price_min',
        'price_max', 'price_step', 'outdir_root', 'seed', 'price_year',
        'time_horizon_years', 'population_by_year', 'eligibility_rate',
        'uptake_by_year', 'market_share', 'per_patient_costs', 'include_discounting'
    }

    unmapped_keys = legacy_keys - known_mappings

    if unmapped_keys:
        print(f"\n⚠️  Found {len(unmapped_keys)} unmapped keys in {version} config:")
        for key in sorted(unmapped_keys):
            value = legacy_config[key]
            print(f"  • {key}: {value}")

        print("\nThese keys were not automatically mapped to v3 config.")
        print("Please review the generated v3 config and manually add any missing settings.")

    return v3_config


def main():
    parser = argparse.ArgumentParser(
        description="Migrate v1/v2 config files to v3 format"
    )
    parser.add_argument(
        '--from-version',
        choices=['v1', 'v2'],
        required=True,
        help='Version of the input config'
    )
    parser.add_argument(
        '--in',
        dest='input_path',
        required=True,
        help='Path to legacy config file'
    )
    parser.add_argument(
        '--out',
        help='Output path for v3 config (default: nextgen_v3/config/migrated_<ver>.yaml)'
    )

    args = parser.parse_args()

    # Determine output path
    if args.out:
        output_path = Path(args.out)
    else:
        version = args.from_version
        output_path = Path(f"nextgen_v3/config/migrated_{version}.yaml")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load legacy config
        input_path = Path(args.input_path)
        print(f"Loading {args.from_version} config from {input_path}")
        legacy_config = load_legacy_config(input_path)

        # Migrate config
        if args.from_version == 'v1':
            v3_config = migrate_v1_config(legacy_config)
        else:  # v2
            v3_config = migrate_v2_config(legacy_config)

        # Prompt for unmapped keys
        v3_config = prompt_for_unmapped_keys(legacy_config, v3_config, args.from_version)

        # Write v3 config
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(v3_config, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Migrated {args.from_version} config to {output_path}")
        print("📋 Migration steps:")
        print("  1. Mapped perspectives, strategies, and basic settings")
        print("  2. Converted strategy names to v3 arm naming convention")
        print("  3. Set default discount rates and WTP grid")
        print("  4. Added standard data schema mappings")
        print("  5. Applied v3-specific defaults")

        if any(key not in ['base', 'perspectives', 'strategies', 'prices', 'effects_unit', 'currency', 'labels']
               for key in legacy_config.keys()):
            print("  ⚠️  Review unmapped keys and manually adjust the output config if needed")

    except Exception as e:
        print(f"❌ Error during config migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()