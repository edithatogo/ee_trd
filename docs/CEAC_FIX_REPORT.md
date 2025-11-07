# CEAC Figure Fix Report

**Date:** October 10, 2025  
**Issue:** CEAC figures not displaying intervention strategies  
**Status:** ✅ **RESOLVED**

## Problem Description

The Cost-Effectiveness Acceptability Curve (CEAC) figures were displaying only reference lines and legend labels, but no strategy curves were visible. The image appeared nearly blank except for axes and title.

## Root Cause

**Data Format Mismatch:**
- The CEAC CSV data was stored in **long format** (each row = one lambda-strategy combination)
- The `plot_ceac()` function expected **wide format** (lambda as index, strategies as columns)
- The data was passed directly from CSV to plotting function without transformation

### Long Format (CSV):
```
lambda,strategy,probability_optimal,expected_nmb
0.0,UC,0.635,-5032.622
0.0,ECT,0.001,-14769.999
0.0,KA-ECT,0.000,-18189.262
...
```

### Wide Format (Expected by plot_ceac):
```
strategy    ECT  IN-EKA  IV-KA  KA-ECT  ...
lambda                                  
0.0       0.001   0.000  0.001   0.000  ...
5000.0    0.379   0.003   0.170  0.338  ...
...
```

## Solution Implemented

### Primary Fix: Data Pivoting
Added pivot transformation in `scripts/generate_v4_figures.py`:

```python
# Before (broken):
ceac_data = pd.read_csv(output_dir / 'ceac.csv')
plot_ceac(ceac_data=ceac_data, ...)

# After (fixed):
ceac_data_long = pd.read_csv(output_dir / 'ceac.csv')
ceac_data = ceac_data_long.pivot(
    index='lambda', 
    columns='strategy', 
    values='probability_optimal'
)
plot_ceac(ceac_data=ceac_data, ...)
```

### Additional Improvements
1. **SVG-First Output:** Changed all figure paths from `.png` to format-agnostic (generates SVG, PDF, PNG, TIFF)
2. **Standards Parameter:** Added `JournalStandards` parameter to all plotting calls for consistent formatting
3. **Better Logging:** Updated success messages to reflect multi-format output

## Files Modified

- `scripts/generate_v4_figures.py`:
  - Lines ~52-70: CEAC data pivoting and SVG-first output
  - Lines ~35-49: CE plane SVG-first output
  - Lines ~73-90: CEAF SVG-first output
  - Lines ~95-113: VOI figures SVG-first output + standards parameter

## Verification

### Test Results
✅ Data structure verified:
- Long format input: 310 rows × 4 columns
- Wide format output: 31 lambda values × 10 strategies
- All strategies present: ECT, IN-EKA, IV-KA, KA-ECT, PO-KA, PO-PSI, UC, UC+AA, UC+Li, rTMS

✅ Files generated successfully:
- All 4 perspectives (AU/NZ × healthcare/societal)
- All formats: SVG, PDF, PNG, TIFF
- Timestamp: Oct 10 19:05 (after fix)

### Generated Files
- `outputs_v4/run_latest/figures/AU/healthcare/ceac.*`
- `outputs_v4/run_latest/figures/AU/societal/ceac.*`
- `outputs_v4/run_latest/figures/NZ/healthcare/ceac.*`
- `outputs_v4/run_latest/figures/NZ/societal/ceac.*`

## Impact

### Fixed Figures
All CEAC figures now display correctly with:
- 10 treatment strategies visible
- Probability curves across WTP range ($0 to $150,000)
- Proper legend with all strategies
- Multi-format output (SVG, PDF, PNG, TIFF)

### Also Updated (SVG-first)
- All CE plane figures
- All CEAF figures
- All EVPI curve figures

## Prevention

**Best Practice:**
When working with PSA/CEA data:
1. Always check data format (long vs wide) before plotting
2. Use `df.pivot()` to transform long → wide when needed
3. Use `df.melt()` to transform wide → long when needed
4. Verify column names match function expectations

## Summary

**Root Cause:** Missing data pivot transformation  
**Solution:** Added `pivot()` call to convert long → wide format  
**Additional Benefit:** Upgraded all figures to SVG-first multi-format output  
**Status:** All CEAC figures now display correctly with all 10 strategies visible

---

## Update: October 10, 2025 19:07

### Additional Issue Found: Incorrect Percentage Scaling

**Problem:** After fixing the data pivot, the CEAC curves were visible but appeared too low (all near 0%). 

**Root Cause:** The data values are stored as proportions (0-1), but the plot expects percentages (0-100) to match the y-axis scale of 0-100%.

**Solution:** Modified `analysis/plotting/cea_plots.py` line ~158 to multiply probability values by 100:

```python
# Before (incorrect scaling):
ax.plot(
    ceac_data.index,
    ceac_data[strategy],  # Values 0-1
    label=strategy,
    linewidth=2
)

# After (correct scaling):
ax.plot(
    ceac_data.index,
    ceac_data[strategy] * 100,  # Convert to percentages 0-100
    label=strategy,
    linewidth=2
)
```

**Verification:**
- ✅ Max probability now displays as 63.5% (was showing as ~0.6%)
- ✅ At WTP=$50,000: KA-ECT shows 55.2%, ECT shows 31.2%
- ✅ All probabilities sum to 100% at each WTP threshold
- ✅ Curves are now clearly visible across the 0-100% range

**Files Updated:**
- `analysis/plotting/cea_plots.py` (line ~158)
- All CEAC figures regenerated at 19:07

**Status:** ✅ **FULLY RESOLVED** - CEAC curves now display at correct scale with proper percentage values

## Final Resolution - Scaling Fix Applied ✅

**Date:** October 10, 2025  
**Status:** FULLY RESOLVED  

### Final Fix Applied
- **File:** `analysis/plotting/cea_plots.py`
- **Line:** 160
- **Change:** Added `* 100` multiplication to convert proportions to percentages
- **Before:** `ceac_data[strategy],`
- **After:** `ceac_data[strategy] * 100,  # Convert proportion to percentage`

### Verification Results
- **Data Storage:** Probabilities stored as proportions (0-1) ✓
- **Display Scale:** Correctly converted to percentages (0-100%) ✓  
- **Sample Values at WTP=$50k:**
  - KA-ECT: 55.2% (was 0.5520)
  - ECT: 31.2% (was 0.3120) 
  - PO-PSI: 9.3% (was 0.0930)
- **Validation:** All probabilities sum to 100% at each WTP threshold ✓
- **Figures:** All 4 perspectives regenerated successfully ✓

### Root Cause Analysis
The CEAC data was correctly calculated and stored as proportions (0-1), but the plotting function was displaying these values directly on a percentage scale (0-100%) without the necessary conversion. This caused all probabilities to appear ~100x too small.

### Impact
- CEAC curves now display correctly with proper percentage values
- All 10 strategies are visible with appropriate probability distributions
- Figures meet publication standards for clarity and accuracy

**Resolution Complete** 🎉

## CEAF Display Improvements ✅

**Date:** October 10, 2025  
**Status:** COMPLETED  

### Improvements Made
- **File:** `analysis/plotting/cea_plots.py` - `plot_ceaf()` function
- **Visualization Type:** Changed from stacked area plot to clear frontier line
- **Key Features Added:**
  - Single CEAF curve showing probability of optimal strategy
  - Strategy change markers with vertical lines and annotations
  - Colored background regions indicating which strategy is optimal
  - Clear annotations showing strategy transitions with WTP thresholds

### Before vs After
**Before:** Confusing stacked area plot attempting to show multiple strategies simultaneously
**After:** Clear frontier line with:
- Blue CEAF curve showing probability cost-effective
- Vertical dashed lines at strategy change points ($5k, $10k)
- Annotated arrows showing UC→ECT→KA-ECT transitions
- Pastel background colors for each optimal strategy region

### Data Insights Revealed
- **Strategy Changes:** 2 transitions across WTP range
  - $5,000: UC → ECT (37.9% probability)
  - $10,000: ECT → KA-ECT (47.5% probability)
- **Dominant Strategy:** KA-ECT optimal for 93.5% of WTP thresholds
- **Probability Range:** 37.9% - 63.5% (well within 0-100% scale)

### Technical Details
- Proper scaling: `probability * 100` for percentage display
- Strategy region visualization using `axvspan()` with alpha=0.2
- Annotation positioning with automatic offset calculation
- Color-coded strategy changes with distinct colors
- Improved legend placement and readability

**CEAF Display Enhancement Complete** 🎯
