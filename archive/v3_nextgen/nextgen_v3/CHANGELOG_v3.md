# CHANGELOG_v3.md

## NextGen v3 Framework

### Overview

Standalone nextgen_v3/ package for ketamine vs ECT analysis, preserving all legacy features without modifying v1/v2 files.

### Key Features

- **Arms Retained**: ECT_std, ECT_ket_anaesthetic, IV_ketamine, Esketamine, Psilocybin, Oral_ketamine
- **Perspectives**: Health-system and societal
- **Analyses**: CEA, BIA, PSA, DSA, DCEA
- **Outputs**: CEAC, CEAF with frontier annotation, pricing thresholds with PSA bands, equity impact plane, distributional CEAC, rank acceptability curves
- **Sourcing**: Subgroup-specific costs (public/private, metro/regional), utilities (state values, cognitive disutility, modifiers), equity weights (Atkinson ε + explicit)
- **Provenance**: SourceID per row, appended to provenance_sources.csv

### Changes

- Modular structure under nextgen_v3/
- Relative imports to nextgen_v3
- Write-guarded outputs to nextgen_v3/out/
- Comprehensive pytest suite
- Subgroup data placeholders with NEEDS_DATA flags
- Frontier identification in CEAF legend

### Compatibility

- No legacy edits
- All features preserved
- Ready for extension with real data
