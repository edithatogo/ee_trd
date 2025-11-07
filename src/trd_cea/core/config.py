"""
Configuration management module for health economic evaluation.

This module handles loading, validating, and managing configuration parameters
for health economic analyses.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration parameters
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def validate_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for required top-level keys
    required_keys = ['analysis', 'strategies']
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")
    
    # Validate analysis parameters
    if 'analysis' in config:
        analysis = config['analysis']
        required_analysis_keys = ['time_horizon', 'discount_rate_costs', 'discount_rate_effects', 'wtp_threshold']
        for key in required_analysis_keys:
            if key not in analysis:
                errors.append(f"Missing required analysis parameter: {key}")
    
    # Validate strategy parameters
    if 'strategies' in config:
        for strategy, params in config['strategies'].items():
            if not isinstance(params, dict):
                errors.append(f"Strategy {strategy} parameters must be a dictionary")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def set_random_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Integer seed value for random number generators
    """
    import random
    import numpy as np
    
    random.seed(seed)
    np.random.seed(seed)