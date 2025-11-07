# nextgen_v3

Next generation framework for ketamine vs ECT analysis.

## Overview

This is the v3 version, standing alone without legacy imports.

## What's New

- Retained all arms: ECT_std, ECT_ket_anaesthetic, IV_ketamine, Esketamine, Psilocybin, Oral_ketamine.
- Added CEAF (Cost-Effectiveness Acceptability Frontier).
- Pricing plots with threshold prices and PSA bands.
- DCEA visuals: equity impact planes, distributional CEAC, RAC.
- Subgroup sourcing with provenance tracking (CSL-JSON/BibTeX/DOI ingestion).

## Structure

- config/: Configuration files
- data_schemas/: CSV schemas with headers
- sourcing/: Data harvesting scripts
- io/: Loaders and validators
- model/: Analysis engines
- plots/: Plotting scripts
- cli/: Command-line interfaces
- notebooks/: Jupyter notebooks
- pipelines/: Makefiles and Snakefiles
- tests/: Unit tests

## How to Run

### CLIs

- `python nextgen_v3/cli/run_sourcing.py --costs-au path/to/costs.csv`
- `python nextgen_v3/cli/run_cea.py --jur AU --perspective health_system`
- `python nextgen_v3/cli/run_psa.py`
- `python nextgen_v3/cli/run_dsa.py`
- `python nextgen_v3/cli/run_dcea.py`
- `python nextgen_v3/cli/run_bia.py --jur AU`

### Pipelines

- `make -f nextgen_v3/pipelines/Makefile v3-all`
- `snakemake -s nextgen_v3/pipelines/Snakefile v3_all`

## Outputs Catalog

All outputs in nextgen_v3/out/{DATE}/:

- cea_results_by_arm_v3.csv: CEA results per arm/jur/perspective
- incremental_vs_ECT_std_v3.csv: Incremental costs/QALYs/ICER
- psa_results_v3.csv: PSA iterations
- ceac_v3.csv/png: CEAC curves
- ceaf_v3.csv/png: CEAF curves
- icer_scatter_v3.png: Incremental scatter
- tornado_v3.png: DSA tornado
- bia_summary_{jur}_v3.csv: BIA summaries
- dcea_by_group_v3.csv: Group-level DCEA
- dcea_edeqaly_v3.csv: EDE-QALYs
- dcea_weighted_inb_v3.csv: Weighted INB
- pricing_v3.png: Threshold pricing
- equity_impact_v3.png: Equity impact plane
- distributional_ceac_v3.png: Distributional CEAC
- rac_v3.png: RAC

## TODO: Missing Features from Legacy Audit

The following features from the legacy system (v1/v2) are not yet implemented in v3. They must be added to ensure no regression. Each is mapped to potential v3 location.

### Entry Points
- **Makefile Targets**: `smoke_oral_ketamine`, `ce_plane_*`, `tornado_*`, `verify_v2`, `ci_v2` → TODO in `pipelines/Makefile`
- **Snakefile Rules**: `all`, `run_cea`, `run_psa_*`, `run_dsa_*`, `run_bia_*`, `analysis_v2_pipeline` → TODO in `pipelines/Snakefile`
- **Python CLI Scripts**:
  - `scripts/audit_and_extend_psa.py` → TODO in `cli/audit_psa.py`
  - `scripts/autofix_common_issues.py` → TODO in `cli/autofix.py`
  - `scripts/ce_plane_psa_draws.py` → TODO in `plots/ce_plane.py`
  - `scripts/ceac_psa_draws.py` → TODO in `plots/ceac.py`
  - `scripts/ceaf_psa_draws.py` → TODO in `plots/ceaf.py`
  - `scripts/check_param_cohesion.py` → TODO in `cli/check_cohesion.py`
  - `scripts/check_publication_readiness.py` → TODO in `cli/publication_readiness.py`
  - `scripts/fetch_new_evidence.py` → TODO in `sourcing/fetch_evidence.py`
  - `scripts/make_price_prob_curves.py` → TODO in `plots/price_prob.py`
  - `scripts/owsa_psa_model.py` → TODO in `model/owsa.py`
  - `scripts/reconcile_v1_v2.py` → TODO in `scripts/reconcile.py`
  - `scripts/summarize_psilocybin_ce_plane.py` → TODO in `plots/summarize_psilo.py`
  - `scripts/threshold_price_curves.py` → TODO in `plots/threshold_price.py`
  - `scripts/verify_v2_cohesion.py` → TODO in `cli/verify_cohesion.py`
  - `analysis_v2/make_bia.py` → TODO in `model/bia_engine.py` (extend stub)
  - `analysis_v2/make_ce_plane.py` → TODO in `plots/ce_plane.py`
  - `analysis_v2/make_ceaf.py` → TODO in `plots/ceaf.py`
  - `analysis_v2/make_price_prob_curves.py` → TODO in `plots/price_prob.py`
  - `analysis_v2/make_tornado_owsa.py` → TODO in `plots/tornado_owsa.py`
  - `analysis_v2/make_tornado_prcc.py` → TODO in `plots/tornado_prcc.py`
  - `analysis_v2/make_vbp_curve.py` → TODO in `plots/vbp.py`
  - `analysis_v2/run_pipeline.py` → TODO in `cli/run_pipeline.py`

### Plots and Visualizations
- **Budget Impact Curves**: `budget_impact_curves_*.png` → TODO in `plots/budget_impact.py`
- **EVPI/EVPPI Curves**: `evpi_*.png`, `evppi_*.png` → TODO in `plots/evpi_evppi.py`
- **Perspective Comparisons**: `perspective_comparison_*.png` → TODO in `plots/perspective_comparison.py`
- **Scenario/Subgroup Analyses**: `scenario_analysis_*.png`, `subgroup_analysis_*.png` → TODO in `plots/scenario_subgroup.py`
- **Two-way DSA**: `two_way_dsa_*.png` → TODO in `plots/two_way_dsa.py`
- **PRISMA Flow**: `prisma_flow.png/svg` → TODO in `plots/prisma.py`

### Data and Outputs
- **Parameter Snapshot**: `parameter_snapshot.json` → TODO in `io/snapshot.py`
- **Tables for Manuscript**: `tables_for_manuscript/` → TODO in `export/tables.py`
- **Reconciliation Reports**: `results/reconciliation_*.csv` → TODO in `scripts/reconcile.py`

### Tests
- **Additional Test Files**: `test_audit_and_extend_psa.py`, `test_ce_plane_deltas.py`, `test_fetch_new_evidence.py`, `test_oral_ketamine_smoke.py`, `test_planes_tornado_bia_smoke.py` → TODO in `tests/`

### Hidden/Implicit Features
- **Environment Variables**: `BIO_ENTREZ_EMAIL`, `BIO_ENTREZ_API_KEY` → TODO in `config/env.py`
- **Internal Modules**: `analysis_core/` (deltas.py, export.py, grids.py, io.py, nmb.py, plotting.py) → TODO in `model/analysis_core/`
- **Notebooks**: `scripts/analysis.ipynb` → TODO extend `notebooks/analysis_v3.ipynb`

### Dependencies
- **Additional Libraries**: `biopython`, `requests` → TODO add to `requirements.txt`
