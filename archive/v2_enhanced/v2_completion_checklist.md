# V2 CEA Completion Checklist

## Overview
V2 currently includes 4 of 6 required interventions. Missing: ECT and ECT-KA.

## Missing Interventions

### 1. ECT (Standard ECT)

#### Clinical Parameters (clinical_inputs.csv)
- [x] ECT Remission rate (non-psychotic TRD, acute)
- [x] ECT Relapse by 6m (no maintenance)
- [x] ECT Maintenance usage rate
- [x] ECT Maintenance relapse (annual)
- [x] ECT Adherence Rate

#### Cost Data (cost_inputs_au.csv & cost_inputs_nz.csv)
- [x] ECT psychiatrist fee (AU)
- [x] ECT anesthesia fee (AU)
- [x] ECT total session cost (AU)
- [x] ECT course sessions count
- [x] ECT psychiatrist fee (NZ)
- [x] ECT anesthesia fee (NZ)
- [x] ECT total session cost (NZ)#### PSA Parameters (parameters_psa.csv)
- [x] ECT remission distribution
- [x] ECT relapse 6m distribution
- [x] ECT maintenance use distribution
- [x] ECT maintenance relapse distribution
- [x] ECT cost distributions (AU & NZ)

#### Strategy Configuration (strategies.yml)
- [x] Add ECT strategy mapping
- [x] Update strategy labels for ECT

### 2. ECT-KA (ECT with Ketamine Anaesthetic)

#### Clinical Parameters (clinical_inputs.csv)
- [x] ECT-KA Remission rate (non-psychotic TRD, acute)
- [x] ECT-KA Relapse by 6m (no maintenance)
- [x] ECT-KA Maintenance usage rate
- [x] ECT-KA Maintenance relapse (annual)
- [x] ECT-KA Adherence Rate

#### Cost Data (cost_inputs_au.csv & cost_inputs_nz.csv)
- [x] ECT-KA psychiatrist fee (AU)
- [x] ECT-KA anesthesia fee (AU)
- [x] ECT-KA ketamine drug cost (AU)
- [x] ECT-KA total session cost (AU)
- [x] ECT-KA course sessions count
- [x] ECT-KA psychiatrist fee (NZ)
- [x] ECT-KA anesthesia fee (NZ)
- [x] ECT-KA ketamine drug cost (NZ)
- [x] ECT-KA total session cost (NZ)

#### PSA Parameters (parameters_psa.csv)
- [x] ECT-KA remission distribution
- [x] ECT-KA relapse 6m distribution
- [x] ECT-KA maintenance use distribution
- [x] ECT-KA maintenance relapse distribution
- [x] ECT-KA cost distributions (AU & NZ)

#### Strategy Configuration (strategies.yml)
- [x] Add ECT-KA strategy mapping
- [x] Update strategy labels for ECT-KA

## Data Integration

### PSA Data Updates (psa_extended.csv)
- [x] Add ECT strategy data for all perspectives
- [x] Add ECT-KA strategy data for all perspectives
- [x] Ensure proper draw alignment across strategies

### Analysis Pipeline Updates
- [x] Update analysis_v2 pipeline to handle 6 strategies
- [x] Verify CE plane generation for all interventions
- [x] Verify CEAF, VBP, and other outputs for all interventions

## Validation Steps

### Data Completeness
- [x] Verify all clinical parameters have AU/NZ values
- [x] Verify all cost data has 2024 values
- [x] Verify all PSA parameters have distributions
- [x] Verify strategy configuration includes all 6 interventions

### Analysis Validation
- [x] Run v2 pipeline successfully with all 6 interventions
- [x] Verify CE planes generated for all intervention pairs
- [x] Verify PSA results include all interventions
- [x] Verify cost-effectiveness outputs complete

### Integration Testing
- [ ] Run full v2 orchestration with all interventions
- [ ] Verify labeling works for all 6 interventions
- [ ] Verify outputs generated for all intervention comparisons
- [ ] Verify data quality checks pass

## Completion Criteria

- [ ] All 6 interventions (ECT, ECT-KA, IV_ketamine, Esketamine, Psilocybin, Oral_ketamine) included
- [ ] All interventions properly configured in strategies.yml
- [ ] All data sources documented and validated
- [ ] Full CEA analysis runs successfully for all interventions
- [ ] V2 pipeline produces complete comparative output set</content>
<parameter name="filePath">v2_completion_checklist.md