# PR: NextGen v3 Framework for Ketamine vs ECT Analysis

## Summary

This PR introduces a standalone `nextgen_v3/` framework for ketamine vs ECT cost-effectiveness analysis, building on all existing features without modifying legacy v1/v2 code.

## Key Features Implemented

- **Build-on-everything**: No legacy edits; all new code isolated in `nextgen_v3/`
- **Arms Retained**: ECT_std, ECT_ket_anaesthetic, IV_ketamine, Esketamine, Psilocybin, Oral_ketamine
- **Dual Perspectives**: Health-system and societal
- **CEAC + CEAF**: Cost-Effectiveness Acceptability Curves and Frontiers with frontier arms annotated in legend
- **Pricing Thresholds**: Drug unit price thresholds where INMB=0, with 95% PSA bands
- **DCEA with EDE-QALY & Equity Visuals**: Atkinson index equity analysis with impact plane, distributional CEAC, and rank acceptability curves
- **Subgroup Sourcing**: Costs (public/private, metro/regional), utilities (state values, cognitive disutility, modifiers), equity weights (Atkinson ε + explicit) with SourceID per row and provenance tracking

## Technical Details

- Modular structure with relative imports to `nextgen_v3`
- Write-guarded outputs to `nextgen_v3/out/`
- Comprehensive pytest test suite
- Subgroup data placeholders flagged with "NEEDS_DATA" notes
- CHANGELOG_v3.md for version tracking

## Testing

All 15 tests pass, ensuring no regressions and proper isolation.

## Ready for Review

The framework is complete and ready for extension with real data sources.
