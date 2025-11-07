#!/usr/bin/env python3
"""
Config migrator for v1/v2 compatibility.
Converts legacy config formats to v3 settings.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any

def migrate_v1_config_to_v3(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v1-style config to v3 settings.yaml format."""
    v3_config = {
        'version': '3.0',
        'analysis': {},
        'model': {},
        'output': {}
    }

    # Migrate analysis settings
    if 'lambda' in config_data:
        v3_config['analysis']['willingness_to_pay'] = config_data['lambda']

    if 'n_sim' in config_data:
        v3_config['analysis']['psa_iterations'] = config_data['n_sim']

    if 'perspectives' in config_data:
        v3_config['analysis']['perspectives'] = config_data['perspectives']

    # Migrate model settings
    if 'model_params' in config_data:
        v3_config['model'].update(config_data['model_params'])

    # Migrate output settings
    if 'output_dir' in config_data:
        v3_config['output']['base_dir'] = config_data['output_dir']

    if 'plot_formats' in config_data:
        v3_config['output']['plot_formats'] = config_data['plot_formats']

    return v3_config

def migrate_v2_strategies_to_arms(strategies_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v2 strategies.yml to v3 arms.yaml format."""
    v3_arms = {
        'version': '3.0',
        'arms': []
    }

    strategies = strategies_data.get('strategies', [])

    for strategy in strategies:
        if isinstance(strategy, str):
            # Simple string strategy
            arm = {
                'id': strategy.lower().replace(' ', '_'),
                'display_name': strategy,
                'short_name': ''.join(word[0] for word in strategy.split()).upper(),
                'route': infer_route_from_name(strategy),
                'enabled': True
            }
        elif isinstance(strategy, dict):
            # Complex strategy with properties
            arm = {
                'id': strategy.get('name', '').lower().replace(' ', '_'),
                'display_name': strategy.get('name', ''),
                'short_name': strategy.get('short_name', ''),
                'route': strategy.get('route', infer_route_from_name(strategy.get('name', ''))),
                'enabled': strategy.get('enabled', True)
            }
        else:
            continue

        v3_arms['arms'].append(arm)

    return v3_arms

def infer_route_from_name(name: str) -> str:
    """Infer administration route from therapy name."""
    name_lower = name.lower()

    if 'intranasal' in name_lower or 'nasal' in name_lower:
        return 'intranasal'
    elif 'oral' in name_lower:
        return 'oral'
    elif 'iv' in name_lower or 'infusion' in name_lower:
        return 'IV'
    elif 'ect' in name_lower:
        return 'IV'  # ECT typically involves IV induction
    else:
        return 'unknown'

def migrate_v2_analysis_defaults_to_settings(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate v2 analysis_v2_defaults.yml to v3 settings.yaml."""
    v3_settings = {
        'version': '3.0',
        'analysis': {
            'willingness_to_pay': analysis_data.get('lambda', 50000),
            'psa_iterations': analysis_data.get('n_sim', 1000),
            'perspectives': ['health_system', 'societal'],
            'jurisdictions': ['AU', 'NZ']
        },
        'model': {
            'time_horizon': analysis_data.get('time_horizon', 1),
            'discount_rate': analysis_data.get('discount_rate', 0.05),
            'currency': analysis_data.get('currency', 'AUD')
        },
        'output': {
            'plot_formats': ['png', 'svg'],
            'table_formats': ['csv', 'xlsx'],
            'report_formats': ['html', 'pdf']
        }
    }

    return v3_settings

def create_perspectives_config() -> Dict[str, Any]:
    """Create v3 perspectives.yaml configuration."""
    return {
        'version': '3.0',
        'perspectives': {
            'health_system': {
                'name': 'Health System',
                'description': 'Includes only direct healthcare costs',
                'cost_categories': ['medical', 'pharmaceutical'],
                'enabled': True
            },
            'societal': {
                'name': 'Societal',
                'description': 'Includes all costs and benefits to society',
                'cost_categories': ['medical', 'pharmaceutical', 'productivity', 'informal_care'],
                'enabled': True
            }
        }
    }

def migrate_config_file(input_path: Path, output_dir: Path) -> Dict[str, str]:
    """Migrate a single config file and return mapping of created files."""
    created_files = {}

    try:
        # Load input config
        if input_path.suffix in ['.yml', '.yaml']:
            with open(input_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif input_path.suffix == '.json':
            with open(input_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {input_path.suffix}")

        # Determine migration type based on filename/content
        filename = input_path.name.lower()

        if 'strategies' in filename or 'arms' in str(config_data.keys()):
            # Migrate to arms.yaml
            v3_arms = migrate_v2_strategies_to_arms(config_data)
            output_path = output_dir / 'arms.yaml'
            with open(output_path, 'w') as f:
                yaml.dump(v3_arms, f, default_flow_style=False)
            created_files['arms'] = str(output_path)

        elif 'analysis' in filename and 'defaults' in filename:
            # Migrate to settings.yaml
            v3_settings = migrate_v2_analysis_defaults_to_settings(config_data)
            output_path = output_dir / 'settings.yaml'
            with open(output_path, 'w') as f:
                yaml.dump(v3_settings, f, default_flow_style=False)
            created_files['settings'] = str(output_path)

        else:
            # Generic config migration
            v3_config = migrate_v1_config_to_v3(config_data)
            output_path = output_dir / f"{input_path.stem}_v3.yaml"
            with open(output_path, 'w') as f:
                yaml.dump(v3_config, f, default_flow_style=False)
            created_files['config'] = str(output_path)

    except Exception as e:
        print(f"Warning: Failed to migrate {input_path}: {e}")

    return created_files

def demo() -> Dict[str, Any]:
    """Demo function showing example config migrations."""
    examples = {}

    # Example v2 strategies migration
    v2_strategies = {
        'strategies': [
            'ECT (standard anaesthesia, IV induction)',
            'Ketamine (IV infusions)',
            'Esketamine (intranasal)',
            'Psilocybin-assisted therapy (oral + psychotherapy)'
        ]
    }

    examples['arms_migration'] = migrate_v2_strategies_to_arms(v2_strategies)

    # Example v2 analysis defaults migration
    v2_analysis = {
        'lambda': 50000,
        'n_sim': 1000,
        'time_horizon': 1,
        'discount_rate': 0.05,
        'currency': 'AUD'
    }

    examples['settings_migration'] = migrate_v2_analysis_defaults_to_settings(v2_analysis)

    # Example perspectives config
    examples['perspectives_config'] = create_perspectives_config()

    return examples

if __name__ == "__main__":
    # Demo when run directly
    examples = demo()
    print("Config Migrator Examples:")
    for name, migrated_config in examples.items():
        print(f"\n{name}:")
        print(yaml.dump(migrated_config, default_flow_style=False))