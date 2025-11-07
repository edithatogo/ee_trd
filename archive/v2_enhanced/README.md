# V2 Enhanced - Comprehensive Analysis Framework

## Overview

V2 represents a major enhancement of the health economic evaluation, providing comprehensive analysis capabilities and a robust framework for comparing multiple psychedelic therapies against ECT.

## Key Features

### Analysis Capabilities
- **Cost-Effectiveness Analysis**: Deterministic and probabilistic CEA with full incremental analysis
- **Sensitivity Analysis**: One-way DSA, two-way DSA, tornado diagrams (OWSA and PRCC)
- **Acceptability Analysis**: CEAC curves, CEAF curves, probability rankings
- **Value of Information**: EVPI and EVPPI analysis
- **Budget Impact Analysis**: Multi-year BIA with market share modeling
- **Pricing Analysis**: Threshold pricing, value-based pricing, price-probability curves
- **Subgroup Analysis**: Age, gender, severity stratification
- **Scenario Analysis**: Alternative scenario comparisons

### Therapies Covered
- ECT (Standard Electroconvulsive Therapy)
- KA-ECT (Ketamine-Assisted ECT)
- IV-KA (Intravenous Ketamine)
- IN-EKA (Intranasal Esketamine)
- PO-PSI (Oral Psilocybin)
- PO-KA (Oral Ketamine)
- Usual Care

### Geographic Coverage
- Australia (AU)
- New Zealand (NZ)

### Economic Perspectives
- Health System perspective
- Societal perspective

## Technical Architecture

### Core Components
- `analysis_v2/`: Main analysis modules
  - `run_pipeline.py`: Pipeline orchestration
  - `make_ceaf.py`: CEAF analysis
  - `make_ce_plane.py`: CE plane generation
  - `make_bia.py`: Budget impact analysis
  - `make_tornado_owsa.py`: Tornado diagrams
  - `make_tornado_prcc.py`: PRCC analysis
  - `make_vbp_curve.py`: Value-based pricing
  - `make_price_prob_curves.py`: Price-probability analysis
  - `make_evpi.py`: Value of information
  - `make_comparison_plots.py`: Comparison visualizations

- `analysis_core/`: Core utilities
  - `io.py`: Data loading and export
  - `nmb.py`: Net monetary benefit calculations
  - `deltas.py`: Incremental analysis
  - `grids.py`: Parameter grid generation
  - `plotting.py`: Base plotting utilities
  - `export.py`: Publication-ready formatting

## Outputs Generated

### Figures (47 types)
- CE planes for all therapies and jurisdictions
- CEAC/CEAF curves
- Budget impact visualizations
- EVPI/EVPPI curves
- Tornado diagrams
- Threshold pricing curves
- Subgroup analysis plots
- Scenario comparison plots
- Perspective comparisons
- Two-way DSA heatmaps
- PRISMA flow diagrams

### Tables (25 types)
- PSA results by jurisdiction and perspective
- BIA summaries
- EVPI/EVPPI values
- Threshold analysis
- DSA results
- Scenario and subgroup analyses

## Purpose and Role

V2 established the comprehensive analysis framework that became the standard for health economic evaluation in this project. It provided:
- Proven, validated analysis capabilities
- Robust pipeline orchestration
- Publication-quality outputs
- Multi-perspective and multi-jurisdiction analysis

## Relationship to V4

V4 consolidates V2's comprehensive analysis capabilities while adding:
- Equity analysis (DCEA)
- Indigenous population analysis
- Advanced model features (semi-Markov, NMA)
- Enhanced publication standards
- Additional therapies (rTMS, augmentation strategies)

V2's analysis modules serve as the foundation for V4's unified analysis framework.

## Archive Contents

This directory contains:
- Complete V2 source code (`analysis_v2/` and `analysis_core/`)
- Configuration files
- Analysis results and outputs
- Generated figures and tables
- V2-specific documentation
