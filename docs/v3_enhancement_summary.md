# V3 Enhancement Plan Summary Report

**Date**: 28 September 2025  
**Status**: Planning Complete - Ready for Implementation

## Executive Summary

The V3 NextGen Equity Framework currently has **all the same issues we just fixed in V2**, plus additional gaps specific to the equity analysis components. This comprehensive plan addresses every identified issue and provides a structured 15-day implementation roadmap.

## Critical Issues Confirmed

### ❌ **Same V2 Issues Present in V3:**
1. **Missing Therapies**: Only 4/5 therapies (missing Oral_ketamine, ECT_ket_anaesthetic)
2. **Generic Naming**: Uses "Ketamine_IV" instead of "IV-KA" publication names  
3. **X-axis Scaling**: CEAF plots use 0-100k range (should be 0-75k)
4. **No Publication Styling**: Basic matplotlib without professional formatting
5. **Missing Comparison Plots**: No side-by-side analyses
6. **Poor PSA Visualization**: Limited uncertainty representation

### ❌ **Additional V3-Specific Issues:**
7. **Incomplete Equity Framework**: DCEA using stub data
8. **Basic Plot Infrastructure**: Many functions are placeholder TODOs
9. **Missing VOI Integration**: No value of information analysis

## Solution Overview

### **5-Phase Implementation Plan** (15 days total)

1. **Phase 1 (Days 1-3)**: Critical Foundation
   - Fix therapy coverage and naming
   - Optimize WTP ranges for curve differentiation
   - Add basic publication styling

2. **Phase 2 (Days 4-6)**: Publication-Quality Plotting  
   - Enhance all individual plot functions
   - Add professional formatting and styling
   - Implement proper PSA uncertainty visualization

3. **Phase 3 (Days 7-9)**: Comparison System
   - Create side-by-side comparative plots
   - Add multi-panel dashboard system
   - Integrate value of information analysis

4. **Phase 4 (Days 10-12)**: Equity Framework Completion
   - Complete DCEA data integration with real equity weights
   - Enhance distributional analysis visualizations
   - Add Indigenous/Pacific population weightings

5. **Phase 5 (Days 13-15)**: Integration & Quality Assurance
   - Orchestrate complete pipeline
   - Comprehensive testing and validation
   - Documentation and publication readiness

## Key Deliverables

### **Immediate Fixes (Phase 1)**
- All 5 therapies properly represented
- CEAF plots with 0-75k x-axis (not 0-100k)
- Proper therapy naming (IV-KA, IN-EKA, PO psilocybin, PO-KA, KA-ECT)
- Basic publication styling applied

### **Enhanced Capabilities (Phases 2-3)**  
- Publication-quality plots with professional formatting
- Comprehensive comparison plot system (matching V2)
- PSA uncertainty properly visualized
- EVPI analysis integrated
- Currency formatting (AUD/NZD)

### **Unique V3 Features (Phase 4)**
- Complete distributional CEA with equity weighting
- Equity impact planes and distributional acceptability curves
- Population subgroup analysis with Indigenous/Pacific focus
- Social welfare function integration (Atkinson)

### **Production Ready (Phase 5)**
- Complete orchestrated pipeline
- All analyses generating publication-ready outputs
- Comprehensive test coverage
- User documentation

## Implementation Strategy

### **Critical Path Dependencies**
1. Therapy standardization must happen first
2. Plot styling can proceed in parallel with equity framework
3. Comparison system builds on individual plot enhancements
4. Final integration requires all components complete

### **Resource Requirements**
- **Development Time**: 15 working days (3 weeks)
- **Key Dependencies**: V2 codebase patterns, real equity data
- **Risk Mitigation**: Staged rollout with compatibility flags

### **Success Metrics**
- [ ] All 5 therapies in every analysis
- [ ] CEAF x-axis 0-75k (not 0-100k) 
- [ ] Publication-quality formatting throughout
- [ ] Complete equity analysis framework
- [ ] Performance maintained (<30s total runtime)

## Recommendations

### **Immediate Action**
✅ **Begin Phase 1 immediately** - therapy standardization and WTP optimization are critical and low-risk

### **Parallel Development**
✅ **V2 and V3 can coexist** - V2 provides immediate publication-ready outputs while V3 develops equity capabilities

### **Strategic Positioning** 
✅ **V3 as equity-enhanced V2** - Position V3 as the advanced version with distributional analysis, not a replacement

## Next Steps

1. **This Week**: Complete Phase 1 (critical foundation fixes)
2. **Next Week**: Execute Phases 2-3 (publication plotting and comparisons)  
3. **Following Week**: Finish Phases 4-5 (equity framework and integration)

## Documentation Created

1. **`docs/v3_enhancement_plan.md`** - Comprehensive enhancement strategy
2. **`docs/v3_technical_analysis.md`** - Architecture and dependency analysis  
3. **`docs/v3_implementation_checklist.md`** - Detailed implementation tasks

This plan transforms V3 from its current state with basic plotting and incomplete equity framework into a publication-ready analysis system that **exceeds V2 capabilities** by adding sophisticated distributional cost-effectiveness analysis while maintaining all the publication-quality features we built in V2.