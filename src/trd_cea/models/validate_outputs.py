"""
Validate all V4 outputs for publication readiness.
"""
import pandas as pd
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.pipeline.quality_checks import (  # noqa: E402
    check_output_completeness,
    check_publication_readiness,
    run_quality_checks
)


def validate_analysis_outputs(results_dir: Path):
    """Validate analysis output files."""
    print("\n" + "=" * 60)
    print("Validating Analysis Outputs")
    print("=" * 60)
    
    _expected_files = [
        'cea_deterministic.csv',
        'cea_incremental.csv',
        'cea_frontier.csv',
        'ceac.csv',
        'ceaf.csv',
        'evpi.csv',
        'population_evpi.csv',
        'dcea_summary.csv',
    ]
    
    completeness = check_output_completeness(results_dir, ['cea', 'voi', 'dcea'])
    
    print(f"\n✓ Output Completeness: {completeness.completeness_percentage:.1f}%")
    print(f"  - Expected files: {len(completeness.expected_files)}")
    print(f"  - Found files: {len(completeness.found_files)}")
    print(f"  - Missing files: {len(completeness.missing_files)}")
    
    if completeness.missing_files:
        print("\n  Missing files:")
        for file in completeness.missing_files:
            print(f"    ✗ {file}")
    
    return completeness


def validate_tables(tables_dir: Path):
    """Validate supplementary tables."""
    print("\n" + "=" * 60)
    print("Validating Supplementary Tables")
    print("=" * 60)
    
    if not tables_dir.exists():
        print(f"  ✗ Tables directory not found: {tables_dir}")
        return None
    
    tables = list(tables_dir.glob('S*.csv'))
    print(f"\n✓ Found {len(tables)} supplementary tables")
    
    # Validate each table
    valid_tables = 0
    for table_path in sorted(tables):
        try:
            df = pd.read_csv(table_path)
            if len(df) > 0:
                print(f"  ✓ {table_path.name}: {len(df)} rows, {len(df.columns)} columns")
                valid_tables += 1
            else:
                print(f"  ✗ {table_path.name}: Empty table")
        except Exception as e:
            print(f"  ✗ {table_path.name}: Error - {e}")
    
    return {'total': len(tables), 'valid': valid_tables}


def validate_figures(figures_dir: Path):
    """Validate publication figures."""
    print("\n" + "=" * 60)
    print("Validating Publication Figures")
    print("=" * 60)
    
    if not figures_dir.exists():
        print(f"  ⚠ Figures directory not found: {figures_dir}")
        print("  Note: Figure generation framework is ready but not executed")
        return None
    
    readiness = check_publication_readiness(figures_dir)
    
    print(f"\n✓ Publication Readiness: {readiness.compliance_percentage:.1f}%")
    print(f"  - Total figures: {readiness.total_figures}")
    print(f"  - Compliant figures: {readiness.compliant_figures}")
    
    if readiness.issues:
        print("\n  Issues:")
        for issue in readiness.issues[:5]:  # Show first 5
            print(f"    ⚠ {issue}")
    
    return readiness


def generate_validation_report(results_dir: Path, tables_dir: Path, figures_dir: Path):
    """Generate comprehensive validation report."""
    print("\n" + "=" * 60)
    print("Generating Validation Report")
    print("=" * 60)
    
    report = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'version': 'V4',
        'validation_results': {}
    }
    
    # Run quality checks
    quality_report = run_quality_checks(
        output_dir=results_dir,
        figures_dir=figures_dir,
        expected_analyses=['cea', 'voi', 'dcea']
    )
    
    report['validation_results']['overall_status'] = quality_report.overall_status
    report['validation_results']['output_completeness'] = {
        'percentage': quality_report.output_completeness.completeness_percentage,
        'is_complete': quality_report.output_completeness.is_complete,
    }
    report['validation_results']['publication_readiness'] = {
        'percentage': quality_report.publication_readiness.compliance_percentage,
        'is_ready': quality_report.publication_readiness.is_ready,
    }
    report['validation_results']['recommendations'] = quality_report.recommendations
    
    # Save report
    report_path = results_dir / 'validation_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Validation report saved: {report_path}")
    
    return report


def main():
    """Run complete validation."""
    print("=" * 60)
    print("V4 Output Validation")
    print("=" * 60)
    
    results_dir = Path('results/v4_test')
    tables_dir = Path('manuscript/supplementary_tables')
    figures_dir = Path('figures/v4_test')
    
    if not results_dir.exists():
        print(f"\n✗ Error: Results directory not found: {results_dir}")
        return 1
    
    try:
        # Validate components
        _output_validation = validate_analysis_outputs(results_dir)
        _table_validation = validate_tables(tables_dir)
        _figure_validation = validate_figures(figures_dir)
        
        # Generate report
        report = generate_validation_report(results_dir, tables_dir, figures_dir)
        
        print("\n" + "=" * 60)
        print("✓ Validation Complete!")
        print("=" * 60)
        
        # Summary
        print("\nValidation Summary:")
        print(f"  - Overall Status: {report['validation_results']['overall_status'].upper()}")
        print(f"  - Output Completeness: {report['validation_results']['output_completeness']['percentage']:.1f}%")
        print(f"  - Publication Readiness: {report['validation_results']['publication_readiness']['percentage']:.1f}%")
        
        if report['validation_results']['recommendations']:
            print("\nRecommendations:")
            for rec in report['validation_results']['recommendations']:
                print(f"  • {rec}")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
