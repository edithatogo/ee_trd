# V3 NextGen - Equity Framework with Publication Enhancements

## Overview

V3 represents the NextGen Equity Framework, introducing distributional cost-effectiveness analysis and publication-ready outputs while maintaining all V2 capabilities.

## Key Features

### Enhanced Analysis Capabilities
All V2 capabilities PLUS:
- **Distributional CEA (DCEA)**: Social welfare function integration, Atkinson index, EDE-QALYs
- **Equity Analysis**: Distributional impact assessment, equity-weighted acceptability
- **Advanced VOI**: EVSI analysis, research prioritization
- **MCDA**: Multi-criteria decision analysis
- **Performance Optimization**: Parallel processing, memory optimization, benchmarking

### Publication Enhancements
- **300 DPI Output**: Journal-quality resolution
- **Professional Styling**: Publication-ready formatting
- **Therapy-Specific Naming**: IV-KA, IN-EKA, PO-KA, PO-PSI nomenclature
- **Optimized Scaling**: Focused WTP ranges (0-75k)
- **Comparison Dashboards**: Multi-panel visualization system

### Unique V3 Features
- Social welfare functions with inequality aversion
- Equity impact planes (efficiency vs equity trade-offs)
- Distributional CEAC curves
- RAC (Rank Acceptability Curves) with equity weights
- Data sourcing with provenance tracking
- Progress tracking and user feedback
- Performance monitoring and optimization

## Technical Architecture

### Core Components
- `nextgen_v3/cli/`: Command-line interfaces
  - `run_pipeline.py`: Enhanced pipeline orchestrator
  - `run_cea.py`: Cost-effectiveness analysis
  - `run_psa.py`: Probabilistic sensitivity analysis
  - `run_dcea.py`: Distributional CEA
  - `run_dsa.py`: Deterministic sensitivity analysis
  - `run_bia.py`: Budget impact analysis
  - `run_mcda.py`: Multi-criteria decision analysis
  - `run_evi.py`: Value of information

- `nextgen_v3/model/`: Analysis engines
  - `cea_engine.py`: CEA calculations
  - `psa.py`: PSA framework
  - `dcea.py`: Distributional analysis
  - `value_of_info.py`: VOI calculations
  - `mcda.py`: MCDA framework

- `nextgen_v3/plots/`: Visualization framework
  - `equity.py`: Equity analysis plots
  - `comparison_plots.py`: Multi-panel dashboards
  - `publication_style.py`: Journal formatting

- `nextgen_v3/utils/`: Utilities
  - `performance.py`: Performance optimization
  - `progress.py`: Progress tracking

## Equity Analysis Outputs

### Figures
- Equity impact planes
- Distributional CEAC curves
- Social welfare curves
- RAC curves
- Inequality plots

### Tables
- EDE-QALY results
- Atkinson indices
- Distributional summaries
- Equity rankings
- Social welfare metrics

## Purpose and Role

V3 introduced equity considerations and publication standards to the health economic evaluation framework. It demonstrated:
- How to incorporate distributional concerns into CEA
- Publication-quality output generation
- Advanced visualization techniques
- Performance optimization for large-scale analyses

## Relationship to V4

V4 incorporates V3's equity framework while adding:
- Indigenous population DCEA (Aboriginal, Māori, Pacific Islander)
- Semi-Markov model structure
- Bayesian network meta-analysis
- Step-care pathway analysis
- 3D sensitivity analysis
- Additional therapies and comparators

V3's equity analysis and publication standards form the foundation for V4's comprehensive framework.

## Key Achievements

### Corrected Implementation
V3 underwent significant correction to ensure it used actual data and calculations rather than placeholder values. The corrected V3 demonstrated:
- Consistency with V2 validated findings
- Real economic calculations
- Publication-ready analysis
- Robust equity framework

### Documentation
- Complete user guide
- Integration tests
- Performance benchmarking
- Comprehensive feature documentation

## Archive Contents

This directory contains:
- Complete V3 source code (`nextgen_v3/`)
- Configuration files and data schemas
- Analysis results and outputs
- Equity analysis results
- Publication-quality figures
- V3-specific documentation
- Correction reports and validation
