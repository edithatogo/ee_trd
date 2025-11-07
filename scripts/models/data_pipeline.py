"""
Data Pipeline Automation and Version Control Module

This module provides tools for automating data pipelines, managing data versions,
and ensuring data quality in health economic evaluations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import hashlib
import json
import pickle
import yaml
import sqlite3
from datetime import datetime
import warnings
from typing import Dict, List, Optional, Any, Tuple
import logging


class DataPipelineManager:
    """
    Manages automated data pipelines for health economic evaluation projects.
    Provides functionality for data versioning, validation, and transformation.
    """
    
    def __init__(self, data_dir: str = "data/", cache_dir: str = "cache/"):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Metadata file to track data versions and transformations
        self.metadata_file = self.data_dir / "pipeline_metadata.json"
        self.load_metadata()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def load_metadata(self):
        """Load pipeline metadata, initialize if doesn't exist."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "datasets": {},
                "transformations": {},
                "pipeline_history": []
            }
    
    def save_metadata(self):
        """Save pipeline metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def hash_file(self, filepath: Path) -> str:
        """Generate hash for file to detect changes."""
        with open(filepath, "rb") as f:
            file_hash = hashlib.sha256()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    
    def validate_dataset(self, df: pd.DataFrame, schema_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate dataset against schema requirements.
        
        Args:
            df: DataFrame to validate
            schema_info: Dictionary defining schema requirements
                {
                    'required_columns': ['col1', 'col2', ...],
                    'data_types': {'col1': 'float', 'col2': 'int', ...},
                    'value_ranges': {'col1': (min_val, max_val), ...}
                }
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required columns
        if 'required_columns' in schema_info:
            missing_cols = set(schema_info['required_columns']) - set(df.columns)
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
        
        # Check data types
        if 'data_types' in schema_info:
            for col, expected_dtype in schema_info['data_types'].items():
                if col in df.columns:
                    actual_dtype = str(df[col].dtype)
                    if expected_dtype.lower() not in actual_dtype.lower():
                        errors.append(f"Column '{col}' has wrong type: expected {expected_dtype}, got {actual_dtype}")
        
        # Check value ranges
        if 'value_ranges' in schema_info:
            for col, (min_val, max_val) in schema_info['value_ranges'].items():
                if col in df.columns:
                    if df[col].min() < min_val or df[col].max() > max_val:
                        errors.append(f"Column '{col}' has values outside range [{min_val}, {max_val}]")
        
        # Additional validation checks
        if 'no_nulls' in schema_info and schema_info['no_nulls']:
            if df.isnull().any().any():
                null_cols = df.columns[df.isnull().any()].tolist()
                errors.append(f"Unexpected null values in columns: {null_cols}")
        
        return len(errors) == 0, errors
    
    def load_data_with_validation(self, filepath: str, schema_info: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Load data file with optional validation.
        
        Args:
            filepath: Path to data file
            schema_info: Schema requirements for validation
        
        Returns:
            Validated DataFrame
        """
        filepath = Path(filepath)
        
        # Check if file has been modified since last validation
        file_hash = self.hash_file(filepath)
        metadata_key = str(filepath)
        
        if metadata_key in self.metadata['datasets']:
            if self.metadata['datasets'][metadata_key]['hash'] == file_hash:
                # File unchanged, can return cached version if available
                cached_path = self.cache_dir / f"{filepath.name}_validated.pkl"
                if cached_path.exists():
                    self.logger.info(f"Loading cached validated data for {filepath}")
                    with open(cached_path, 'rb') as f:
                        return pickle.load(f)
        
        # Load and validate data
        self.logger.info(f"Loading and validating data from {filepath}")
        
        if filepath.suffix.lower() == '.csv':
            df = pd.read_csv(filepath)
        elif filepath.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        elif filepath.suffix.lower() == '.parquet':
            df = pd.read_parquet(filepath)
        elif filepath.suffix.lower() == '.json':
            df = pd.read_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        # Perform validation if schema provided
        if schema_info:
            is_valid, errors = self.validate_dataset(df, schema_info)
            if not is_valid:
                error_msg = f"Validation failed for {filepath}: {'; '.join(errors)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Cache validated data
        cached_path = self.cache_dir / f"{filepath.name}_validated.pkl"
        with open(cached_path, 'wb') as f:
            pickle.dump(df, f)
        
        # Update metadata
        self.metadata['datasets'][metadata_key] = {
            'hash': file_hash,
            'last_validated': str(datetime.now()),
            'shape': df.shape,
            'columns': list(df.columns),
            'schema_used': schema_info
        }
        
        self.save_metadata()
        self.logger.info(f"Successfully loaded and validated data from {filepath}")
        
        return df
    
    def apply_transformation(self, df: pd.DataFrame, transform_func, transform_name: str = "") -> pd.DataFrame:
        """
        Apply a transformation function to a DataFrame and track it in metadata.
        
        Args:
            df: Input DataFrame
            transform_func: Function to apply to the DataFrame
            transform_name: Name to identify this transformation
        
        Returns:
            Transformed DataFrame
        """
        self.logger.info(f"Applying transformation: {transform_name}")
        
        # Apply transformation
        transformed_df = transform_func(df)
        
        # Track transformation in metadata
        transform_id = f"{transform_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metadata['transformations'][transform_id] = {
            'name': transform_name,
            'applied_at': str(datetime.now()),
            'input_shape': df.shape,
            'output_shape': transformed_df.shape,
            'columns_before': list(df.columns),
            'columns_after': list(transformed_df.columns)
        }
        
        self.save_metadata()
        self.logger.info(f"Completed transformation: {transform_name}")
        
        return transformed_df
    
    def save_processed_data(self, df: pd.DataFrame, output_path: str, format: str = 'csv') -> str:
        """
        Save processed data with versioning information.
        
        Args:
            df: DataFrame to save
            output_path: Path to save the data
            format: Format to save ('csv', 'excel', 'parquet')
        
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to filename to maintain version history
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stem = output_path.stem
        suffix = output_path.suffix
        
        if format == 'csv':
            versioned_path = output_path.parent / f"{stem}_{timestamp}{suffix}"
            df.to_csv(versioned_path, index=False)
        elif format == 'excel':
            versioned_path = output_path.parent / f"{stem}_{timestamp}.xlsx"
            df.to_excel(versioned_path, index=False)
        elif format == 'parquet':
            versioned_path = output_path.parent / f"{stem}_{timestamp}.parquet"
            df.to_parquet(versioned_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Update metadata
        file_hash = self.hash_file(versioned_path)
        self.metadata['datasets'][str(versioned_path)] = {
            'hash': file_hash,
            'saved_at': str(datetime.now()),
            'shape': df.shape,
            'columns': list(df.columns),
            'creator': 'pipeline_manager'
        }
        
        self.save_metadata()
        self.logger.info(f"Saved processed data to {versioned_path}")
        
        return str(versioned_path)
    
    def get_latest_version(self, base_filename: str) -> Optional[Path]:
        """
        Get the latest version of a file based on timestamp naming convention.
        
        Args:
            base_filename: Base name of the file (without timestamp)
        
        Returns:
            Path to latest version or None if no files found
        """
        base_path = Path(base_filename)
        pattern = f"{base_path.stem}_????????_??????{base_path.suffix}"
        matching_files = list(base_path.parent.glob(pattern))
        
        if not matching_files:
            return None
        
        # Sort by modification time (newest first)
        matching_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return matching_files[0]
    
    def clear_cache(self):
        """Clear all cached files."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
        self.logger.info("Cache cleared")
    
    def log_pipeline_step(self, step_name: str, inputs: List[str], outputs: List[str], 
                         parameters: Dict[str, Any] = None):
        """Log a pipeline step for tracking and reproducibility."""
        step_record = {
            'step_name': step_name,
            'timestamp': str(datetime.now()),
            'inputs': inputs,
            'outputs': outputs,
            'parameters': parameters or {}
        }
        
        self.metadata['pipeline_history'].append(step_record)
        self.save_metadata()


class DataVersionTracker:
    """
    Tracks data versions using a simple database system.
    """
    
    def __init__(self, db_path: str = "data_versions.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with necessary tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create dataset versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT NOT NULL,
                version TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hash_value TEXT NOT NULL,
                metadata TEXT,
                UNIQUE(dataset_name, version)
            )
        """)
        
        # Create dependencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                derived_dataset_id INTEGER,
                source_dataset_id INTEGER,
                FOREIGN KEY (derived_dataset_id) REFERENCES dataset_versions(id),
                FOREIGN KEY (source_dataset_id) REFERENCES dataset_versions(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_version(self, dataset_name: str, version: str, file_path: str, 
                   hash_value: str, metadata: Dict[str, Any] = None) -> int:
        """Add a new dataset version to the tracker."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO dataset_versions (dataset_name, version, file_path, hash_value, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (dataset_name, version, file_path, hash_value, json.dumps(metadata or {})))
        
        dataset_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return dataset_id
    
    def get_latest_version(self, dataset_name: str) -> Dict[str, Any]:
        """Get the latest version of a dataset."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM dataset_versions 
            WHERE dataset_name = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (dataset_name,))
        
        result = cursor.fetchone()
        if result:
            col_names = [description[0] for description in cursor.description]
            result_dict = dict(zip(col_names, result))
            if result_dict['metadata']:
                result_dict['metadata'] = json.loads(result_dict['metadata'])
        
        conn.close()
        return result_dict if result else None
    
    def get_version_history(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Get the version history for a dataset."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM dataset_versions 
            WHERE dataset_name = ?
            ORDER BY created_at DESC
        """, (dataset_name,))
        
        results = cursor.fetchall()
        if results:
            col_names = [description[0] for description in cursor.description]
            history = []
            for result in results:
                result_dict = dict(zip(col_names, result))
                if result_dict['metadata']:
                    result_dict['metadata'] = json.loads(result_dict['metadata'])
                history.append(result_dict)
            return history
        
        conn.close()
        return []


def create_data_pipeline_example():
    """
    Example of how to use the data pipeline manager.
    """
    # Initialize pipeline manager
    pm = DataPipelineManager()
    
    # Define schema for validation
    schema_info = {
        'required_columns': ['strategy', 'cost', 'effect'],
        'data_types': {'cost': 'float', 'effect': 'float'},
        'value_ranges': {'cost': (0, 100000), 'effect': (0, 2)},
        'no_nulls': True
    }
    
    # Load data with validation
    # df = pm.load_data_with_validation("data/input_data.csv", schema_info)
    
    # Apply transformations
    def normalize_costs(df):
        df = df.copy()
        df['cost_normalized'] = df['cost'] / df['cost'].max()
        return df
    
    # transformed_df = pm.apply_transformation(df, normalize_costs, "normalize_costs")
    
    # Save processed data
    # pm.save_processed_data(transformed_df, "data/processed_data.csv")
    
    return pm


# Example usage function
def run_data_pipeline_workflow():
    """
    Complete workflow example using the data pipeline tools.
    """
    print("Initializing data pipeline...")
    
    # Initialize components
    pm = DataPipelineManager()
    vt = DataVersionTracker()
    
    print("Pipeline initialized successfully!")
    
    # Return managers for use in workflows
    return pm, vt