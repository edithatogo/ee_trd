# V3 Technical Architecture Analysis

## Current V3 Codebase Structure

```
nextgen_v3/
├── cli/                    # Command-line interfaces
│   ├── run_cea.py         # Cost-effectiveness analysis
│   ├── run_dcea.py        # Distributional CEA (equity)
│   ├── run_dsa.py         # Deterministic sensitivity analysis  
│   ├── run_psa.py         # Probabilistic sensitivity analysis
│   └── run_bia.py         # Budget impact analysis
├── plots/                  # Visualization modules
│   ├── ceaf.py            # Cost-effectiveness acceptability frontiers
│   ├── ceac.py            # Cost-effectiveness acceptability curves
│   ├── pricing.py         # Price-probability curves
│   ├── equity.py          # Equity-specific visualizations
│   ├── tornado.py         # Tornado diagrams
│   └── frontier.py        # Efficiency frontiers and regret curves
├── config/                 # Configuration management
│   └── settings.yaml      # Main configuration file
├── data_schemas/          # Data structure definitions
│   └── dcea_weights.csv   # Equity weighting specifications
└── models/                # Core analysis engines (implied)
```

## V3 vs V2 Architecture Comparison

| Component | V2 Enhanced | V3 Current | Gap Analysis |
|-----------|-------------|------------|--------------|
| **Therapy Coverage** | 5 therapies | 4 therapies | Missing 1 therapy |
| **Naming System** | Publication names (IV-KA, IN-EKA) | Generic names | Inconsistent labeling |
| **Plot Quality** | Publication-ready with styling | Basic matplotlib | No publication formatting |
| **Comparison Plots** | Comprehensive side-by-side | None | Missing comparative analysis |
| **PSA Visualization** | Proper uncertainty clouds | Basic scatter | Limited uncertainty representation |
| **Axis Scaling** | Optimized ranges (0-75k) | Wide ranges (0-100k) | Poor curve differentiation |
| **VOI Analysis** | EVPI integrated | None | Missing value of information |
| **Equity Framework** | N/A | DCEA foundation | Unique equity capability |

## Critical Dependencies

### Data Dependencies
- `data/cost_inputs_au.csv` - Australian cost data
- `data/cost_inputs_nz.csv` - New Zealand cost data  
- `data/parameters_psa.csv` - PSA parameter distributions
- Missing: Complete therapy definitions for all 5 arms

### Code Dependencies
- V2 enhanced plotting patterns (for styling reference)
- Equity data schemas (partially implemented)
- DSA parameter data (for tornado plots)

## Implementation Priority Matrix

| Issue Category | Impact | Effort | Priority | Timeline |
|----------------|---------|---------|----------|----------|
| Missing therapies | High | Medium | Critical | Days 1-2 |
| X-axis scaling | High | Low | Critical | Day 1 |
| Therapy naming | High | Medium | High | Days 2-3 |
| Publication styling | Medium | High | High | Days 4-6 |
| Comparison plots | Medium | High | Medium | Days 7-9 |
| Equity framework | Low | High | Medium | Days 10-12 |
