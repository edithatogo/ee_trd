# V3 CEA Completion Checklist

## Overview
V3 currently includes 4 of 6 required interventions. Missing: KA_ECT and Oral Ketamine.

## Missing Interventions

### 1. ECT_ket_anaesthetic (KA_ECT) - ECT + ketamine (IV anaesthetic)

#### Clinical Parameters (clinical_inputs.csv)
- [ ] ECT + Ketamine Remission rate (non-psychotic TRD, acute)
- [ ] ECT + Ketamine Relapse by 6m (no maintenance)
- [ ] ECT + Ketamine Maintenance usage rate
- [ ] ECT + Ketamine Maintenance relapse (annual)
- [ ] ECT + Ketamine Adherence Rate

#### Cost Data (cost_inputs_au.csv & cost_inputs_nz.csv)
- [ ] ECT + Ketamine psychiatrist fee (AU)
- [ ] ECT + Ketamine anesthesia fee (AU) 
- [ ] ECT + Ketamine total session cost (AU)
- [ ] ECT + Ketamine course sessions count
- [ ] ECT + Ketamine psychiatrist fee (NZ)
- [ ] ECT + Ketamine anesthesia fee (NZ)
- [ ] ECT + Ketamine total session cost (NZ)

#### PSA Parameters (parameters_psa.csv)
- [ ] ECT + Ketamine remission distribution
- [ ] ECT + Ketamine relapse 6m distribution
- [ ] ECT + Ketamine maintenance use distribution
- [ ] ECT + Ketamine maintenance relapse distribution
- [ ] ECT + Ketamine cost distributions (AU & NZ)

#### Configuration Updates
- [ ] Add "ECT_ket_anaesthetic" to arms list in settings.yaml

### 2. Oral_ketamine - Ketamine (oral)

#### Clinical Parameters (clinical_inputs.csv)
- [ ] Oral Ketamine Remission rate (4 weeks)
- [ ] Oral Ketamine Relapse on maintenance (~4 months)
- [ ] Oral Ketamine Relapse off maintenance (1 year)
- [ ] Oral Ketamine Adherence Rate

#### Cost Data (cost_inputs_au.csv & cost_inputs_nz.csv)
- [ ] Oral Ketamine session drug cost (AU)
- [ ] Oral Ketamine session admin/monitoring cost (AU)
- [ ] Oral Ketamine total session cost (AU)
- [ ] Oral Ketamine session drug cost (NZ)
- [ ] Oral Ketamine session admin/monitoring cost (NZ)
- [ ] Oral Ketamine total session cost (NZ)

#### PSA Parameters (parameters_psa.csv)
- [ ] Oral Ketamine remission distribution
- [ ] Oral Ketamine relapse on maintenance distribution
- [ ] Oral Ketamine relapse off maintenance distribution
- [ ] Oral Ketamine cost distributions (AU & NZ)

#### Configuration Updates
- [ ] Add "Oral_ketamine" to arms list in settings.yaml

## Data Schema Updates Required

### DCEA Groups & Weights
- [ ] Update dcea_groups.csv with KA_ECT and Oral Ketamine population shares
- [ ] Update dcea_weights.csv with KA_ECT and Oral Ketamine equity weights

### MCDA Data
- [ ] Update mcda_weights.csv with KA_ECT and Oral Ketamine weights
- [ ] Update mcda_value_functions.csv with KA_ECT and Oral Ketamine functions

### Provenance Data
- [ ] Update provenance_sources.csv with KA_ECT and Oral Ketamine data sources
- [ ] Update grade_certainty.csv with KA_ECT and Oral Ketamine certainty grades

## Validation Steps

### Data Completeness
- [ ] Verify all clinical parameters have AU/NZ values
- [ ] Verify all cost data has 2024 values
- [ ] Verify all PSA parameters have distributions
- [ ] Verify all data sources are documented

### Configuration Validation
- [ ] Run v3 sourcing pipeline successfully
- [ ] Run v3 CEA with all 6 arms
- [ ] Run v3 PSA with all 6 arms
- [ ] Run v3 DCEA with all 6 arms

### Integration Testing
- [ ] Run full orchestration with all interventions
- [ ] Verify labeling works for all 6 arms
- [ ] Verify outputs generated for all interventions
- [ ] Verify data quality checks pass

## Completion Criteria

- [ ] All 6 interventions (ECT_std, ECT_ket_anaesthetic, IV_ketamine, Esketamine, Psilocybin, Oral_ketamine) included
- [ ] All interventions properly labeled with route tokens
- [ ] All data sources documented and validated
- [ ] Full CEA analysis runs successfully for all interventions
- [ ] Orchestration system produces complete output set
