# TRD CEA Toolkit - Setup and Usage Guide

This document provides instructions for setting up the repository for GitHub publication and using the health economic evaluation tools.

## Repository Transformation Complete

The repository has been successfully transformed from a complex, publication-focused codebase into a streamlined, professional data science toolkit for health economic evaluation. All analytical capabilities have been preserved while making it accessible and focused on the codebase rather than manuscript preparation.

## Repository Structure

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
│   └── plotting/             # Visualization utilities
├── config/                   # Configuration files
├── data/                     # Data schemas
├── docs/                     # Documentation
├── tests/                    # Comprehensive test suite
├── environment.yml           # Conda environment specification
├── requirements.txt          # Python dependencies
├── setup.py                 # Python package setup
├── pyproject.toml           # Modern Python packaging
├── README.md                # Project overview
└── LICENSE                  # Apache 2.0 License
```

## Setup Instructions

### 1. Local Development Environment

```bash
# Clone the repository (when available on GitHub)
git clone https://github.com/username/trd-cea-analysis.git
cd trd-cea-analysis

# Create conda environment
conda env create -f environment.yml
conda activate trd-cea

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install as editable package for development
pip install -e .
```

### 2. Running Analyses

#### Using Python API:
```python
from src.trd_cea.core.utils import calculate_icer, calculate_nmb
from src.trd_cea.analysis import run_analysis_pipeline

# Example calculation
icer = calculate_icer(cost_new=6000, cost_ref=5000, effect_new=0.75, effect_ref=0.65)
nmb = calculate_nmb(cost=5000, effect=0.65, wtp_threshold=50000)

# Run complete analysis pipeline
results = run_analysis_pipeline(
    config_path="config/analysis_defaults.yaml",
    analysis_type="cea"
)
```

#### Using Jupyter Notebooks:
- Navigate to the analysis directories (e.g., `analysis/cea/`)
- Open the example notebooks to see usage examples
- Each notebook demonstrates a different type of analysis

### 3. Configuration Management

All analyses are configured through YAML files in the `config/` directory:

```yaml
analysis:
  time_horizon: 10
  discount_rate_costs: 0.035
  discount_rate_effects: 0.035
  wtp_threshold: 50000

strategies:
  ECT:
    cost: 5000
    effect: 0.60
  IV-KA:
    cost: 7500
    effect: 0.75
  PO-KA:
    cost: 6000
    effect: 0.68
```

## Analysis Types Available

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
- **Markov**: Markov state-transition models with time-dependence
- **Time-to-Benefit**: Timing of therapeutic effects analysis
- **Adverse Events**: Side effect disutility incorporation

## Testing and Quality Assurance

Run the full test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test groups
python -m pytest tests/test_core_functionality.py -v
python -m pytest tests/test_quality_assurance.py -v
```

## Automated Documentation

The package includes:
- Comprehensive docstrings for all functions and classes
- Example notebooks for each analysis type
- Configuration schemas and validation
- Usage examples with parameter documentation
- Results interpretation guides

## Reproducibility Features

- Complete provenance tracking through logging
- Parameter versioning and audit trails
- Random seed management for reproducibility
- Execution environment documentation
- Configuration change tracking

## Performance Optimizations

- Intelligent caching for expensive computations
- Memory management for large datasets
- Asynchronous processing capabilities
- Progress tracking for long-running analyses
- Optimized numerical methods

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the full test suite
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## GitHub Publication Steps

To publish this repository to GitHub:

1. Create a new repository on GitHub
2. Update the remote origin:
   ```bash
   git remote set-url origin https://github.com/yourusername/your-repository-name.git
   ```
3. Push the main branch:
   ```bash
   git push -u origin main
   ```
4. Enable GitHub Actions in the repository settings
5. Set up any secrets for external data access if needed

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.