"""
V4 Data Validation and Quality Assurance

Comprehensive validation framework for input data, analysis outputs, and publication readiness.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any


from analysis.core.io import PSAData

__all__ = [
    "ValidationResult",
    "ValidationReport",
    "validate_psa_data",
    "validate_analysis_outputs",
    "validate_publication_readiness",
    "run_comprehensive_validation",
]


@dataclass
class ValidationResult:
    """Container for validation results."""
    
    check_name: str
    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """Container for complete validation report."""
    
    results: List[ValidationResult]
    n_errors: int
    n_warnings: int
    n_passed: int
    overall_status: str  # 'pass', 'warning', 'fail'


def validate_psa_data(psa: PSAData) -> List[ValidationResult]:
    """
    Validate PSA data integrity and completeness.
    
    Args:
        psa: PSAData object to validate
    
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    # Check required columns
    required_columns = {'draw', 'strategy', 'cost', 'effect', 'perspective'}
    missing_columns = required_columns - set(psa.table.columns)
    
    if missing_columns:
        results.append(ValidationResult(
            check_name="Required Columns",
            passed=False,
            message=f"Missing required columns: {missing_columns}",
            severity="error",
            details={'missing_columns': list(missing_columns)}
        ))
    else:
        results.append(ValidationResult(
            check_name="Required Columns",
            passed=True,
            message="All required columns present",
            severity="info"
        ))
    
    # Check for missing values
    if 'cost' in psa.table.columns and 'effect' in psa.table.columns:
        missing_values = psa.table[['cost', 'effect']].isnull().sum()
        if missing_values.any():
            results.append(ValidationResult(
                check_name="Missing Values",
                passed=False,
                message=f"Missing values found: {missing_values.to_dict()}",
                severity="error",
                details={'missing_counts': missing_values.to_dict()}
            ))
        else:
            results.append(ValidationResult(
                check_name="Missing Values",
                passed=True,
                message="No missing values in cost/effect columns",
                severity="info"
            ))
    
    return results


def validate_analysis_outputs(
    output_dir: Path,
    expected_files: List[str]
) -> List[ValidationResult]:
    """
    Validate analysis output completeness and format.
    
    Args:
        output_dir: Directory containing analysis outputs
        expected_files: List of expected output files
    
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    if not output_dir.exists():
        results.append(ValidationResult(
            check_name="Output Directory",
            passed=False,
            message=f"Output directory does not exist: {output_dir}",
            severity="error"
        ))
        return results
    
    # Check for expected files
    missing_files = []
    for expected_file in expected_files:
        file_path = output_dir / expected_file
        if not file_path.exists():
            missing_files.append(expected_file)
    
    if missing_files:
        results.append(ValidationResult(
            check_name="Expected Files",
            passed=False,
            message=f"Missing expected files: {missing_files}",
            severity="error",
            details={'missing_files': missing_files}
        ))
    else:
        results.append(ValidationResult(
            check_name="Expected Files",
            passed=True,
            message="All expected files present",
            severity="info"
        ))
    
    return results


def validate_publication_readiness(
    figures_dir: Path,
    required_dpi: int = 300,
    required_formats: List[str] = None
) -> List[ValidationResult]:
    """
    Validate figures meet publication standards.
    
    Args:
        figures_dir: Directory containing figures
        required_dpi: Minimum DPI requirement
        required_formats: List of required formats
    
    Returns:
        List of ValidationResult objects
    """
    if required_formats is None:
        required_formats = ['png', 'pdf', 'tiff']
    
    results = []
    
    if not figures_dir.exists():
        results.append(ValidationResult(
            check_name="Figures Directory",
            passed=False,
            message=f"Figures directory does not exist: {figures_dir}",
            severity="error"
        ))
        return results
    
    # Check for figure files
    figure_files = []
    for fmt in required_formats:
        figure_files.extend(list(figures_dir.glob(f'*.{fmt}')))
    
    if not figure_files:
        results.append(ValidationResult(
            check_name="Figure Files",
            passed=False,
            message=f"No figure files found in formats: {required_formats}",
            severity="error"
        ))
    else:
        results.append(ValidationResult(
            check_name="Figure Files",
            passed=True,
            message=f"Found {len(figure_files)} figure files",
            severity="info"
        ))
    
    return results


def run_comprehensive_validation(
    psa: Optional[PSAData] = None,
    output_dir: Optional[Path] = None,
    figures_dir: Optional[Path] = None,
    config_dict: Optional[Dict[str, Any]] = None
) -> ValidationReport:
    """
    Run comprehensive validation across all components.
    
    Args:
        psa: PSAData object to validate
        output_dir: Analysis output directory
        figures_dir: Figures directory
        config_dict: Configuration dictionary
    
    Returns:
        ValidationReport with all results
    """
    all_results = []
    
    # Validate PSA data
    if psa is not None:
        all_results.extend(validate_psa_data(psa))
    
    # Summarize results
    n_errors = sum(1 for r in all_results if r.severity == 'error' and not r.passed)
    n_warnings = sum(1 for r in all_results if r.severity == 'warning' and not r.passed)
    n_passed = sum(1 for r in all_results if r.passed)
    
    if n_errors > 0:
        overall_status = 'fail'
    elif n_warnings > 0:
        overall_status = 'warning'
    else:
        overall_status = 'pass'
    
    return ValidationReport(
        results=all_results,
        n_errors=n_errors,
        n_warnings=n_warnings,
        n_passed=n_passed,
        overall_status=overall_status
    )
