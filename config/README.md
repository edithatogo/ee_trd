# V4 Configuration Files

This directory contains all configuration files for V4 analyses.

## Configuration Files

### `v4_strategies.yml`
**Purpose**: Defines treatment strategies using V4 manuscript abbreviations

**Key Sections**:
- `strategies`: List of all therapies (ECT, KA-ECT, IV-KA, IN-EKA, PO-PSI, PO-KA, rTMS, UC+Li, UC+AA, Usual Care)
- `prices`: Base pricing for each therapy
- `labels`: Human-friendly display names
- `full_names`: Complete therapy names for documentation
- `step_care_sequences`: Treatment pathway definitions

**Usage**:
```python
from analysis.core.io import StrategyConfig
config = StrategyConfig.from_yaml(Path("config/v4_strategies.yml"))
```

### `v4_analysis_defaults.yml`
**Purpose**: Default parameters for all V4 analyses

**Key Sections**:
- `data`: Input data file paths
- `wtp`: Willingness-to-pay parameters
- `psa`: PSA configuration (iterations, seed)
- `discount`: Discount rates for AU and NZ
- `output`: Output directory and format settings
- `modules`: Enable/disable analysis modules
- `indigenous`: Indigenous population analysis settings
- `publication`: Journal standards and figure requirements

**Usage**:
```python
from analysis.core.config import load_v4_config
config = load_v4_config()
```

### `journal_standards.yml`
**Purpose**: Publication standards for target journals

**Key Sections**:
- `australian_nz_psychiatry`: Standards for Australian and New Zealand Journal of Psychiatry
  - Figure resolution (300 DPI minimum)
  - Accepted formats (TIFF, EPS, PDF)
  - Dimension requirements
  - Font specifications
  - Color mode (RGB, sRGB profile)
- `generic`: Fallback standards for other journals

**Usage**:
```python
from analysis.core.config import load_journal_standards
standards = load_journal_standards("australian_nz_psychiatry")
```

## Legacy Configuration Files

### `strategies.yml` (V2/V3)
Legacy strategy configuration using old naming conventions. Preserved for reference but not used in V4.

### `analysis_v2_defaults.yml` (V2)
Legacy V2 analysis defaults. Superseded by `v4_analysis_defaults.yml`.

### `bia.yaml` (V2)
Legacy budget impact analysis configuration. Settings now integrated into `v4_analysis_defaults.yml`.

## V4 Therapy Abbreviations

V4 uses standardized manuscript abbreviations for all therapies:

| Abbreviation | Full Name |
|--------------|-----------|
| ECT | Standard Electroconvulsive Therapy |
| KA-ECT | Ketamine-Assisted ECT |
| IV-KA | Intravenous Ketamine |
| IN-EKA | Intranasal Esketamine |
| PO-PSI | Oral Psilocybin-Assisted Therapy |
| PO-KA | Oral Ketamine |
| rTMS | Repetitive Transcranial Magnetic Stimulation |
| UC+Li | Usual Care + Lithium Augmentation |
| UC+AA | Usual Care + Atypical Antipsychotic |
| Usual Care | Standard Care Comparator |

## Configuration Validation

All configurations are validated on load:

```python
from analysis.core.config import load_v4_config, validate_config

config = load_v4_config()
warnings = validate_config(config)

if warnings:
    print("Configuration warnings:")
    for warning in warnings:
        print(f"  - {warning}")
```

## Customization

To customize analysis parameters:

1. Copy `v4_analysis_defaults.yml` to a new file
2. Modify parameters as needed
3. Load custom configuration:

```python
config = load_v4_config(Path("config/my_custom_config.yml"))
```

## Publication Standards

V4 ensures all outputs meet Australian and New Zealand Journal of Psychiatry requirements:

- **Resolution**: 300 DPI minimum (600 DPI preferred)
- **Formats**: TIFF (preferred), EPS, PDF
- **Dimensions**: 
  - Single column: 84mm (3.31")
  - Double column: 174mm (6.85")
  - Full page: 174mm × 234mm
- **Fonts**: Arial or Helvetica, minimum 8pt
- **Colors**: RGB mode, sRGB profile

These standards are automatically applied when using V4 plotting functions.
