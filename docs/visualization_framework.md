# V4 Visualization Framework

## Overview

The V4 visualization framework provides comprehensive publication-quality plotting capabilities for health economic evaluation, meeting Australian and New Zealand Journal of Psychiatry standards.

## Framework Structure

```
analysis/plotting/
├── __init__.py              # Main exports
├── publication.py           # Journal standards and utilities
├── cea_plots.py            # Cost-effectiveness analysis plots
├── dcea_plots.py           # Distributional CEA and equity plots
├── voi_plots.py            # Value of information plots
├── vbp_plots.py            # Value-based pricing plots
├── bia_plots.py            # Budget impact analysis plots
├── comparison_plots.py     # Multi-panel comparisons
└── advanced_plots.py       # 3D and advanced visualizations
```

## Plot Types by Module

### 1. Publication Framework (`publication.py`)
- **JournalStandards**: Configuration for journal requirements
- **FigureArtifacts**: Multi-format output management
- **Utilities**: Axis formatting, legends, reference lines
- **Standards**: 300 DPI, proper sizing, color schemes

### 2. Cost-Effectiveness Analysis (`cea_plots.py`)
1. **CE Plane** - Cost-effectiveness scatter plot with WTP threshold
2. **CEAC** - Cost-effectiveness acceptability curve
3. **CEAF** - Cost-effectiveness acceptability frontier
4. **INMB Distribution** - Incremental net monetary benefit distributions
5. **Tornado Diagram** - One-way sensitivity analysis

### 3. Distributional CEA (`dcea_plots.py`)
6. **Equity Impact Plane** - Total QALYs vs inequality
7. **Atkinson Index** - Inequality measurement over WTP
8. **EDE-QALYs** - Equally distributed equivalent QALYs
9. **Distributional CEAC** - Equity-weighted acceptability curves
10. **Subgroup Comparison** - Population subgroup analysis

### 4. Value of Information (`voi_plots.py`)
11. **EVPI Curve** - Expected value of perfect information
12. **EVPPI Bars** - Expected value of partial perfect information
13. **EVSI Curve** - Expected value of sample information
14. **VOI Tornado** - Research prioritization

### 5. Value-Based Pricing (`vbp_plots.py`)
15. **VBP Curve** - Price vs probability cost-effective
16. **Threshold Price** - Maximum prices at different WTP levels
17. **Price Elasticity** - Demand response to price changes
18. **Multi-Indication VBP** - Pricing across indications
19. **Risk-Sharing Scenarios** - Agreement scenario analysis

### 6. Budget Impact Analysis (`bia_plots.py`)
20. **Annual Budget Impact** - Year-by-year impact
21. **Cumulative Budget Impact** - Cumulative over time
22. **Market Share Evolution** - Stacked area chart
23. **Budget Impact Breakdown** - By cost category
24. **Population Impact** - Patient numbers over time
25. **Affordability Analysis** - Impact vs capacity
26. **Scenario Comparison** - Different adoption scenarios

### 7. Comparison Plots (`comparison_plots.py`)
27. **Perspective Comparison** - Healthcare vs societal
28. **Jurisdiction Comparison** - Australia vs New Zealand
29. **Comprehensive Dashboard** - 4-panel overview
30. **Strategy Comparison Grid** - Multi-strategy matrix

### 8. Advanced Visualizations (`advanced_plots.py`)
31. **3D Sensitivity Surface** - Two-parameter sensitivity
32. **Parameter Interaction Heatmap** - Interaction effects
33. **Pathway Network** - Treatment pathway diagrams
34. **Multi-Dimensional Projection** - PCA/t-SNE visualizations

## Total Plot Types: 34+

## Key Features

### Publication Quality
- **Resolution**: 300 DPI minimum (configurable)
- **Formats**: PNG, PDF, SVG, TIFF
- **Sizing**: Journal-compliant dimensions
- **Fonts**: Professional typography
- **Colors**: Colorblind-friendly palettes

### Therapy Naming
- Uses V4 manuscript abbreviations:
  - ECT, KA-ECT, IV-KA, IN-EKA
  - PO-PSI, PO-KA
  - rTMS, UC+Li, UC+AA
  - Usual Care

### Currency Formatting
- Automatic currency symbol placement
- Thousands separators
- Configurable precision
- Support for A$ (Australia) and NZ$ (New Zealand)

### Axis Formatting
- Currency axes with proper formatting
- Percentage axes (0-100%)
- Automatic scaling for large numbers
- Grid lines and reference lines

### Legend Management
- Automatic positioning
- Multi-column support
- Consistent styling
- Therapy-specific colors

## Usage Examples

### Basic CEA Plot
```python
from analysis.plotting import plot_ce_plane

plot_ce_plane(
    costs=costs_df,
    effects=effects_df,
    output_path=Path("figures/ce_plane.png"),
    wtp_threshold=50000,
    currency="A$"
)
```

### Equity Analysis
```python
from analysis.plotting import plot_equity_impact_plane

plot_equity_impact_plane(
    total_qalys=qalys_df,
    inequality=inequality_df,
    output_path=Path("figures/equity_plane.png")
)
```

### Budget Impact
```python
from analysis.plotting import plot_annual_budget_impact

plot_annual_budget_impact(
    bia_data=bia_df,
    output_path=Path("figures/bia_annual.png"),
    currency="A$"
)
```

### Comprehensive Dashboard
```python
from analysis.plotting import plot_comprehensive_dashboard

plot_comprehensive_dashboard(
    cea_data=cea_df,
    ceac_data=ceac_df,
    evpi_data=evpi_df,
    output_path=Path("figures/dashboard.png"),
    currency="A$"
)
```

## Multi-Format Export

All plotting functions support multi-format export:

```python
from analysis.plotting import save_multiformat

# Automatically saves PNG, PDF, SVG, TIFF
artifacts = save_multiformat(
    fig=figure,
    base_path=Path("figures/my_plot"),
    formats=['png', 'pdf', 'svg', 'tiff'],
    dpi=300
)
```

## Journal Standards Configuration

```python
from analysis.plotting import JournalStandards

# Australian and New Zealand Journal of Psychiatry
standards = JournalStandards(
    min_dpi=300,
    max_width_inches=7.0,
    max_height_inches=9.0,
    font_family='Arial',
    font_size_base=10
)
```

## Customization

### Custom Colors
```python
# Define custom color palette
custom_colors = {
    'ECT': '#1f77b4',
    'KA-ECT': '#ff7f0e',
    'IV-KA': '#2ca02c',
    # ... more strategies
}
```

### Custom Styling
```python
from analysis.plotting import journal_style, figure_context

with journal_style(), figure_context(figsize=(10, 6)):
    # Your plotting code here
    pass
```

## Output Organization

Recommended figure output structure:
```
figures/
├── cea/
│   ├── ce_plane_healthcare.png
│   ├── ceac_healthcare.png
│   └── ceaf_healthcare.png
├── dcea/
│   ├── equity_plane.png
│   ├── atkinson_index.png
│   └── distributional_ceac.png
├── voi/
│   ├── evpi_curve.png
│   └── evppi_bars.png
├── vbp/
│   ├── vbp_curve.png
│   └── threshold_price.png
├── bia/
│   ├── annual_impact.png
│   └── cumulative_impact.png
└── comparison/
    ├── perspective_comparison.png
    └── jurisdiction_comparison.png
```

## Quality Assurance

All plots undergo automatic quality checks:
- ✅ Resolution meets minimum DPI
- ✅ Dimensions within journal limits
- ✅ All required formats generated
- ✅ File sizes reasonable
- ✅ No missing data warnings
- ✅ Proper axis labels and titles

## Integration with Analysis Engines

The visualization framework integrates seamlessly with all analysis engines:

```python
from analysis.engines import CEAEngine
from analysis.plotting import plot_ce_plane, plot_ceac

# Run analysis
engine = CEAEngine(psa_data)
results = engine.run_analysis()

# Generate plots
plot_ce_plane(
    costs=results['costs'],
    effects=results['effects'],
    output_path=Path("figures/ce_plane.png")
)

plot_ceac(
    ceac_data=results['ceac'],
    output_path=Path("figures/ceac.png")
)
```

## Performance Considerations

- **Caching**: Figures are cached to avoid regeneration
- **Parallel Generation**: Multiple figures can be generated in parallel
- **Memory Management**: Large datasets are handled efficiently
- **Format Optimization**: Each format optimized for size/quality

## Accessibility

All visualizations follow accessibility best practices:
- Colorblind-friendly palettes
- High contrast ratios
- Clear labeling
- Alternative text support
- Screen reader compatibility

## Version Control

Figure versioning is managed through:
- Timestamp in metadata
- Git integration
- Manifest tracking
- Reproducibility checksums

---

*This visualization framework provides comprehensive, publication-ready plotting capabilities for the V4 health economic evaluation, ensuring all figures meet journal standards and support the manuscript submission process.*
