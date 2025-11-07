# V4 Figures Status Report

**Date**: October 2, 2025  
**Current Status**: Partial - Only 4 of 47+ figure types generated

---

## Problem Identified

The V4 analysis only generated **basic outputs** and therefore only **4 figure types** were created, when the design document specifies **47+ figure types** across multiple analysis categories.

---

## What Was Generated ✅

### Current Figures (4 types × 4 perspectives = 16 figures)

1. **CE Plane** - Cost-effectiveness plane ✅
2. **CEAC** - Cost-effectiveness acceptability curve ✅
3. **CEAF** - Cost-effectiveness acceptability frontier ✅
4. **EVPI Curve** - Expected value of perfect information ✅

---

## What's Missing ❌

### Missing Data/Analyses

The following analyses were NOT run, so we don't have data to generate their figures:

#### 1. Value-Based Pricing (VBP) - 5 figure types
- ❌ VBP curves
- ❌ Threshold price analysis
- ❌ Price elasticity curves
- ❌ Multi-indication VBP
- ❌ Risk-sharing scenarios

**Missing Data**: No VBP analysis was run

#### 2. Budget Impact Analysis (BIA) - 7 figure types
- ❌ Annual budget impact
- ❌ Cumulative budget impact
- ❌ Market share evolution
- ❌ Budget impact breakdown
- ❌ Population impact
- ❌ Affordability analysis
- ❌ Scenario comparison

**Missing Data**: No BIA analysis was run

#### 3. Extended VOI - 3 additional figure types
- ❌ EVPPI bars (parameter-specific VOI)
- ❌ EVSI curves (sample information value)
- ❌ VOI tornado (research prioritization)

**Missing Data**: Only basic EVPI was calculated

#### 4. DCEA/Equity - 4 additional figure types
- ❌ Equity impact plane
- ❌ Atkinson index comparison
- ❌ EDE-QALYs visualization
- ❌ Distributional CEAC
- ❌ Subgroup comparison

**Missing Data**: Only basic DCEA summary was calculated

#### 5. Sensitivity Analysis - 5 figure types
- ❌ Tornado diagrams (OWSA)
- ❌ Tornado diagrams (PRCC)
- ❌ Two-way DSA heatmaps
- ❌ Three-way DSA (3D surfaces)
- ❌ Scenario comparisons

**Missing Data**: No DSA analysis was run

#### 6. Comparison Plots - 4 figure types
- ❌ Perspective comparison (healthcare vs societal)
- ❌ Jurisdiction comparison (AU vs NZ)
- ❌ Comprehensive dashboard
- ❌ Strategy comparison grid

**Missing Data**: Could be generated from existing data

#### 7. Advanced Plots - 4 figure types
- ❌ 3D sensitivity surfaces
- ❌ Parameter interaction heatmaps
- ❌ Pathway network diagrams
- ❌ Multi-dimensional projections

**Missing Data**: Requires additional analyses

---

## Summary

### Generated
- **4 figure types** (CE plane, CEAC, CEAF, EVPI)
- **16 total figures** (4 types × 4 perspectives)
- **48 total files** (16 figures × 3 formats)

### Missing
- **30+ figure types** not generated
- **120+ figures** missing
- **360+ files** missing (with all formats)

---

## Root Cause

The `scripts/run_v4_analysis.py` and `scripts/generate_v4_outputs.py` only implemented:
1. Basic CEA (deterministic, CEAC, CEAF)
2. Basic VOI (EVPI only)
3. Basic DCEA (summary statistics only)

They did NOT implement:
- VBP engine
- BIA engine
- Full VOI (EVPPI, EVSI)
- DSA/sensitivity engine
- Full DCEA with equity analysis
- Subgroup analysis
- Scenario analysis

---

## Solution Required

### Option 1: Generate All Missing Analyses (Recommended)

Extend the analysis scripts to run:

```python
# In scripts/generate_v4_outputs.py, add:

def run_vbp_analysis(psa, output_dir):
    """Run value-based pricing analysis."""
    # Generate VBP curves, threshold prices, etc.
    pass

def run_bia_analysis(psa, output_dir):
    """Run budget impact analysis."""
    # Generate BIA projections, market share, etc.
    pass

def run_full_voi_analysis(psa, output_dir):
    """Run complete VOI including EVPPI and EVSI."""
    # Generate EVPPI for each parameter
    # Generate EVSI curves
    pass

def run_dsa_analysis(psa, output_dir):
    """Run deterministic sensitivity analysis."""
    # Generate tornado diagrams
    # Generate two-way DSA
    pass

def run_full_dcea_analysis(psa, output_dir):
    """Run complete DCEA with equity metrics."""
    # Generate equity impact planes
    # Generate distributional CEAC
    pass
```

Then update `generate_v4_figures.py` to call all 34 plot functions.

### Option 2: Generate Figures from Existing Data Only

Create comparison plots and dashboards that can be generated from the existing CEA/CEAC/CEAF/EVPI data:
- Perspective comparisons
- Jurisdiction comparisons
- Comprehensive dashboards
- Strategy comparison grids

This would add ~16 more figures but still leave most missing.

---

## Recommendation

**Implement Option 1** - Run all missing analyses to generate complete data, then generate all 47+ figure types.

This requires:
1. Implementing VBP engine calls
2. Implementing BIA engine calls
3. Implementing full VOI (EVPPI, EVSI)
4. Implementing DSA/tornado analysis
5. Implementing full DCEA with equity metrics
6. Updating figure generation script to call all 34 plot functions

**Estimated Effort**: 2-3 hours to implement all analyses and generate all figures

---

## Current Figure Inventory

### Generated (16 figures)
```
outputs_v4/run_latest/figures/
├── AU/
│   ├── healthcare/
│   │   ├── ce_plane.{png,pdf,tiff}      ✅
│   │   ├── ceac.{png,pdf,tiff}          ✅
│   │   ├── ceaf.{png,pdf,tiff}          ✅
│   │   └── evpi_curve.{png,pdf,tiff}    ✅
│   └── societal/ (same 4 types)          ✅
└── NZ/ (same structure)                  ✅
```

### Missing (120+ figures)
- VBP figures (20 figures)
- BIA figures (28 figures)
- Extended VOI figures (12 figures)
- DCEA figures (16 figures)
- DSA figures (20 figures)
- Comparison figures (16 figures)
- Advanced figures (16 figures)

---

**Status**: ⚠️ **INCOMPLETE - Only 4 of 47+ figure types generated**

**Action Required**: Implement all missing analyses and regenerate figures

---

**Generated**: October 2, 2025  
**Author**: V4 Analysis Review
