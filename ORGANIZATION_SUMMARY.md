# Repository Structure Summary: TRD CEA Data Science Tools

## Rationale for Changes

The repository has been reorganized from a complex publication-focused codebase to a streamlined data science toolkit. The main goals were:

1. **Focus on Analysis Tools**: Remove publication-specific components and focus on analytical functions
2. **Simplify for Data Scientists**: Use a structure familiar to data science practitioners
3. **Enable Reproducibility**: Clear execution paths and documentation for reproducible analysis
4. **Modular Design**: Separate concerns between models, analysis execution, utilities, and visualization

## Final Repository Structure

```
trd-cea-analysis/
├── analysis/                 # Jupyter notebooks organized by analysis type
│   ├── cea/                  # Cost-effectiveness analysis notebooks
│   ├── dcea/                 # Distributional CEA notebooks
│   ├── voi/                  # Value of information notebooks
│   └── bia/                  # Budget impact analysis notebooks
├── scripts/                  # Python scripts organized by function
│   ├── analysis/             # Analysis execution scripts and notebooks
│   ├── core/                 # Core utilities and configuration
│   ├── models/               # Model implementations (CEA, BIA, VOI, etc.)
│   └── plotting/             # Visualization utilities
├── config/                   # Configuration files
├── data/                     # Data schemas and sample data structures
│   ├── input_schemas/        # Input data structure definitions
│   └── output_schemas/       # Output data structure definitions
├── docs/                     # Documentation
├── results/                  # Example results directory (not tracked in Git)
├── run_analysis.py           # Main execution script
├── environment.yml           # Conda environment specification
├── requirements.txt          # Python dependencies
├── README.md                 # Project overview and usage
├── LICENSE                   # License information
├── .gitignore               # Git ignore rules for data science projects
└── utils.py                 # Common utilities
```

## Key Improvements

1. **Analysis-First Approach**: Jupyter notebooks provide interactive exploration
2. **Clear Separation**: Models, execution scripts, and utilities are separated
3. **Reproducible Workflows**: Clean execution path from data input to results
4. **Data Science Friendly**: Structure follows common data science project patterns
5. **Reduced Complexity**: Removed unnecessary publication and tracking systems

## Usage

To run a complete analysis:
```
python run_analysis.py all
```

To run a specific analysis:
```
python run_analysis.py cea
```

To run with a configuration file:
```
python run_analysis.py voi --config-file config/voi_params.yml
```

To run interactively with Jupyter notebooks:
```
jupyter lab
```

This structure makes it much easier for data scientists to:
- Understand the analysis components
- Reproduce the results
- Modify parameters and methodologies
- Extend the analysis with new methods
- Integrate with other data science tools