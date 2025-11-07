"""
I/O utilities for health economic evaluation framework.

This module provides functions for loading and saving data, results, and parameters.

Classes:
    PSAData: Container for probabilistic sensitivity analysis data
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Union
import csv
import os
from dataclasses import dataclass


@dataclass
class PSAData:
    """Container for probabilistic sensitivity analysis data."""
    table: pd.DataFrame  # must have columns: draw, strategy, cost, effect
    config: Dict[str, Any]
    draws: int


def load_data(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load data from various file formats.
    
    Args:
        filepath: Path to the data file
        
    Returns:
        Pandas DataFrame containing the data
    """
    filepath = Path(filepath)
    
    if filepath.suffix.lower() == '.csv':
        return pd.read_csv(filepath)
    elif filepath.suffix.lower() in ['.xlsx', '.xls']:
        return pd.read_excel(filepath)
    elif filepath.suffix.lower() == '.json':
        return pd.read_json(filepath)
    elif filepath.suffix.lower() == '.parquet':
        return pd.read_parquet(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def save_results(results: Dict[str, Any], filepath: Union[str, Path], format: str = 'csv') -> None:
    """
    Save analysis results to specified format.
    
    Args:
        results: Dictionary of results to save
        filepath: Path to save the results
        format: Format to save ('csv', 'json', 'excel', 'pickle')
    """
    filepath = Path(filepath)
    
    if format == 'csv':
        # Convert results to DataFrame and save
        df = pd.DataFrame(results)
        df.to_csv(filepath, index=False)
    elif format == 'json':
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    elif format == 'excel':
        df = pd.DataFrame(results)
        df.to_excel(filepath, index=False)
    elif format == 'pickle':
        pd.DataFrame(results).to_pickle(filepath)
    else:
        raise ValueError(f"Unsupported format: {format}")


def load_psa_results(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load PSA results from specific format.
    
    Args:
        filepath: Path to the PSA results file
        
    Returns:
        DataFrame with PSA results
    """
    df = load_data(filepath)
    
    # Verify required columns exist
    required_columns = ['draw', 'strategy', 'cost', 'effect']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column in PSA results: {col}")
    
    return df


def load_parameters(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Load model parameters from YAML or JSON file.
    
    Args:
        filepath: Path to the parameter file
        
    Returns:
        Dictionary containing parameters
    """
    filepath = Path(filepath)
    
    if filepath.suffix.lower() in ['.yaml', '.yml']:
        import yaml
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    elif filepath.suffix.lower() == '.json':
        with open(filepath, 'r') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported parameter file format: {filepath.suffix}")


def validate_data_schema(df: pd.DataFrame, expected_columns: list, required_dtypes: Dict[str, type] = None) -> list[str]:
    """
    Validate data schema against expected columns and types.
    
    Args:
        df: DataFrame to validate
        expected_columns: List of expected column names
        required_dtypes: Dictionary of column name to expected type
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check for missing columns
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
    
    # Check for data types
    if required_dtypes:
        for col, expected_type in required_dtypes.items():
            if col in df.columns:
                # Check if all values are of expected type or can be converted
                try:
                    df[col].astype(expected_type)
                except ValueError:
                    errors.append(f"Column {col} has values that can't be converted to {expected_type}")
    
    return errors


def save_parameter_sensitivity_results(results: Dict[str, Any], filepath: Union[str, Path]) -> None:
    """
    Save parameter sensitivity analysis results.
    
    Args:
        results: Dictionary with sensitivity analysis results
        filepath: Path to save results
    """
    # Convert results to appropriate format and save
    # This could be a more complex format depending on the sensitivity analysis
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)