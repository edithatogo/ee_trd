# Surgical Manuscript Update Plan - V4 to V6

**Date**: February 10, 2025  
**Approach**: Minimal, targeted changes only  
**Goal**: Update values without changing narrative or structure

---

## 📋 DOCUMENTS TO UPDATE

### 1. Protocol (New Version)
- **Source**: Find existing protocol document
- **Target**: `protocol_v4.md`
- **Changes**: Model structure updates only

### 2. Manuscript (New Version)
- **Source**: `manuscript_v5_20251002.md`
- **Target**: `manuscript_v6_20251010.md`
- **Changes**: Results values only

### 3. Supplementary Materials (New Version)
- **Source**: `manuscript/supplementary_materials_index.md`
- **Target**: `manuscript/supplementary_v6.md`
- **Changes**: Add all V4 tables and figures

---

## 🎯 PHASE 1: IDENTIFY WHAT TO CHANGE

### Protocol Updates Needed

**Model Structure Changes**:
1. ✓ Semi-Markov model (was: standard Markov)
2. ✓ Time-dependent transitions (was: constant)
3. ✓ Tunnel states: 0-3m, 4-6m, 7-12m, >12m
4. ✓ 10 therapy strategies (was: 3-4)

**Analysis Types Added**:
1. ✓ DCEA (Distributional CEA)
2. ✓ VOI (Value of Information)
3. ✓ VBP (Value-Based Pricing)
4. ✓ BIA (Budget Impact Analysis)
5. ✓ Advanced sensitivity (3D DSA)
6. ✓ Subgroup analysis
7. ✓ Indigenous population analysis

**What NOT to Change**:
- ✗ Study objectives
- ✗ Background/rationale
- ✗ Ethical considerations
- ✗ Data sources (unless new)

### Manuscript Updates Needed

**Results Section - Specific Values**:
1. Base case ICERs (Table 2)
2. Probabilistic results (Table 3)
3. CEAC probabilities (Figure 2)
4. Sensitivity analysis (Figure 3)
5. Subgroup results (if reported)

**Methods Section - Minimal Additions**:
1. Mention semi-Markov structure
2. List all 10 therapies
3. Reference V4 analyses

**What NOT to Change**:
- ✗ Abstract (unless results changed significantly)
- ✗ Introduction
- ✗ Discussion (unless conclusions changed)
- ✗ References
- ✗ Author list
- ✗ Acknowledgments

### Supplementary Materials - Complete Replacement

**Add All V4 Content**:
1. All 7 generated tables
2. All planned figures (9 types)
3. Mathematical equations
4. Parameter sources
5. Model structure diagrams

---

## 🔍 PHASE 2: EXTRACT CURRENT VALUES

### Step 1: Scan Manuscript for Numbers

**Search Patterns**:
```regex
- ICER values: \$[\d,]+/QALY
- Probabilities: \d+\.?\d*%
- Costs: \$[\d,]+
- QALYs: \d+\.?\d+ QALYs?
- Table references: Table \d+
- Figure references: Figure \d+
```

**Extract Locations**:
- Line numbers of each value
- Context (what the value represents)
- Current value
- Source (which analysis)

### Step 2: Map to V4 Outputs

**Mapping Table**:
| Manuscript Value | V4 Source File | V4 Column | V4 Row |
|------------------|----------------|-----------|--------|
| Base ICER (ECT) | cea_deterministic.csv | icer | strategy==ECT |
| CEAC @ $50k | ceac.csv | probability | wtp==50000 |
| EVPI @ $50k | evpi.csv | evpi | wtp==50000 |
| ... | ... | ... | ... |

### Step 3: Create Replacement Dictionary

```python
replacements = {
    # Format: (old_value, new_value, context)
    ("$45,000/QALY", "$XX,XXX/QALY", "ECT base case ICER"),
    ("65%", "XX%", "CEAC probability at $50k"),
    # ... etc
}
```

---

## 🔧 PHASE 3: SURGICAL REPLACEMENT STRATEGY

### Protocol Update Strategy

**File**: `protocol_v4.md`

**Changes** (Line-specific):
1. **Section 3.2 - Model Structure**
   - OLD: "Markov model"
   - NEW: "Semi-Markov model with time-dependent transitions"
   
2. **Section 3.3 - Health States**
   - ADD: "Tunnel states for time-since-remission: 0-3 months, 4-6 months, 7-12 months, >12 months"
   
3. **Section 3.4 - Interventions**
   - OLD: List of 3-4 therapies
   - NEW: List all 10 V4 therapies with abbreviations
   
4. **Section 4 - Analysis Plan**
   - ADD: "Distributional cost-effectiveness analysis (DCEA)"
   - ADD: "Value of information analysis (VOI)"
   - ADD: "Value-based pricing analysis (VBP)"
   - ADD: "Budget impact analysis (BIA)"

**What to Keep**:
- All objectives
- All background
- All ethical sections
- All data source descriptions (unless changed)

### Manuscript Update Strategy

**File**: `manuscript_v6_20251010.md`

**Section-by-Section Changes**:

#### Abstract
- **IF** primary outcome changed: Update result sentence
- **IF** conclusion changed: Update conclusion
- **ELSE**: No changes

#### Introduction
- **No changes** (background doesn't change)

#### Methods
- **Line X**: Add "semi-Markov model with time-dependent transitions"
- **Line Y**: Update therapy list to 10 strategies
- **Line Z**: Add sentence: "Additional analyses included distributional CEA, value of information, value-based pricing, and budget impact analysis."

#### Results

**Table 2: Base Case Results**
```
Strategy | Cost | QALYs | ICER
---------|------|-------|------
OLD → NEW (from cea_deterministic.csv)
```

**Table 3: Probabilistic Results**
```
Strategy | Mean Cost (95% CrI) | Mean QALYs (95% CrI) | Prob CE @ $50k
---------|---------------------|----------------------|----------------
OLD → NEW (from ceac.csv)
```

**In-text values**:
- Line X: "ICER of $XX,XXX" → Update from V4
- Line Y: "XX% probability" → Update from V4
- Line Z: "EVPI of $X,XXX" → Update from V4

#### Discussion
- **Minimal changes**: Only if conclusions changed
- **Keep**: All interpretation, limitations, implications

#### Figures
- **Update captions**: Use V4 therapy abbreviations
- **Update references**: Point to V4 figure files

### Supplementary Materials Strategy

**File**: `manuscript/supplementary_v6.md`

**Complete Replacement** with:

1. **All V4 Tables** (7 existing + more to generate):
   - S1-S3: Parameter tables
   - S4-S7: Results tables
   - S8-S25: Additional results (to be generated)

2. **All V4 Figures** (9 existing + more to generate):
   - Figure S1-S4: CEA figures
   - Figure S5-S6: VOI figures
   - Figure S7-S8: DCEA figures
   - Figure S9: Dashboard
   - Figure S10-S25: Additional figures

3. **Mathematical Appendix**:
   - Use: `manuscript/supplementary_equations_v4.md`

4. **Parameter Sources**:
   - Use: `data/documentation/parameter_sources.md`

---

## 📊 PHASE 4: IMPLEMENTATION STEPS

### Step 1: Prepare Data Extraction Script

```python
# scripts/extract_v4_values.py
"""
Extract all values from V4 outputs for manuscript update.
"""

def extract_values():
    # Load V4 outputs
    cea = pd.read_csv('results/v4_test/cea_deterministic.csv')
    ceac = pd.read_csv('results/v4_test/ceac.csv')
    evpi = pd.read_csv('results/v4_test/evpi.csv')
    
    # Extract key values
    values = {
        'base_case_icers': {},
        'ceac_probabilities': {},
        'evpi_values': {},
    }
    
    # Populate values dictionary
    for strategy in cea['strategy']:
        values['base_case_icers'][strategy] = {
            'cost': cea[cea['strategy']==strategy]['cost'].values[0],
            'qalys': cea[cea['strategy']==strategy]['effect'].values[0],
            'icer': cea[cea['strategy']==strategy].get('icer', 'N/A'),
        }
    
    return values
```

### Step 2: Create Manuscript Scanner

```python
# scripts/scan_manuscript.py
"""
Scan manuscript for values that need updating.
"""

def scan_for_values(manuscript_path):
    with open(manuscript_path) as f:
        lines = f.readlines()
    
    findings = []
    for i, line in enumerate(lines):
        # Find ICER values
        if re.search(r'\$[\d,]+/QALY', line):
            findings.append({
                'line': i,
                'type': 'ICER',
                'value': re.findall(r'\$[\d,]+/QALY', line)[0],
                'context': line.strip()
            })
        
        # Find probabilities
        if re.search(r'\d+\.?\d*%', line):
            findings.append({
                'line': i,
                'type': 'Probability',
                'value': re.findall(r'\d+\.?\d*%', line)[0],
                'context': line.strip()
            })
    
    return findings
```

### Step 3: Create Surgical Replacement Script

```python
# scripts/update_manuscript_surgical.py
"""
Surgically update manuscript with V4 values.
"""

def update_manuscript(source, target, replacements):
    with open(source) as f:
        content = f.read()
    
    # Apply each replacement
    for old_val, new_val, context in replacements:
        # Only replace if context matches
        if context in content:
            content = content.replace(old_val, new_val, 1)
    
    # Save new version
    with open(target, 'w') as f:
        f.write(content)
```

### Step 4: Create Validation Script

```python
# scripts/validate_updates.py
"""
Validate that updates were applied correctly.
"""

def validate_updates(original, updated, expected_changes):
    # Load both versions
    with open(original) as f:
        old_lines = f.readlines()
    with open(updated) as f:
        new_lines = f.readlines()
    
    # Find differences
    diffs = []
    for i, (old, new) in enumerate(zip(old_lines, new_lines)):
        if old != new:
            diffs.append({
                'line': i,
                'old': old.strip(),
                'new': new.strip()
            })
    
    # Verify expected number of changes
    assert len(diffs) == expected_changes, \
        f"Expected {expected_changes} changes, found {len(diffs)}"
    
    return diffs
```

---

## ✅ PHASE 5: EXECUTION CHECKLIST

### Pre-Update
- [ ] Extract all V4 values
- [ ] Scan manuscript for current values
- [ ] Create replacement mapping
- [ ] Review mapping for accuracy
- [ ] Backup original files

### Protocol Update
- [ ] Create protocol_v4.md
- [ ] Update model structure section
- [ ] Update interventions list
- [ ] Update analysis plan
- [ ] Validate changes

### Manuscript Update
- [ ] Create manuscript_v6_20251010.md
- [ ] Update Methods section (minimal)
- [ ] Update Results tables
- [ ] Update Results in-text values
- [ ] Update Figure captions
- [ ] Validate changes

### Supplementary Update
- [ ] Create supplementary_v6.md
- [ ] Include all 7 existing tables
- [ ] Generate remaining tables (S8-S25)
- [ ] Include all figure references
- [ ] Include mathematical appendix
- [ ] Include parameter sources
- [ ] Validate completeness

### Post-Update
- [ ] Run validation script
- [ ] Generate diff report
- [ ] Review all changes
- [ ] Create change log
- [ ] Archive old versions

---

## 📝 CHANGE LOG FORMAT

```markdown
# Manuscript V5 → V6 Changes

## Summary
- Total changes: XX
- Values updated: XX
- Sections modified: XX
- New content: XX lines

## Detailed Changes

### Methods
- Line 123: Added "semi-Markov model"
- Line 145: Updated therapy list (3 → 10 strategies)

### Results
- Line 234: Updated ECT ICER ($45,000 → $XX,XXX)
- Line 256: Updated CEAC probability (65% → XX%)
- Table 2: All values updated from V4 outputs
- Table 3: All values updated from V4 outputs

### Figures
- Figure 2: Caption updated with V4 abbreviations
- Figure 3: Reference updated to V4 output

## Files Changed
- protocol_v3.md → protocol_v4.md
- manuscript_v5_20251002.md → manuscript_v6_20251010.md
- supplementary_v5.md → supplementary_v6.md
```

---

## 🎯 SUCCESS CRITERIA

### Protocol
- ✓ Model structure accurately reflects V4
- ✓ All 10 therapies listed
- ✓ All V4 analyses mentioned
- ✓ No unnecessary changes

### Manuscript
- ✓ All result values from V4 outputs
- ✓ Therapy abbreviations consistent
- ✓ Minimal narrative changes
- ✓ Structure preserved

### Supplementary
- ✓ All V4 tables included
- ✓ All V4 figures referenced
- ✓ Mathematical appendix complete
- ✓ Parameter sources documented

### Quality
- ✓ No broken references
- ✓ Consistent formatting
- ✓ All changes validated
- ✓ Change log complete

---

## 📊 ESTIMATED EFFORT

| Task | Time | Complexity |
|------|------|------------|
| Extract V4 values | 30 min | Low |
| Scan manuscript | 15 min | Low |
| Create mapping | 45 min | Medium |
| Update protocol | 1 hour | Medium |
| Update manuscript | 2 hours | Medium |
| Update supplementary | 3 hours | High |
| Validation | 1 hour | Medium |
| **Total** | **8-9 hours** | **Medium** |

---

## 🚀 NEXT STEPS

1. **Review this plan** - Confirm approach
2. **Extract V4 values** - Run extraction script
3. **Scan manuscript** - Identify all values to change
4. **Create mapping** - Map old → new values
5. **Execute updates** - Apply surgical changes
6. **Validate** - Verify all changes correct
7. **Review** - Human review of changes
8. **Finalize** - Create final versions

---

**Status**: Plan Complete - Ready for Execution  
**Approach**: Surgical, minimal changes only  
**Risk**: Low (targeted changes, validation at each step)
