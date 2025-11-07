"""
Automated Validation and Quality Checks

Output validation, completeness checking, and publication readiness validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any

import pandas as pd

from trd_cea.core.validation import (
    ValidationReport
)

__all__ = [
    "OutputCompleteness",
    "PublicationReadiness",
    "QualityCheckReport",
    "run_quality_checks",
    "generate_automated_report",
]


@dataclass
class OutputCompleteness:
    """Container for output completeness check results."""
    
    expected_files: List[str]
    found_files: List[str]
    missing_files: List[str]
    completeness_percentage: float
    
    @property
    def is_complete(self) -> bool:
        """Check if all expected files are present."""
        return len(self.missing_files) == 0


@dataclass
class PublicationReadiness:
    """Container for publication readiness check results."""
    
    total_figures: int
    compliant_figures: int
    non_compliant_figures: List[str]
    compliance_percentage: float
    issues: List[str]
    
    @property
    def is_ready(self) -> bool:
        """Check if publication ready."""
        return len(self.non_compliant_figures) == 0


@dataclass
class QualityCheckReport:
    """Comprehensive quality check report."""
    
    output_completeness: OutputCompleteness
    publication_readiness: PublicationReadiness
    validation_report: ValidationReport
    overall_status: str  # 'pass', 'warning', 'fail'
    recommendations: List[str]


def check_output_completeness(
    output_dir: Path,
    expected_analyses: List[str]
) -> OutputCompleteness:
    """
    Check completeness of analysis outputs.
    
    Args:
        output_dir: Output directory
        expected_analyses: List of expected analysis types
    
    Returns:
        OutputCompleteness report
    """
    # Define expected files for each analysis type
    expected_files_map = {
        'cea': [
            'cea_deterministic.csv',
            'cea_probabilistic.csv',
            'ceac.csv',
            'ceaf.csv',
            'icer_table.csv',
        ],
        'dcea': [
            'dcea_atkinson.csv',
            'dcea_ede_qalys.csv',
            'dcea_equity_impact.csv',
            'distributional_ceac.csv',
        ],
        'voi': [
            'evpi.csv',
            'evppi.csv',
            'evsi.csv',
            'population_evpi.csv',
        ],
        'vbp': [
            'vbp_curves.csv',
            'threshold_prices.csv',
            'price_probability.csv',
        ],
        'bia': [
            'bia_annual.csv',
            'bia_cumulative.csv',
            'market_share.csv',
        ],
        'sensitivity': [
            'owsa_results.csv',
            'twsa_results.csv',
            'tornado_data.csv',
        ],
        'subgroup': [
            'subgroup_icer.csv',
            'subgroup_nmb.csv',
            'subgroup_qalys.csv',
        ],
    }
    
    # Collect expected files
    expected_files = []
    for analysis in expected_analyses:
        if analysis in expected_files_map:
            expected_files.extend(expected_files_map[analysis])
    
    # Check which files exist
    found_files = []
    missing_files = []
    
    for expected_file in expected_files:
        file_path = output_dir / expected_file
        if file_path.exists():
            found_files.append(expected_file)
        else:
            missing_files.append(expected_file)
    
    # Calculate completeness
    if len(expected_files) > 0:
        completeness = len(found_files) / len(expected_files) * 100
    else:
        completeness = 100.0
    
    return OutputCompleteness(
        expected_files=expected_files,
        found_files=found_files,
        missing_files=missing_files,
        completeness_percentage=completeness
    )


def check_publication_readiness(
    figures_dir: Path,
    required_dpi: int = 300,
    required_formats: List[str] = None
) -> PublicationReadiness:
    """
    Check publication readiness of figures.
    
    Args:
        figures_dir: Figures directory
        required_dpi: Minimum DPI requirement
        required_formats: Required file formats
    
    Returns:
        PublicationReadiness report
    """
    if required_formats is None:
        required_formats = ['png', 'pdf', 'tiff']
    
    issues = []
    non_compliant_figures = []
    
    # Check if figures directory exists
    if not figures_dir.exists():
        return PublicationReadiness(
            total_figures=0,
            compliant_figures=0,
            non_compliant_figures=[],
            compliance_percentage=0.0,
            issues=['Figures directory does not exist']
        )
    
    # Get all figure files
    figure_files = []
    for fmt in required_formats:
        figure_files.extend(list(figures_dir.glob(f'*.{fmt}')))
    
    if not figure_files:
        return PublicationReadiness(
            total_figures=0,
            compliant_figures=0,
            non_compliant_figures=[],
            compliance_percentage=0.0,
            issues=['No figure files found']
        )
    
    # Group by base name
    figure_groups = {}
    for fig_file in figure_files:
        base_name = fig_file.stem
        if base_name not in figure_groups:
            figure_groups[base_name] = []
        figure_groups[base_name].append(fig_file.suffix[1:])  # Remove leading dot
    
    # Check each figure group
    total_figures = len(figure_groups)
    compliant_figures = 0
    
    for base_name, formats in figure_groups.items():
        is_compliant = True
        
        # Check format completeness
        missing_formats = set(required_formats) - set(formats)
        if missing_formats:
            issues.append(f"{base_name}: Missing formats {missing_formats}")
            is_compliant = False
        
        # Check file size (basic check)
        for fmt in formats:
            file_path = figures_dir / f"{base_name}.{fmt}"
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > 10:  # Max 10 MB
                issues.append(f"{base_name}.{fmt}: File size ({file_size_mb:.1f} MB) exceeds 10 MB")
                is_compliant = False
        
        if is_compliant:
            compliant_figures += 1
        else:
            non_compliant_figures.append(base_name)
    
    # Calculate compliance
    compliance = (compliant_figures / total_figures * 100) if total_figures > 0 else 0.0
    
    return PublicationReadiness(
        total_figures=total_figures,
        compliant_figures=compliant_figures,
        non_compliant_figures=non_compliant_figures,
        compliance_percentage=compliance,
        issues=issues
    )


def run_quality_checks(
    output_dir: Path,
    figures_dir: Path,
    expected_analyses: List[str],
    config_dict: Optional[Dict[str, Any]] = None
) -> QualityCheckReport:
    """
    Run comprehensive quality checks.
    
    Args:
        output_dir: Output directory
        figures_dir: Figures directory
        expected_analyses: List of expected analysis types
        config_dict: Configuration dictionary
    
    Returns:
        QualityCheckReport
    """
    # Check output completeness
    output_completeness = check_output_completeness(output_dir, expected_analyses)
    
    # Check publication readiness
    publication_readiness = check_publication_readiness(figures_dir)
    
    # Run validation
    from trd_cea.core.validation import run_comprehensive_validation
    validation_report = run_comprehensive_validation(
        output_dir=output_dir,
        figures_dir=figures_dir,
        config_dict=config_dict
    )
    
    # Determine overall status
    if (not output_completeness.is_complete or 
        not publication_readiness.is_ready or 
        validation_report.overall_status == 'fail'):
        overall_status = 'fail'
    elif (output_completeness.completeness_percentage < 100 or
          publication_readiness.compliance_percentage < 100 or
          validation_report.overall_status == 'warning'):
        overall_status = 'warning'
    else:
        overall_status = 'pass'
    
    # Generate recommendations
    recommendations = []
    
    if output_completeness.missing_files:
        recommendations.append(
            f"Generate missing output files: {', '.join(output_completeness.missing_files[:5])}"
        )
    
    if publication_readiness.non_compliant_figures:
        recommendations.append(
            f"Fix non-compliant figures: {', '.join(publication_readiness.non_compliant_figures[:5])}"
        )
    
    if validation_report.n_errors > 0:
        recommendations.append(
            f"Address {validation_report.n_errors} validation errors"
        )
    
    if validation_report.n_warnings > 0:
        recommendations.append(
            f"Review {validation_report.n_warnings} validation warnings"
        )
    
    if not recommendations:
        recommendations.append("All quality checks passed. Ready for publication.")
    
    return QualityCheckReport(
        output_completeness=output_completeness,
        publication_readiness=publication_readiness,
        validation_report=validation_report,
        overall_status=overall_status,
        recommendations=recommendations
    )


def generate_automated_report(
    quality_report: QualityCheckReport,
    output_path: Path
) -> None:
    """
    Generate automated quality check report.
    
    Args:
        quality_report: Quality check report
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create markdown report
    report_lines = [
        "# V4 Quality Check Report",
        "",
        f"**Overall Status**: {quality_report.overall_status.upper()}",
        "",
        "## Output Completeness",
        "",
        f"- **Completeness**: {quality_report.output_completeness.completeness_percentage:.1f}%",
        f"- **Expected Files**: {len(quality_report.output_completeness.expected_files)}",
        f"- **Found Files**: {len(quality_report.output_completeness.found_files)}",
        f"- **Missing Files**: {len(quality_report.output_completeness.missing_files)}",
        "",
    ]
    
    if quality_report.output_completeness.missing_files:
        report_lines.append("### Missing Files")
        report_lines.append("")
        for missing_file in quality_report.output_completeness.missing_files:
            report_lines.append(f"- {missing_file}")
        report_lines.append("")
    
    report_lines.extend([
        "## Publication Readiness",
        "",
        f"- **Compliance**: {quality_report.publication_readiness.compliance_percentage:.1f}%",
        f"- **Total Figures**: {quality_report.publication_readiness.total_figures}",
        f"- **Compliant Figures**: {quality_report.publication_readiness.compliant_figures}",
        f"- **Non-Compliant Figures**: {len(quality_report.publication_readiness.non_compliant_figures)}",
        "",
    ])
    
    if quality_report.publication_readiness.issues:
        report_lines.append("### Issues")
        report_lines.append("")
        for issue in quality_report.publication_readiness.issues[:10]:  # Limit to 10
            report_lines.append(f"- {issue}")
        report_lines.append("")
    
    report_lines.extend([
        "## Validation Summary",
        "",
        f"- **Status**: {quality_report.validation_report.overall_status}",
        f"- **Total Checks**: {len(quality_report.validation_report.results)}",
        f"- **Passed**: {quality_report.validation_report.n_passed}",
        f"- **Warnings**: {quality_report.validation_report.n_warnings}",
        f"- **Errors**: {quality_report.validation_report.n_errors}",
        "",
    ])
    
    # Add validation errors
    errors = [r for r in quality_report.validation_report.results 
             if r.severity == 'error' and not r.passed]
    if errors:
        report_lines.append("### Validation Errors")
        report_lines.append("")
        for error in errors[:10]:  # Limit to 10
            report_lines.append(f"- **{error.check_name}**: {error.message}")
        report_lines.append("")
    
    # Add recommendations
    report_lines.extend([
        "## Recommendations",
        "",
    ])
    
    for i, recommendation in enumerate(quality_report.recommendations, 1):
        report_lines.append(f"{i}. {recommendation}")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Report generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
