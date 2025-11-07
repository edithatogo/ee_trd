# V3 Enhancement Implementation Checklist

## Phase 1: Critical Foundation (Days 1-3)

### ✅ Therapy Standardization
- [ ] **Update settings.yaml**: Add missing `Oral_ketamine` and `ECT_ket_anaesthetic`
- [ ] **Implement therapy labeling system**: Create mapping from generic to publication names
- [ ] **Verify data consistency**: Ensure all analyses include 5 therapies
- [ ] **Test therapy coverage**: Validate all plots show complete therapy set

**Files to modify:**
- `nextgen_v3/config/settings.yaml`
- `nextgen_v3/data_schemas/therapy_labels.yaml` (new)

### ✅ WTP Range Optimization  
- [ ] **Update WTP grid**: Change from [0,25000,50000,75000,100000] to [0,12500,25000,37500,50000,62500,75000]
- [ ] **Set CEAF maximum**: Implement 75000 max for curve differentiation
- [ ] **Update pricing bounds**: Set pricing_max to 50000

**Files to modify:**
- `nextgen_v3/config/settings.yaml`

### ✅ Basic Style Enhancement
- [ ] **Create publication style module**: `nextgen_v3/plots/publication_style.py`
- [ ] **Implement currency formatting**: AUD/NZD display functions
- [ ] **Add color scheme**: Therapy-specific color mapping
- [ ] **Update core plots**: Apply basic styling to CEAF, CEAC, pricing

**New files:**
- `nextgen_v3/plots/publication_style.py`
- `nextgen_v3/plots/utils.py`

## Phase 2: Publication Plotting (Days 4-6)

### ✅ Enhanced Individual Plots
- [ ] **Upgrade CEAF plots**: Add focused x-axis, professional styling, proper legends
- [ ] **Enhance CEAC plots**: Add uncertainty bands, publication formatting
- [ ] **Fix pricing plots**: Implement proper scaling and confidence intervals
- [ ] **Complete tornado plots**: Replace placeholder with real DSA data

**Files to modify:**
- `nextgen_v3/plots/ceaf.py`
- `nextgen_v3/plots/ceac.py`  
- `nextgen_v3/plots/pricing.py`
- `nextgen_v3/plots/tornado.py`

### ✅ PSA Visualization Enhancement
- [ ] **Add CE plane scatter plots**: Proper PSA uncertainty clouds
- [ ] **Implement confidence intervals**: 95% CIs for all PSA-based plots
- [ ] **Add PSA summary statistics**: Mean, median, percentiles display

**Files to modify:**
- `nextgen_v3/plots/frontier.py` (add CE plane function)

## Phase 3: Comparison System (Days 7-9)

### ✅ Comparison Plot Infrastructure
- [ ] **Create comparison module**: `nextgen_v3/plots/comparison_plots.py`
- [ ] **Implement CEAF comparisons**: Side-by-side country/perspective plots
- [ ] **Add equity comparisons**: Distributional analysis comparisons
- [ ] **Create dashboard system**: Multi-panel publication figures

**New files:**
- `nextgen_v3/plots/comparison_plots.py`

### ✅ Value of Information Integration
- [ ] **Create VOI module**: `nextgen_v3/analysis/voi.py`
- [ ] **Implement EVPI calculations**: Population-level expected value of perfect information
- [ ] **Add VOI plotting**: EVPI visualization with publication styling

**New files:**
- `nextgen_v3/analysis/voi.py`
- `nextgen_v3/plots/voi.py`

## Phase 4: Equity Framework (Days 10-12)

### ✅ DCEA Data Integration
- [ ] **Complete equity groups**: Define population subgroups for analysis
- [ ] **Implement Atkinson functions**: Social welfare calculations
- [ ] **Add Indigenous weightings**: Specific equity parameters for Indigenous/Pacific populations
- [ ] **Validate equity calculations**: Test distributional CEA computations

**Files to modify:**
- `nextgen_v3/data_schemas/dcea_weights.csv`
- `nextgen_v3/data_schemas/dcea_groups.csv` (new)

### ✅ Enhanced Equity Visualizations  
- [ ] **Upgrade equity plots**: Professional styling for equity impact planes
- [ ] **Add DCEAC plots**: Distributional cost-effectiveness acceptability curves
- [ ] **Implement rank acceptability**: Equity-weighted rank acceptability curves
- [ ] **Create equity dashboard**: Comprehensive distributional analysis

**Files to modify:**
- `nextgen_v3/plots/equity.py`

## Phase 5: Integration & Testing (Days 13-15)

### ✅ Pipeline Integration
- [ ] **Update CLI orchestrator**: `nextgen_v3/cli/run_pipeline.py`
- [ ] **Integrate all analyses**: CEA, DCEA, PSA, DSA, BIA, VOI
- [ ] **Add comparison generation**: Automated comparison plot creation
- [ ] **Implement output management**: Organized directory structure

**Files to modify:**
- `nextgen_v3/cli/run_pipeline.py` (new or enhance existing)

### ✅ Quality Assurance & Documentation
- [ ] **Create test suite**: Validation tests for all analyses
- [ ] **Generate documentation**: User guides and technical docs
- [ ] **Performance testing**: Ensure reasonable computation times
- [ ] **Publication readiness**: Final quality checks

**New files:**
- `nextgen_v3/tests/test_v3_enhancements.py`
- `nextgen_v3/docs/user_guide.md`

## Success Validation Checklist

### ✅ Data Completeness
- [ ] All 5 therapies present in every analysis
- [ ] Consistent therapy naming across all outputs
- [ ] Complete parameter coverage for PSA

### ✅ Plot Quality Standards
- [ ] CEAF plots use 0-75k x-axis range
- [ ] All plots have publication-quality styling
- [ ] Proper currency formatting (AUD/NZD)
- [ ] Professional legends and labels
- [ ] High-resolution output (300 DPI)

### ✅ Analysis Completeness
- [ ] Cost-effectiveness analysis with PSA uncertainty
- [ ] Distributional CEA with equity weighting
- [ ] Value of information analysis (EVPI)
- [ ] Budget impact analysis for all therapies
- [ ] Deterministic sensitivity analysis (tornado)

### ✅ Comparison Capabilities
- [ ] Side-by-side therapy comparisons
- [ ] Multi-country comparative analysis
- [ ] Perspective comparison (health system vs societal)
- [ ] Equity impact comparisons

### ✅ Publication Readiness
- [ ] All figures suitable for journal submission
- [ ] Consistent styling and branding
- [ ] Clear, intuitive legends and labels
- [ ] Professional color schemes
- [ ] Proper uncertainty representation

## Resource Allocation

**Total Development Time**: 15 working days
**Critical Path**: Therapy standardization → Plot enhancement → Comparison system
**Parallel Development**: Equity framework development alongside core enhancements
**Testing Buffer**: 2 days for quality assurance and bug fixes

## Risk Mitigation

### High-Priority Risks
- [ ] **Equity data availability**: Prepare fallback with simulated equity weights
- [ ] **V3 compatibility**: Maintain backward compatibility with existing workflows  
- [ ] **Performance impact**: Monitor computation time increases

### Contingency Plans
- [ ] **Staged rollout**: Implement core fixes first, equity framework second
- [ ] **Compatibility flags**: Allow users to choose enhancement level
- [ ] **Documentation**: Clear migration guide for existing V3 users