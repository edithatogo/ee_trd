# Feature Audit Report - Baseline for nextgen_v3

This document inventories all discovered features in the existing repository to ensure nextgen_v3 preserves and augments them without loss.

## Feature Inventory

### Entry Points

- **Makefile Targets**:
  - `smoke_oral_ketamine`: Runs smoke test pipeline for oral ketamine, generating PSA, CE planes, and OWSA tornado.
  - `ce_plane_societal` / `ce_plane_health_system`: Generate cost-effectiveness planes for societal/health_system perspectives.
  - `tornado_owsa_societal` / `tornado_owsa_health_system`: Generate OWSA tornado diagrams.
  - `verify_v2`: Runs verification pipeline including cohesion checks, reconciliation, and publication readiness.
  - `ci_v2`: Runs pre-commit checks on verification scripts.

- **Snakefile Rules** (Snakemake pipeline):
  - `all`: Depends on PSA results, CEAC plots, DSA/BIA results for AU/NZ.
  - `run_cea`: Runs CEA model.
  - `run_psa_au` / `run_psa_nz`: Runs PSA for AU/NZ.
  - `run_dsa_au` / `run_dsa_nz`: Runs DSA for AU/NZ.
  - `run_bia_au` / `run_bia_nz`: Runs BIA for AU/NZ.
  - `analysis_v2_pipeline`: Runs full analysis_v2 pipeline.

- **Python CLI Scripts** (with argparse):
  - `scripts/audit_and_extend_psa.py`: Audits and extends PSA draws.
  - `scripts/autofix_common_issues.py`: Fixes common issues.
  - `scripts/ce_plane_psa_draws.py`: Creates CE plane from PSA draws.
  - `scripts/ceac_psa_draws.py`: Generates CEAC from PSA results.
  - `scripts/ceaf_psa_draws.py`: Generates CEAF from PSA results.
  - `scripts/check_param_cohesion.py`: Checks parameter cohesion.
  - `scripts/check_publication_readiness.py`: Checks publication readiness.
  - `scripts/fetch_new_evidence.py`: Fetches new evidence for therapies.
  - `scripts/make_price_prob_curves.py`: Generates price-probability curves.
  - `scripts/owsa_psa_model.py`: Deterministic stub model for OWSA.
  - `scripts/reconcile_v1_v2.py`: Reconciles v1 vs v2 outputs.
  - `scripts/summarize_psilocybin_ce_plane.py`: Summarizes psilocybin CE plane.
  - `scripts/threshold_price_curves.py`: Generates threshold price curves.
  - `scripts/verify_v2_cohesion.py`: Verifies v2 cohesion.
  - `analysis_v2/make_bia.py`: Makes BIA artifacts.
  - `analysis_v2/make_ce_plane.py`: Makes CE plane plots.
  - `analysis_v2/make_ceaf.py`: Computes CEAF curves.
  - `analysis_v2/make_price_prob_curves.py`: Generates price-probability curves.
  - `analysis_v2/make_tornado_owsa.py`: Runs OWSA tornado.
  - `analysis_v2/make_tornado_prcc.py`: Makes probabilistic tornado via PRCC.
  - `analysis_v2/make_vbp_curve.py`: Computes VBP curves.
  - `analysis_v2/run_pipeline.py`: Runs full analysis_v2 pipeline.

- **Other Scripts** (non-CLI or legacy):
  - Numerous scripts in `scripts/` for CEA, PSA, DSA, BIA, EVPI/EVPPI/EVSI, scenario/subgroup analysis, tornado plots, etc.

- **Notebooks**:
  - `scripts/analysis.ipynb`: Jupyter notebook for analysis.

### Plots and Visualizations

- **Plot Types** (PNG files in `figures/`):
  - Cost-effectiveness planes (ce_plane_*.png): Individual and combined for therapies (ketamine, esketamine, psilocybin), countries (AU/NZ), perspectives (healthcare/societal).
  - CEAC curves (ceac_*.png): Cost-effectiveness acceptability curves.
  - CEAF curves (ceaf_*.png): Cost-effectiveness acceptability frontiers.
  - Budget impact curves (budget_impact_curves_*.png).
  - EVPI/EVPPI curves (evpi_*.png, evppi_*.png).
  - Threshold price curves (threshold_price_*.png).
  - Tornado diagrams (tornado_diagrams_*.png).
  - Perspective comparisons (perspective_comparison_*.png).
  - Scenario/subgroup analyses (scenario_analysis_*.png, subgroup_analysis_*.png).
  - Two-way DSA (two_way_dsa_*.png).
  - PRISMA flow (prisma_flow.png/svg).

- **Outputs**: All plots are generated to `figures/` or `results/` subdirs.

### Data and Outputs

- **Input Data** (`data/`):
  - `clinical_inputs.csv`: Clinical parameters.
  - `cost_inputs_au.csv` / `cost_inputs_nz.csv`: Cost inputs for AU/NZ.
  - `dsa_inputs.csv`: DSA inputs.
  - `parameters_psa.csv`: PSA parameters.
  - `psa.csv`, `psa_extended.csv`, `psa_extended_hs.csv`, etc.: PSA draws and extensions.
  - `parameter_snapshot.json`: Parameter snapshots.

- **Output Data**:
  - PSA results (psa_results_*.csv).
  - DSA results (dsa_results_*.csv).
  - BIA results (bia_results_*.csv).
  - Tables for manuscript (`tables_for_manuscript/`).
  - Results in `results/` (e.g., reconciliation reports).

- **Config Formats** (`config/`):
  - YAML files: `analysis_v2_defaults.yml`, `bia.yaml`, `strategies.yml`.

### Tests

- **Test Files** (`tests/`):
  - `test_audit_and_extend_psa.py`
  - `test_ce_plane_deltas.py`
  - `test_fetch_new_evidence.py`
  - `test_oral_ketamine_smoke.py`
  - `test_planes_tornado_bia_smoke.py`
  - `conftest.py`: Pytest configuration.

## Hidden/Implicit Features

### Flags and Options

- Extensive CLI flags across scripts (e.g., --psa, --strategies-yaml, --perspective, --lambda, --outdir, --seed, --top, etc.).
- Perspectives: health_system, societal.
- Therapies: Oral ketamine, Esketamine, Ketamine, Psilocybin, Usual care (base).
- Countries: AU, NZ.

### Environment Variables

- `BIO_ENTREZ_EMAIL`: Required for NCBI Entrez API in `fetch_new_evidence.py`.
- `BIO_ENTREZ_API_KEY`: Optional for NCBI Entrez API.

### Internal Modules

- `utils.py`: Utility functions (e.g., set_seed).
- `analysis_core/`: Core analysis modules (deltas.py, export.py, grids.py, io.py, nmb.py, plotting.py).
- Internal dependencies: analysis_v2/ imports from analysis_core/, scripts import from both.

## Data/Plot Naming Patterns

- **Plots**: `{plot_type}_{therapy}_{country}_{perspective}.png` (e.g., `ce_plane_ketamine_AU_healthcare.png`).
- **Data**: `{type}_{variant}.csv` (e.g., `psa_extended_hs.csv` for health_system perspective).
- **Results**: `{analysis}_{country}_{perspective}.csv` (e.g., `psa_results_AU_healthcare.csv`).

## Dependency Graph

- **External Dependencies** (requirements.txt):
  - pandas, numpy, matplotlib, pyyaml, biopython, requests.

- **Internal Dependencies**:
  - `analysis_core/` modules: Independent, provide core functions (IO, plotting, NMB calculations).
  - `analysis_v2/` modules: Depend on `analysis_core/`, `utils.py`, and external libs.
  - `scripts/`: Depend on `analysis_core/`, `analysis_v2/`, `utils.py`, and external libs.
  - `tests/`: Depend on project modules and pytest.

This baseline ensures nextgen_v3 retains all treatments, perspectives, DCEA, CEAC/CEAF, pricing plots, and features. Any additions must augment without dropping.
</content>
<parameter name="filePath">/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/nextgen_v3/FEATURE_AUDIT.md