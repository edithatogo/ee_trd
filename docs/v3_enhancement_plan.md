# V3 NextGen Equity Framework Enhancement Plan

**Date:** 28 September 2025  
**Scope:** Comprehensive fixes for V3 analysis issues based on V2 enhancement learnings  
**Status:** Planning Phase

## Executive Summary

The V3 NextGen Equity Framework currently has significant gaps compared to the enhanced V2 analysis system. This plan addresses all identified issues and provides a roadmap for bringing V3 to publication-quality standards while preserving its unique equity analysis capabilities.

## Issues Identified

### 1. Critical Data Issues
- **Missing Therapies**: Only 4/5 therapies present (missing `Oral_ketamine`, `ECT_ket_anaesthetic`)
- **Generic Naming**: Uses "Ketamine_IV", "Esketamine" instead of publication names
- **Inconsistent Coverage**: Incomplete therapy representation across analyses

### 2. Plotting & Visualization Issues
- **X-axis Scaling**: CEAF plots use 0-100k range (should be 0-75k for curve differentiation)
- **Basic Formatting**: No publication-quality styling, currency formatting, or enhanced legends
- **Missing PSA Visualization**: No proper uncertainty representation in CE planes
- **Stub Implementations**: Many plotting functions have TODO placeholders

### 3. Publication Quality Issues  
- **No Comparison Plots**: Missing side-by-side therapy comparisons
- **Basic Plot Styling**: Simple matplotlib without professional formatting
- **Poor Legend Systems**: Generic labels without intuitive naming conventions
- **Missing Analysis Types**: No EVPI, limited VOI analysis integration

### 4. Equity Framework Specific Issues
- **Incomplete DCEA Implementation**: Using stub data for equity groups and weights
- **Missing Distributional Analysis**: Limited equity impact visualization
- **Basic Equity Plots**: Placeholder equity visualizations

### 5. Configuration & Settings Issues
- **Wide WTP Ranges**: Same 0-100k scaling problems as original V2
- **Missing Therapy Configuration**: Incomplete arm definitions
- **Basic Settings**: No optimized ranges for publication clarity

## Enhancement Plan

### Phase 1: Foundation & Data Consistency (Priority: Critical)

#### 1.1 Therapy Standardization
**Target Files:**
- `nextgen_v3/config/settings.yaml`
- Data input mappings
- Therapy label systems

**Actions:**
```yaml
# Update settings.yaml arms section
arms: [ECT_std, ECT_ket_anaesthetic, Ketamine_IV, Esketamine, Psilocybin, Oral_ketamine]

# Add proper therapy labeling system
therapy_labels:
  ECT_std: "ECT"
  ECT_ket_anaesthetic: "KA-ECT" 
  Ketamine_IV: "IV-KA"
  Esketamine: "IN-EKA"
  Psilocybin: "PO psilocybin"
  Oral_ketamine: "PO-KA"
```

#### 1.2 WTP Range Optimization
**Target:** `nextgen_v3/config/settings.yaml`
```yaml
# Focused WTP ranges for better curve differentiation
wtp_grid: [0, 12500, 25000, 37500, 50000, 62500, 75000]
pricing_max: 50000
ceaf_max_wtp: 75000
```

### Phase 2: Publication-Quality Plotting System (Priority: High)

#### 2.1 Enhanced Plotting Infrastructure
**New Files to Create:**
- `nextgen_v3/plots/publication_style.py` - Style configuration
- `nextgen_v3/plots/comparison_plots.py` - Comparative analysis plots  
- `nextgen_v3/plots/utils.py` - Common plotting utilities

**Key Features:**
```python
# Publication style configuration
PUBLICATION_STYLE = {
    'figure_size': (12, 8),
    'dpi': 300,
    'font_family': 'Arial',
    'font_sizes': {'title': 14, 'labels': 12, 'ticks': 10},
    'color_palette': 'Set2',
    'grid_alpha': 0.3
}

# Currency formatting
def format_currency(value, country='AU'):
    if country == 'AU':
        return f"${value:,.0f} AUD"
    elif country == 'NZ': 
        return f"${value:,.0f} NZD"
```

#### 2.2 Enhanced Individual Plot Scripts
**Files to Upgrade:**
- `nextgen_v3/plots/ceaf.py` - Add publication styling, proper legends, focused x-axis
- `nextgen_v3/plots/ceac.py` - Add uncertainty bands, professional formatting
- `nextgen_v3/plots/pricing.py` - Fix scaling, add confidence intervals
- `nextgen_v3/plots/tornado.py` - Replace placeholder with real DSA data

**Example CEAF Enhancement:**
```python
def plot_ceaf(ceaf_df, output_path='nextgen_v3/out/ceaf_v3.png', 
              max_wtp=75000, country='AU'):
    """Enhanced CEAF plot with publication styling."""
    plt.figure(figsize=(12, 8))
    
    # Apply publication style
    apply_publication_style()
    
    # Plot with proper therapy names and colors
    for arm in ceaf_df['arm'].unique():
        arm_data = ceaf_df[ceaf_df['arm'] == arm]
        plt.plot(arm_data['wtp'], arm_data['prob_optimal'], 
                label=get_therapy_label(arm), 
                color=get_therapy_color(arm),
                linewidth=2.5)
    
    # Professional formatting
    plt.xlabel(f'Willingness-to-Pay Threshold ({get_currency_label(country)})', fontsize=12)
    plt.ylabel('Probability of Being Optimal', fontsize=12)
    plt.xlim(0, max_wtp)
    plt.ylim(0, 1)
    
    # Enhanced legend and grid
    plt.legend(frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3)
    
    # Save with high quality
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
```

### Phase 3: Comparison & Analysis Enhancement (Priority: High)

#### 3.1 Comparison Plot System
**Create:** `nextgen_v3/plots/comparison_plots.py`

**Functions to Implement:**
- `create_ceaf_comparison_plot()` - Side-by-side country/perspective comparisons
- `create_equity_comparison_dashboard()` - Equity framework comparisons
- `create_comprehensive_dashboard()` - Multi-plot publication figure

#### 3.2 Value of Information Integration  
**Create:** `nextgen_v3/analysis/voi.py`
**Enhance:** Integrate EVPI calculations with equity framework

### Phase 4: Equity Framework Completion (Priority: Medium)

#### 4.1 DCEA Data Integration
**Target Files:**
- `nextgen_v3/data_schemas/dcea_weights.csv` (already exists)
- `nextgen_v3/data_schemas/dcea_groups.csv` (create)

**Actions:**
- Replace stub data with real equity group definitions
- Implement Atkinson social welfare functions
- Add Indigenous/Pacific population weightings

#### 4.2 Enhanced Equity Visualizations
**Upgrade:** `nextgen_v3/plots/equity.py`

**New Visualizations:**
- Distributional cost-effectiveness acceptability curves (DCEAC)
- Rank acceptability curves by equity group
- Equity impact planes with confidence intervals
- Population equity impact dashboard

### Phase 5: Pipeline Integration & Orchestration (Priority: Medium)

#### 5.1 Enhanced CLI System
**Files to Enhance:**
- `nextgen_v3/cli/run_pipeline.py` - Main orchestrator
- Add comparison plot generation
- Integrate all analysis types

#### 5.2 Configuration Management
**Create:** `nextgen_v3/config/publication_defaults.yaml`
```yaml
# Publication-optimized settings
publication:
  max_wtp: 75000
  max_price: 50000
  figure_quality: 300
  style_theme: publication
  color_scheme: therapy_optimized
```

## Implementation Roadmap

### Sprint 1 (Days 1-3): Critical Foundation
1. **Therapy Standardization**: Fix naming and ensure all 5 therapies
2. **WTP Range Optimization**: Implement focused axis ranges  
3. **Basic Style Enhancement**: Add publication styling to key plots

**Deliverables:**
- All 5 therapies properly represented
- CEAF plots with 0-75k x-axis range
- Professional plot styling implemented

### Sprint 2 (Days 4-6): Publication Plotting
1. **Enhanced Plot Scripts**: Upgrade all individual plotting functions
2. **Publication Infrastructure**: Create styling and utility systems
3. **Quality Improvements**: Add currency formatting, legends, grids

**Deliverables:**
- Professional CEAF, CEAC, pricing plots
- Consistent styling across all visualizations  
- High-quality output formatting

### Sprint 3 (Days 7-9): Comparison System
1. **Comparison Plots**: Implement side-by-side analysis plots
2. **Dashboard Creation**: Multi-panel publication figures
3. **VOI Integration**: Add expected value of information analysis

**Deliverables:**
- Comparison plot system matching V2 capabilities
- Comprehensive analysis dashboards
- EVPI analysis integrated

### Sprint 4 (Days 10-12): Equity Framework
1. **DCEA Data Integration**: Replace stubs with real equity data
2. **Enhanced Equity Plots**: Professional equity visualizations
3. **Distributional Analysis**: Complete DCEAC and equity impact

**Deliverables:**
- Complete equity analysis capability
- Professional distributional visualizations
- Publication-ready equity framework

### Sprint 5 (Days 13-15): Integration & Testing  
1. **Pipeline Integration**: Orchestrated analysis system
2. **Quality Assurance**: Comprehensive testing and validation
3. **Documentation**: User guides and technical documentation

**Deliverables:**
- Complete V3 analysis pipeline
- Quality-assured outputs
- Documentation for publication use

## Success Criteria

### Technical Criteria
- [ ] All 5 therapies represented in every analysis
- [ ] CEAF plots use 0-75k x-axis range for curve differentiation
- [ ] Professional publication-quality plot formatting
- [ ] Proper therapy naming (IV-KA, IN-EKA, PO psilocybin, etc.)
- [ ] PSA uncertainty properly visualized in CE planes
- [ ] Comparison plots matching V2 capabilities

### Analysis Criteria  
- [ ] Complete equity framework with real data
- [ ] EVPI analysis integrated
- [ ] Distributional CEA with proper equity weighting
- [ ] Budget impact analysis for all therapies
- [ ] Professional tornado plots with real DSA data

### Publication Criteria
- [ ] High-resolution outputs (300 DPI)
- [ ] Consistent color schemes and styling
- [ ] Proper currency formatting (AUD/NZD)
- [ ] Intuitive legend systems
- [ ] Publication-ready figure quality

## Resource Requirements

### Development Time
- **Total Estimate**: 15 working days
- **Critical Path**: Therapy standardization → Plot enhancement → Comparison system
- **Parallel Work**: Equity framework can be developed alongside plotting improvements

### Dependencies
- V2 codebase (for styling and patterns)
- Real equity weighting data (may need stakeholder input)
- DSA parameter data (for tornado plots)
- Testing infrastructure

## Risk Assessment

### High Risk
- **Equity Data Availability**: May need to create/validate equity group weightings
- **Backward Compatibility**: Changes may affect existing V3 users

### Medium Risk  
- **Complexity Integration**: Equity framework adds complexity to standard CEA
- **Performance Impact**: Enhanced plotting may increase computation time

### Mitigation Strategies
- Implement equity framework as optional module
- Maintain compatibility flags for existing workflows
- Create staged rollout plan

## Next Steps

1. **Immediate**: Begin Sprint 1 with therapy standardization
2. **This Week**: Complete foundation and basic plot enhancements
3. **Next Week**: Implement comparison system and equity framework
4. **Following Week**: Integration, testing, and documentation

This plan provides a comprehensive roadmap to transform V3 from its current state to a publication-quality equity analysis framework that matches and exceeds the capabilities we built in V2.