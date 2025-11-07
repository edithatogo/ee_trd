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
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# Or install as package
pip install .
```

## Usage

### Running Analyses

Basic CEA analysis:
```python
from scripts.models.cea_engine import CEAEngine

cea = CEAEngine()
results = cea.run_analysis(
    strategies=['ECT', 'IV-KA', 'PO-KA'],
    costs=[5000, 7500, 6000], 
    effects=[0.6, 0.8, 0.7],
    wtp_threshold=50000
)
```

### Analysis Types

The toolkit supports multiple analysis types organized in the `analysis/` directory:

- `analysis/cea/` - Cost-effectiveness analysis
- `analysis/dcea/` - Distributional CEA with equity considerations  
- `analysis/voi/` - Value of information analysis
- `analysis/bia/` - Budget impact analysis
- `analysis/mcda/` - Multi-criteria decision analysis
- `analysis/psa/` - Probabilistic sensitivity analysis
- `analysis/dsa/` - Deterministic sensitivity analysis
- `analysis/nma/` - Network meta-analysis integration
- And more specialized analyses...

### Example Notebooks

Jupyter notebooks demonstrating each analysis type are available in the respective analysis directories.

## Project Structure

```
trd-cea-toolkit/
├── analysis/                 # Jupyter notebooks by analysis type
│   ├── cea/                  # Cost-effectiveness analysis examples
│   ├── dcea/                 # Distributional CEA examples  
│   ├── voi/                  # Value of information examples
│   └── ...                   # Other analysis types
├── scripts/                  # Core Python functionality
│   ├── core/                 # Fundamental utilities
│   ├── models/               # Analysis engines and models
│   ├── analysis/             # Analysis execution scripts  
│   └── plotting/             # Visualization utilities
├── config/                   # Configuration files
├── data/                     # Data schemas and structures
├── docs/                     # Documentation
├── tests/                    # Test suite
├── results/                  # Example results
├── requirements.txt          # Dependencies
├── pyproject.toml           # Package configuration
└── README.md                # This file
```

## Contributing

We welcome contributions! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this toolkit in your research, please consider citing:

[To be updated with actual citation when published]
