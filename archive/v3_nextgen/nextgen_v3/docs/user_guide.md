# V3 NextGen Equity Framework - User Guide

## Overview

The V3 NextGen Equity Framework is a comprehensive health economic analysis system that extends traditional cost-effectiveness analysis with distributional considerations and advanced comparison capabilities. V3 addresses all limitations of V2 while providing unique equity-focused features.

## Key Features

### ✨ **Enhanced Capabilities (vs V2)**
- ✅ **Complete therapy coverage**: All 5 therapies (IV-KA, IN-EKA, PO psilocybin, PO-KA, KA-ECT)
- ✅ **Publication-quality outputs**: 300 DPI, professional styling, proper formatting
- ✅ **Optimized scaling**: Focused WTP ranges (0-75k), proper axis limits
- ✅ **Therapy-specific naming**: Publication-ready labels (IV-KA vs generic names)
- ✅ **Advanced comparisons**: Side-by-side analysis with comparison plots
- ✅ **VOI analysis**: Expected Value of Perfect Information with equity weighting

### 🚀 **Unique V3 Features**
- 🎯 **Distributional CEA (DCEA)**: Social welfare function integration
- 📊 **Equity analysis**: Distributional impact assessment  
- 🔄 **Unified pipeline**: Single command for complete workflows
- ⚡ **Progress feedback**: Real-time status updates and timing estimates
- 🎨 **Comparison dashboards**: Multi-panel visualization system

## Installation & Setup

### Prerequisites
```bash
# Python 3.8+ with required packages
pip install -r requirements.txt

# Verify installation
python nextgen_v3/cli/run_cea.py --help
```

### Configuration
V3 uses `nextgen_v3/config/settings.yaml` for all configuration:

```yaml
# Core settings optimized for publication
therapies:
  iv_ketamine: { label: "IV-KA", color: "#1f77b4" }
  intranasal_esketamine: { label: "IN-EKA", color: "#ff7f0e" }
  psilocybin: { label: "PO psilocybin", color: "#2ca02c" }
  oral_ketamine: { label: "PO-KA", color: "#d62728" }
  ketamine_ect: { label: "KA-ECT", color: "#9467bd" }

wtp_grid: [0, 12500, 25000, 37500, 50000, 62500, 75000]  # Optimized range
```

## Quick Start

### 1. **Complete Pipeline (Recommended)**
Run the entire V3 workflow with a single command:

```bash
# Full pipeline - both jurisdictions and perspectives
python nextgen_v3/cli/run_pipeline.py

# Specific jurisdiction and perspective
python nextgen_v3/cli/run_pipeline.py --jur AU --perspectives health_system

# Skip time-intensive steps for quick testing
python nextgen_v3/cli/run_pipeline.py --skip-sourcing --skip-voi
```

### 2. **Individual Analyses**
Run specific analysis types:

```bash
# Cost-effectiveness analysis
python nextgen_v3/cli/run_cea.py --jur AU --perspective health_system

# Probabilistic sensitivity analysis  
python nextgen_v3/cli/run_psa.py

# Distributional cost-effectiveness analysis
python nextgen_v3/cli/run_dcea.py

# Budget impact analysis
python nextgen_v3/cli/run_bia.py --jur NZ
```

### 3. **Comparison & VOI Analysis**
Generate advanced comparison outputs:

```bash
# The pipeline automatically creates these, but you can also run:
python -c "
from nextgen_v3.plots.comparison_plots import create_comprehensive_v3_dashboard
create_comprehensive_v3_dashboard('data/psa_extended.csv', 'results/comparisons')
"

python -c "
from nextgen_v3.analysis.voi import run_comprehensive_voi_analysis  
run_comprehensive_voi_analysis('data/psa_extended.csv', 'results/voi')
"
```

## Pipeline Structure

### Workflow Overview
```
V3 Pipeline Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Data        │ -> │ Core        │ -> │ Advanced    │
│ Sourcing    │    │ Analyses    │    │ Features    │
└─────────────┘    └─────────────┘    └─────────────┘
│               │                │               │
├ Validation    ├ CEA            ├ Comparisons   │
├ Preparation   ├ PSA            ├ VOI Analysis  │
└ QA Checks     ├ DCEA           └ Publication   │
                ├ DSA                Outputs      │
                └ BIA                             │
```

### Output Structure
```
results/v3_pipeline_TIMESTAMP/
├── cea/                    # Cost-effectiveness results
├── psa/                    # Probabilistic sensitivity  
├── dcea/                   # Distributional analysis
├── dsa/                    # Deterministic sensitivity
├── bia/                    # Budget impact
├── comparisons/            # V3 comparison plots
│   ├── ceaf_comparison.png
│   ├── equity_dashboard.png
│   └── comprehensive_dashboard.png
└── voi/                    # Value of information
    ├── evpi_analysis.png
    ├── evpi_by_therapy.csv
    └── voi_summary.json
```

## Advanced Usage

### Custom Configuration
Create custom settings for specific analyses:

```python
# Custom V3 configuration
from nextgen_v3.config.settings import SETTINGS

# Override therapy selection
custom_therapies = ['iv_ketamine', 'intranasal_esketamine']
SETTINGS['analyses']['therapies'] = custom_therapies

# Custom WTP range for sensitivity testing
SETTINGS['analyses']['wtp_grid'] = [0, 25000, 50000, 100000]
```

### Batch Processing
Process multiple scenarios efficiently:

```bash
# Create batch script
cat > run_v3_batch.sh << 'EOF'
#!/bin/bash
for jur in AU NZ; do
  for perspective in health_system societal; do
    echo "Running V3 for $jur $perspective..."
    python nextgen_v3/cli/run_pipeline.py \
      --jur $jur \
      --perspectives $perspective \
      --output-dir "results/v3_${jur,,}_${perspective}"
  done
done
EOF

chmod +x run_v3_batch.sh
./run_v3_batch.sh
```

### Integration with Orchestration
V3 integrates seamlessly with the project's orchestration system:

```bash
# Run all versions (v1, v2, v3) for comparison
make orchestrate-plan  # Preview execution plan
make orchestrate-run   # Execute all versions

# V3-specific orchestration
python orchestration/run_all_versions.py --versions v3 --execute
```

## Comparison with V2

| Feature | V2 | V3 | Notes |
|---------|----|----|-------|
| **Therapy Coverage** | ❌ Missing therapies | ✅ All 5 therapies | Complete coverage |
| **Naming Convention** | ❌ Generic names | ✅ Publication format | IV-KA, IN-EKA, etc. |
| **Axis Scaling** | ❌ Wide ranges (0-300k) | ✅ Focused (0-75k) | Publication optimized |
| **Plot Quality** | ❌ Basic formatting | ✅ 300 DPI, professional | Publication ready |
| **Comparisons** | ❌ None | ✅ Multi-panel dashboards | Side-by-side analysis |
| **VOI Analysis** | ❌ Basic | ✅ Comprehensive EVPI | Advanced methodology |
| **Pipeline** | ✅ Available | ✅ Enhanced | V3 adds progress tracking |
| **Equity Framework** | ❌ None | ✅ DCEA integration | Unique V3 feature |

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure V3 is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/nextgen_v3"

# Or run from project root
cd /path/to/project
python nextgen_v3/cli/run_pipeline.py
```

**2. Memory Issues with Large PSAs**
```bash
# Use smaller batch sizes for PSA
python nextgen_v3/cli/run_psa.py --batch-size 100

# Or increase system memory limits
ulimit -m 8388608  # 8GB limit
```

**3. Missing Data Files**
```bash
# Verify required data files exist
ls -la data/psa_extended.csv
ls -la config/strategies.yml

# Run data preparation if needed
python nextgen_v3/cli/run_sourcing.py
```

### Performance Optimization

**1. Parallel Processing**
```python
# Enable multiprocessing in your custom scripts
from multiprocessing import Pool
import numpy as np

def run_parallel_psa(n_cores=4):
    with Pool(n_cores) as pool:
        # Split PSA iterations across cores
        pass
```

**2. Result Caching**
```python
# Cache expensive computations
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_analysis_function(params_hash):
    # Expensive computation here
    return results
```

**3. Memory Management**
```python
# Process large datasets in chunks
def process_large_psa(df, chunk_size=1000):
    for chunk in pd.read_csv(file, chunksize=chunk_size):
        yield process_chunk(chunk)
```

## API Reference

### Core Classes
- `V3PipelineRunner`: Main pipeline orchestrator
- `ProgressIndicator`: User feedback system  
- `ComparisonPlotter`: Advanced visualization
- `VOIAnalyzer`: Value of information calculations

### Key Functions
- `create_comprehensive_v3_dashboard()`: Multi-panel comparison plots
- `run_comprehensive_voi_analysis()`: Complete VOI workflow
- `apply_publication_style()`: Professional plot formatting

## Migration from V2

### Automated Migration
```bash
# V2 to V3 command equivalents:

# V2: python analysis_v2/run_pipeline.py
# V3: python nextgen_v3/cli/run_pipeline.py

# V2: python analysis_v2/make_ceaf.py --perspective health_system  
# V3: python nextgen_v3/cli/run_cea.py --perspective health_system

# V2: python analysis_v2/make_bia.py --jur AU
# V3: python nextgen_v3/cli/run_bia.py --jur AU
```

### Configuration Updates
V2 config files can be adapted for V3:

```python
# Convert V2 config to V3 format
from nextgen_v3.compat.cli_adapters import adapt_v2_run_pipeline_args

v2_args = load_v2_config()
v3_config = adapt_v2_run_pipeline_args(v2_args)
```

## Support & Contributing

### Getting Help
- **Documentation**: See `nextgen_v3/docs/` for detailed technical docs
- **Examples**: Check `nextgen_v3/examples/` for usage patterns  
- **Tests**: Run `pytest nextgen_v3/tests/` to verify installation

### Performance Monitoring
V3 includes built-in performance tracking:

```bash
# Enable verbose logging for performance analysis
python nextgen_v3/cli/run_pipeline.py --verbose

# Output includes timing for each step:
# ✅ Completed: CEA analysis (AU, health_system) (45.2s)
# ✅ Completed: PSA analysis (127.8s)  
# ✅ Completed: Comparison plot generation (23.1s)
```

---

**V3 NextGen Equity Framework** - Publication-ready health economic analysis with distributional equity considerations.

*For technical support or feature requests, see the project documentation or contact the development team.*