# TRD CEA Toolkit: Health Economic Evaluation Tools

This repository contains a comprehensive toolkit for conducting health economic evaluations 
comparing psychedelic therapies and other interventions for treatment-resistant depression (TRD).

## Overview

The TRD CEA Toolkit provides:

- **Cost-Effectiveness Analysis (CEA)**: Traditional and distributional CEA
- **Value of Information (VOI)**: EVPI, EVPPI, and EVSI analysis  
- **Budget Impact Analysis (BIA)**: Multi-year budget projections
- **Multiple Criteria Decision Analysis (MCDA)**: Multi-attribute utility modeling
- **Sensitivity Analysis**: One-way, multi-way, and probabilistic sensitivity analysis
- **Implementation Modeling**: Capacity constraints and implementation costs
- **Equity Analysis**: Distributional cost-effectiveness with population subgroups

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/trd-cea-toolkit.git
cd trd-cea-toolkit

# Create conda environment (recommended)
conda env create -f environment.yml
conda activate trd-cea

# Or create environment manually
conda create -n trd-cea python=3.10
conda activate trd-cea
pip install -r requirements.txt

# Install as package in development mode
pip install -e .
```

## Usage

### Quick Start with Jupyter Notebooks

The easiest way to get started is using the example notebooks in the `analysis/` directory:

```bash
# Activate environment
conda activate trd-cea

# Launch Jupyter Lab
jupyter lab
```

Then navigate to the example notebooks in `analysis/cea/`, `analysis/dcea/`, etc.

### Command Line Interface

The toolkit includes a command-line interface:

```bash
# Run CEA analysis
trd-cea-analyze cea --config config/analysis_config.yaml

# Run Budget Impact Analysis
trd-cea-analyze bia --config config/bia_config.yaml

# Run Value of Information analysis
trd-cea-analyze voi --config config/voi_config.yaml --type evpi
```

### Programmatic Usage

```python
from src.trd_cea.analysis import run_analysis_pipeline

# Run analysis from configuration
results = run_analysis_pipeline(
    config_path="config/analysis_config.yaml",
    analysis_type="cea"
)
```

### Analysis Types

The toolkit provides implementations for:

- **CEA**: Cost-effectiveness analysis with ICERs and NMB calculations
- **DCEA**: Distributional CEA incorporating equity considerations
- **VOI**: Value of information analysis (EVPI, EVPPI, EVSI)
- **BIA**: Budget impact analysis with multi-year projections
- **MCDA**: Multi-criteria decision analysis
- **PSA**: Probabilistic sensitivity analysis
- **DSA**: Deterministic sensitivity analysis (one-way and multi-way)
- **VBP**: Value-based pricing calculations
- **Headroom**: Headroom and pricing threshold analysis
- **Subgroup**: Subgroup analysis by demographics/clinical characteristics
- **Scenario**: Scenario analysis for different assumptions
- **Capacity**: Capacity constraints and implementation modeling
- **Policy**: Policy realism and implementation feasibility assessment

## Project Structure

```
trd-cea-analysis/
├── analysis/                 # Jupyter notebooks by analysis type
│   ├── cea/                  # Cost-effectiveness analysis examples
│   ├── dcea/                 # Distributional CEA examples  
│   ├── voi/                  # Value of information examples
│   ├── bia/                  # Budget impact analysis examples
│   └── ...                   # Other analysis types
├── src/trd_cea/              # Python package source
│   ├── core/                 # Core utilities and configuration
│   ├── models/               # Analysis engine implementations
│   ├── analysis/             # Analysis execution functions
│   ├── plotting/             # Visualization and plotting utilities
│   └── utils/                # General utility functions
├── config/                   # Configuration files
├── data/                     # Data schemas and sample data structures
├── docs/                     # Documentation
├── tests/                    # Test suite
├── reports/                  # Project reports and documentation
├── development/              # Development tools and configuration
├── archives/                 # Archive files and backups
├── environment.yml           # Conda environment specification
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Python package metadata
├── setup.py                  # Package setup script
├── scripts/                  # Additional scripts (orchestration, etc.)
├── README.md                 # This file
└── LICENSE                   # License information
```

## Configuration

All analyses are configurable through YAML files in the `config/` directory. This separates configuration from code, allowing for reproducible analyses with different parameter sets.

## Contributing

We welcome contributions! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for details.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this toolkit in your research, please consider citing:

Dylan A Mordaunt (2025). TRD CEA Toolkit: Health Economic Evaluation Tools. 
Available at https://github.com/edithatogo/ee_trd