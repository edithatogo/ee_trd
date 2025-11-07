# AI Coding Assistant Instructions for Ketamine vs ECT Health Economic Evaluation

## Project Overview
This is a health economic evaluation toolkit comparing psychedelic therapies (ketamine, psilocybin) against electroconvulsive therapy (ECT) for treatment-resistant depression. The codebase evolved through 4 major versions (V1-V4), with V4 being the current canonical implementation featuring semi-Markov modeling, Bayesian network meta-analysis integration, and comprehensive equity analysis.

## Architecture & Data Flow

### Core Analysis Framework (`analysis/`)
- **`core/`**: Utilities for I/O, NMB calculations, parameter grids, and base plotting
- **`engines/`**: Analysis implementations (CEA, PSA, DSA, BIA, DCEA, VOI, MCDA)
- **`plotting/`**: Publication-quality visualizations with journal standards
- **`pipeline/`**: Workflow orchestration and validation

### Key Data Structures
- **PSA Data**: Probabilistic sensitivity analysis draws with columns `{draw, strategy, cost, effect, perspective}`
- **Strategies**: 10 treatment options defined in `config/strategies.yml` (ECT, KA-ECT, IV-KA, IN-EKA, PO-PSI, PO-KA, rTMS, UC+Li, UC+AA, Usual Care)
- **Perspectives**: `health_system` (healthcare payer) vs `societal` (broader economic impact)
- **Jurisdictions**: Australia (AU) and New Zealand (NZ) with jurisdiction-specific pricing

### Version Management
- **V4**: Current canonical version in `analysis/` and `scripts/`
- **V1-V3**: Archived in `archive/` with orchestration system in `orchestration/`
- **Parity System**: Feature tracking across versions in `parity/`

## Critical Developer Workflows

### Build & Test Commands
```bash
# Quick smoke test for oral ketamine analysis
make smoke_oral_ketamine

# Run minimal smoke pipeline
make smoke-min

# Full V4 pipeline for both jurisdictions
python scripts/run_v4_pipeline.py --jur both --perspectives health_system societal

# Run specific analysis modules
python scripts/run_cua.py --jur AU --perspective health_system
python scripts/run_dcea.py --jur AU --include-indigenous
python scripts/run_voi.py --jur AU

# Test suite
pytest tests/ --cov=analysis_core --cov=scripts --cov=analysis_v2
```

### Workflow Orchestration
- **Makefile**: Primary build system with version-specific targets (`v3-pipeline`, `v4-pipeline`)
- **Snakemake**: Declarative workflow in `Snakefile` for dependency management
- **Orchestration**: Cross-version execution via `orchestration/run_all_versions.py`

### Environment Setup
```bash
# Virtual environment (Python 3.10+)
python3.10 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# NCBI API for evidence fetching
export NCBI_EMAIL="your.name@example.com"
```

## Project-Specific Conventions

### Therapy Abbreviations & Naming
Always use manuscript abbreviations:
- `ECT`: Standard Electroconvulsive Therapy
- `KA-ECT`: Ketamine-Assisted ECT
- `IV-KA`: Intravenous Ketamine
- `IN-EKA`: Intranasal Esketamine
- `PO-PSI`: Oral Psilocybin-Assisted Therapy
- `PO-KA`: Oral Ketamine
- `rTMS`: Repetitive Transcranial Magnetic Stimulation
- `UC+Li`: Usual Care + Lithium Augmentation
- `UC+AA`: Usual Care + Atypical Antipsychotic

### Configuration Patterns
- **Strategy Config**: `config/strategies.yml` defines therapies, prices, perspectives
- **Analysis Defaults**: `config/v4_analysis_defaults.yml` for V4 parameters
- **Journal Standards**: `config/journal_standards.yml` for publication formatting

### Data Organization
- **Input Data**: `data/` with jurisdiction-specific CSVs (clinical_inputs.csv, cost_inputs_au.csv, cost_inputs_nz.csv)
- **PSA Data**: Multiple versions (psa.csv, psa_extended.csv, psa_nma_integrated.csv) with different coverage
- **Results**: `results/` with dated subdirectories for reproducibility

### Step-Care Pathways
Complex treatment sequences defined in `config/strategies.yml`:
```yaml
step_care_sequences:
  "Step-care: Pharm → rTMS → IV-KA → ECT":
    - "Usual care"
    - "rTMS"
    - "IV-KA"
    - "ECT"
```

## Integration Points & Dependencies

### External APIs
- **NCBI E-utilities**: Evidence fetching via `scripts/fetch_new_evidence.py`
- **Publication Standards**: Compliance with ANZJP formatting requirements

### Cross-Component Communication
- **Parameter Auditing**: `scripts/audit_and_extend_psa.py` validates parameter consistency
- **Version Reconciliation**: `scripts/reconcile_v1_v2.py` ensures numerical consistency across versions
- **Parity Checking**: `parity/` system tracks feature implementation across versions

### Quality Assurance
- **Pre-commit Hooks**: Code quality via `.pre-commit-config.yaml`
- **Publication Readiness**: `scripts/check_publication_readiness.py` validates outputs
- **Parameter Cohesion**: `scripts/check_param_cohesion.py` ensures consistency

## Common Patterns & Anti-Patterns

### DO Use:
- **Dataclasses** for configuration structures (see `analysis/core/io.py`)
- **Pathlib** for file operations (never use `os.path`)
- **YAML** for configuration (not JSON for human-editable configs)
- **Pandas** for data manipulation with explicit dtypes
- **Type hints** throughout (PEP 484 compliance)

### DON'T Use:
- **Seaborn**: Explicitly forbidden (see `scripts/check_no_seaborn.py`)
- **Hardcoded paths**: Always use relative paths from project root
- **Bare exceptions**: Always catch specific exceptions
- **Global state**: Prefer functional composition over mutable globals

### Testing Patterns
```python
@pytest.mark.parametrize("jur,perspective", [
    ("AU", "health_system"),
    ("NZ", "societal")
])
def test_analysis_consistency(jur, perspective):
    # Test implementation
```

### Plotting Standards
- **300 DPI** minimum resolution
- **Publication colors**: Consistent color schemes across all figures
- **Journal compliance**: ANZJP formatting standards
- **Figure inventory**: `scripts/create_figure_inventory.py` tracks all outputs

## Debugging & Development

### Common Issues
- **Jurisdiction mismatches**: Ensure AU/NZ data alignment
- **Perspective confusion**: health_system excludes productivity costs
- **Parameter drift**: Run `make check_param_cohesion` after changes
- **Version conflicts**: Use orchestration system for cross-version testing

### Performance Optimization
- **Profiling**: `python -m cProfile scripts/run_v4_analysis.py`
- **Memory monitoring**: Built into `analysis/core/performance.py`
- **Parallel execution**: Snakemake handles dependency-based parallelism

## Key Files for Understanding
- `README.md`: High-level overview and quick start
- `analysis/README.md`: V4 framework architecture
- `config/strategies.yml`: Therapy definitions and pricing
- `Makefile`: Primary development workflows
- `orchestration/VERSIONS_MANIFEST.json`: Version management
- `scripts/audit_and_extend_psa.py`: Parameter validation patterns</content>
<parameter name="filePath">/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/.github/copilot-instructions.md