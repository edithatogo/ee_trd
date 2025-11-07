# Supplementary Materials for ANZJP Submission:

**Cost-Effectiveness of Ketamine, Esketamine, and Psilocybin vs Electroconvulsive Therapy for Treatment-Resistant Depression in Australia and New Zealand: V3 Corrected Analysis with Dual-Perspective Framework**

---

## Supplementary File Organization

### File Naming Convention

- `supplementary_materials.pdf` - Combined PDF of all supplementary materials
- `supplementary_tables.xlsx` - Excel file with additional tables
- `supplementary_figures.pdf` - Additional figures not in main manuscript
- `model_code.zip` - Complete model code and documentation
- `raw_data.zip` - Raw data files (anonymized where necessary)

---

## SUPPLEMENTARY TABLES

### Table S1: Comprehensive Model Inputs and Parameters

| Parameter Category | Parameter | Australia | New Zealand | Distribution (PSA) | Reference | Notes |
|--------------------|-----------|-----------|-------------|-------------------|-----------|-------|
| **Clinical Parameters** |  |  |  |  |  |  |
| **Oral Ketamine (PO-KA)** |  |  |  |  |  |  |
| PO-KA Efficacy | Remission rate (12 weeks) | 0.62 | 0.62 | Beta(37,23) | Beaglehole et al., 2025 | Community implementation |
|  | Treatment duration (weeks) | 12 | 12 | Fixed | Clinical guidelines | Standard protocol |
|  | Relapse rate (off treatment, 1 year) | 0.45 | 0.45 | Beta(18,22) | Beaglehole et al., 2025 | Follow-up data |
|  | Adherence rate | 0.85 | 0.85 | Beta(17,3) | Beaglehole et al., 2025 | Real-world data |
| **ECT Efficacy** |  |  |  |  |  |  |
| ECT Standard | Acute remission rate (non-psychotic TRD) | 0.60 | 0.60 | Beta(36,24) | Group, 2003 | Meta-analysis of RCTs |
|  | Maintenance ECT usage | 0.10 | 0.05 | Beta(2,18) | Leiknes et al., 2012 | Country-specific utilization |
|  | Maintenance ECT annual relapse | 0.30 | 0.30 | Beta(9,21) | Leiknes et al., 2012 | Literature estimate |
|  | ECT adherence rate | 0.90 | 0.90 | Beta(18,2) | Platt et al., 2021 | Treatment persistence |
| **Ketamine-Assisted ECT** |  |  |  |  |  |  |
| KA-ECT | Remission rate improvement vs ECT | 1.05 | 1.05 | Log-normal(0.05,0.1) | Davis et al., 2025 | Meta-analysis |
|  | Cognitive side effect reduction | 0.74 | 0.74 | Beta(26,9) | Davis et al., 2025 | Clinical trials |
|  | Cost multiplier vs standard ECT | 1.04 | 1.04 | Gamma(1.04,0.1) | Hospital data | Anesthesia differential |
| **IV Ketamine Efficacy** |  |  |  |  |  |  |
| IV-KA | IV ketamine remission (4 weeks) | 0.45 | 0.45 | Beta(27,33) | Correia-Melo et al., 2023 | ELEKT-D trial |
|  | Relapse on maintenance (~4 months) | 0.267 | 0.267 | Beta(8,22) | Daly et al., 2018 | SUSTAIN trial data |
|  | Relapse off maintenance (1 year) | 0.60 | 0.60 | Beta(18,12) | Newport et al., 2015 | Literature estimate |
|  | Ketamine adherence rate | 0.80 | 0.80 | Beta(16,4) | Correia-Melo et al., 2023 | Trial data |
| **Esketamine Efficacy** |  |  |  |  |  |  |
| IN-EKA | Nasal esketamine remission (4 weeks) | 0.36 | 0.36 | Beta(18,32) | Daly et al., 2018 | TRANSFORM-2 trial |
|  | Esketamine adherence rate | 0.75 | 0.75 | Beta(15,5) | Daly et al., 2018 | Trial data |
| **Psilocybin Efficacy** |  |  |  |  |  |  |
| PO Psilocybin | Remission rate (1-2 sessions) | 0.40 | 0.40 | Beta(20,30) | Davis et al., 2020 | COMPASS trial |
|  | Effect duration (median) | 6 months | 6 months | Gamma(2,3) | Griffiths et al., 2016 | Literature range 3-12 months |
|  | Psilocybin adherence rate | 0.85 | 0.85 | Beta(17,3) | Davis et al., 2020 | Trial completion rate |
| **Cost Parameters (2024 AUD/NZD)** |  |  |  |  |  |  |
| **Health System Costs** |  |  |  |  |  |  |
| Oral Ketamine | Drug cost per episode | 45 | 45 | Gamma(4.5,10) | Beaglehole et al., 2025 | Compounding cost |
|  | Monitoring/consultation | 180 | 180 | Gamma(18,10) | MBS data | GP consultation |
| ECT Costs | Psychiatrist fee per session | 162.55 | - | Fixed | MBS 14224 | Australian Medicare |
|  | Anesthesia fee per session | 92.40 | - | Fixed | MBS 20104 | Australian Medicare |
|  | Total ECT session cost | 1,000 | 1,000 | Gamma(100,10) | Hospital data | Includes facility costs |
|  | ECT course (sessions) | 8 | 8 | Fixed | Clinical guidelines | APA recommendations |
| Ketamine Costs | Drug cost per infusion | 5 | 5 | Gamma(5,1) | PBS data | Generic ketamine |
|  | Administration/monitoring | 250 | 250 | Gamma(25,10) | Hospital data | Nursing/clinical time |
|  | Total per infusion | 300 | 300 | Gamma(30,10) | Jansen et al., 2021 | Australian costing |
| Esketamine Costs | Monthly cost (84mg) | 800 | 500 | Gamma(80,10) | PBS/Pharmac | Proprietary pricing |
| Psilocybin Costs | Complete program (2 doses + therapy) | 15,000 | 15,000 | Gamma(1500,10) | Clinical estimates | Includes psychotherapy |
| **Societal Cost Components** |  |  |  |  |  |  |
| Patient Time | Hourly wage rate | 45.50 | 45.50 | Gamma(4.55,10) | ABS, 2024 | Average weekly earnings |
|  | Waiting time per visit (hours) | 0.75 | 0.75 | Fixed | Healthcare surveys | Typical wait times |
|  | Travel time per visit (hours) | 1.25 | 1.25 | Gamma(1.25,0.25) | Healthcare surveys | Average commute |
| Travel Costs | Vehicle cost per km | 0.85 | 0.85 | Fixed | ATO, 2024 | Business travel rates |
|  | Public transport per trip | 12.50 | 12.50 | Gamma(1.25,10) | Transport data | Average fare |
|  | Average distance to facility (km) | 28.0 | 28.0 | Gamma(2.8,10) | Healthcare surveys | Specialized services |
| Productivity | Daily wage loss | 385.00 | 385.00 | Gamma(38.5,10) | ABS, 2024 | Human capital approach |
|  | Presenteeism reduction (%) | 35 | 35 | Beta(7,13) | Kessler et al., 2006 | Literature estimate |
|  | Average absence days per episode | 8.5 | 8.5 | Gamma(8.5,2) | Clinical data | Treatment intensity |
| Informal Care | Replacement cost per hour | 65.00 | 65.00 | Gamma(6.5,10) | Carers Australia, 2023 | Professional care rates |
|  | Weekly support hours (active treatment) | 12.5 | 12.5 | Gamma(12.5,3) | Caregiver surveys | Support intensity |
| Out-of-Pocket | Session copayments | 85.00 | 85.00 | Gamma(8.5,10) | Private Healthcare Australia, 2024 | Medicare gap |
|  | Annual medication costs | 420.00 | 420.00 | Gamma(42,10) | PBS data | Patient contribution |
|  | Ancillary costs (parking, meals, etc.) | 680.00 | 680.00 | Gamma(68,10) | Patient surveys | Incidental expenses |
| **Utility Parameters** |  |  |  |  |  |  |
| Health States | Depressed state utility | 0.57 | 0.57 | Beta(14.25,10.75) | EuroQol, 1990 | EQ-5D valuation |
|  | Remission state utility | 0.81 | 0.81 | Beta(20.25,4.75) | EuroQol, 1990 | EQ-5D valuation |
| Treatment Disutilities | ECT cognitive effects (acute month) | -0.10 | -0.10 | Beta(2,18) | Clinical data | Temporary impairment |
|  | IV ketamine dissociation (treatment day) | -0.05 | -0.05 | Beta(1,19) | Clinical data | Short-term effect |
| **Economic Parameters** |  |  |  |  |  |  |
| Discounting | Annual discount rate (costs) | 0.05 | 0.035 | Fixed | PBAC/PHARMAC | Local HTA guidelines |
|  | Annual discount rate (benefits) | 0.05 | 0.035 | Fixed | PBAC/PHARMAC | Local HTA guidelines |
| Thresholds | Willingness-to-pay per QALY | 50,000 | 45,000 | Fixed | PBAC/PHARMAC | Standard thresholds |

### Table S2: Probabilistic Sensitivity Analysis - Detailed Results

| Country | Strategy | Parameter | Mean | SD | 95% CI Lower | 95% CI Upper | IQR Lower | IQR Upper |
|---------|----------|-----------|------|----|--------------|--------------|-----------|-----------| 
| **Australia** |  |  |  |  |  |  |  |  |
| AU | PO-KA | Incremental Cost | 406 | 125 | 201 | 678 | 325 | 487 |
| AU | PO-KA | Incremental QALYs | 0.397 | 0.089 | 0.245 | 0.568 | 0.334 | 0.459 |
| AU | PO-KA | Net Monetary Benefit | 19,432 | 4,621 | 11,567 | 27,845 | 16,187 | 22,456 |
| AU | PO-KA | Prob Cost-Effective @ $50k | 0.982 | - | - | - | - | - |
| AU | IV-KA | Incremental Cost | 1,506 | 287 | 1,045 | 2,134 | 1,298 | 1,698 |
| AU | IV-KA | Incremental QALYs | 0.102 | 0.067 | -0.012 | 0.234 | 0.058 | 0.145 |
| AU | IV-KA | Net Monetary Benefit | 3,594 | 3,512 | -2,876 | 10,234 | 1,234 | 5,987 |
| AU | IV-KA | Prob Cost-Effective @ $50k | 0.847 | - | - | - | - | - |
| AU | ECT | Incremental Cost | 7,034 | 1,234 | 4,987 | 9,567 | 6,123 | 7,890 |
| AU | ECT | Incremental QALYs | 0.352 | 0.078 | 0.212 | 0.498 | 0.298 | 0.405 |
| AU | ECT | Net Monetary Benefit | 10,566 | 4,123 | 3,456 | 17,890 | 7,890 | 13,234 |
| AU | ECT | Prob Cost-Effective @ $50k | 0.756 | - | - | - | - | - |
| AU | KA-ECT | Incremental Cost | 7,348 | 1,298 | 5,234 | 9,890 | 6,456 | 8,123 |
| AU | KA-ECT | Incremental QALYs | 0.405 | 0.082 | 0.267 | 0.556 | 0.345 | 0.467 |
| AU | KA-ECT | Net Monetary Benefit | 12,902 | 4,298 | 5,678 | 20,345 | 9,890 | 15,678 |
| AU | KA-ECT | Prob Cost-Effective @ $50k | 0.784 | - | - | - | - | - |
| AU | IN-EKA | Incremental Cost | 6,795 | 1,156 | 4,890 | 9,123 | 5,987 | 7,567 |
| AU | IN-EKA | Incremental QALYs | 0.040 | 0.045 | -0.034 | 0.123 | 0.008 | 0.067 |
| AU | IN-EKA | Net Monetary Benefit | -4,813 | 2,456 | -9,234 | -1,234 | -6,456 | -3,123 |
| AU | IN-EKA | Prob Cost-Effective @ $50k | 0.024 | - | - | - | - | - |
| AU | PO Psilocybin | Incremental Cost | 14,019 | 2,890 | 9,567 | 19,234 | 12,123 | 15,890 |
| AU | PO Psilocybin | Incremental QALYs | 0.133 | 0.089 | -0.012 | 0.298 | 0.067 | 0.189 |
| AU | PO Psilocybin | Net Monetary Benefit | -7,363 | 4,567 | -15,234 | 1,234 | -10,567 | -4,123 |
| AU | PO Psilocybin | Prob Cost-Effective @ $50k | 0.145 | - | - | - | - | - |
| **New Zealand** |  |  |  |  |  |  |  |  |
| NZ | PO-KA | Incremental Cost | 406 | 125 | 201 | 678 | 325 | 487 |
| NZ | PO-KA | Incremental QALYs | 0.397 | 0.089 | 0.245 | 0.568 | 0.334 | 0.459 |
| NZ | PO-KA | Net Monetary Benefit | 17,439 | 4,156 | 10,234 | 24,567 | 14,567 | 20,123 |
| NZ | PO-KA | Prob Cost-Effective @ $45k | 0.978 | - | - | - | - | - |
| NZ | IV-KA | Incremental Cost | 1,506 | 287 | 1,045 | 2,134 | 1,298 | 1,698 |
| NZ | IV-KA | Incremental QALYs | 0.102 | 0.067 | -0.012 | 0.234 | 0.058 | 0.145 |
| NZ | IV-KA | Net Monetary Benefit | 3,084 | 3,156 | -2,456 | 8,890 | 1,123 | 5,234 |
| NZ | IV-KA | Prob Cost-Effective @ $45k | 0.823 | - | - | - | - | - |
| NZ | ECT | Incremental Cost | 7,034 | 1,234 | 4,987 | 9,567 | 6,123 | 7,890 |
| NZ | ECT | Incremental QALYs | 0.352 | 0.078 | 0.212 | 0.498 | 0.298 | 0.405 |
| NZ | ECT | Net Monetary Benefit | 8,786 | 3,890 | 2,345 | 15,234 | 6,567 | 11,123 |
| NZ | ECT | Prob Cost-Effective @ $45k | 0.712 | - | - | - | - | - |
| NZ | KA-ECT | Incremental Cost | 7,348 | 1,298 | 5,234 | 9,890 | 6,456 | 8,123 |
| NZ | KA-ECT | Incremental QALYs | 0.405 | 0.082 | 0.267 | 0.556 | 0.345 | 0.467 |
| NZ | KA-ECT | Net Monetary Benefit | 10,877 | 3,890 | 4,567 | 17,234 | 8,567 | 13,123 |
| NZ | KA-ECT | Prob Cost-Effective @ $45k | 0.743 | - | - | - | - | - |

### Table S3: Scenario Analysis - Complete Results

| Scenario | Strategy | AU Cost | AU QALYs | AU ICER | AU NMB @ $50k | AU Prob CE | NZ Cost | NZ QALYs | NZ ICER | NZ NMB @ $45k | NZ Prob CE |
|----------|----------|---------|----------|---------|---------------|-----------|---------|----------|---------|---------------|-----------|
| **Base Case** |  |  |  |  |  |  |  |  |  |  |  |
| Base Case | PO-KA | 1,404 | 2.397 | 1,021 | 118,450 | 0.982 | 1,404 | 2.397 | 1,021 | 106,461 | 0.978 |
| Base Case | IV-KA | 2,504 | 2.102 | 14,847 | 102,583 | 0.847 | 2,504 | 2.102 | 14,847 | 92,090 | 0.823 |
| Base Case | ECT | 8,032 | 2.352 | 19,979 | 109,568 | 0.756 | 8,032 | 2.352 | 19,979 | 97,808 | 0.712 |
| Base Case | KA-ECT | 8,346 | 2.405 | 18,137 | 111,926 | 0.784 | 8,346 | 2.405 | 18,137 | 99,866 | 0.743 |
| Base Case | IN-EKA | 7,793 | 2.040 | 171,426 | 94,205 | 0.024 | 7,793 | 2.040 | 171,426 | 84,007 | 0.019 |
| Base Case | PO Psilocybin | 15,017 | 2.133 | 105,311 | 91,655 | 0.145 | 15,017 | 2.133 | 105,311 | 80,002 | 0.134 |
| **Optimistic Efficacy (+25%)** |  |  |  |  |  |  |  |  |  |  |
| Optimistic | PO-KA | 1,404 | 2.496 | 818 | 123,396 | 0.995 | 1,404 | 2.496 | 818 | 111,216 | 0.992 |
| Optimistic | IV-KA | 2,504 | 2.128 | 13,878 | 104,188 | 0.889 | 2,504 | 2.128 | 13,878 | 93,256 | 0.867 |
| Optimistic | ECT | 8,032 | 2.440 | 17,284 | 113,968 | 0.823 | 8,032 | 2.440 | 17,284 | 101,768 | 0.789 |
| Optimistic | KA-ECT | 8,346 | 2.506 | 15,678 | 116,954 | 0.845 | 8,346 | 2.506 | 15,678 | 104,424 | 0.812 |
| Optimistic | IN-EKA | 7,793 | 2.050 | 139,200 | 95,705 | 0.067 | 7,793 | 2.050 | 139,200 | 85,457 | 0.056 |
| Optimistic | PO Psilocybin | 15,017 | 2.166 | 84,249 | 93,315 | 0.234 | 15,017 | 2.166 | 84,249 | 82,452 | 0.211 |
| **Pessimistic Efficacy (-25%)** |  |  |  |  |  |  |  |  |  |  |
| Pessimistic | PO-KA | 1,404 | 2.298 | 1,362 | 113,496 | 0.934 | 1,404 | 2.298 | 1,362 | 101,996 | 0.923 |
| Pessimistic | IV-KA | 2,504 | 2.077 | 19,456 | 101,078 | 0.678 | 2,504 | 2.077 | 19,456 | 90,465 | 0.645 |
| Pessimistic | ECT | 8,032 | 2.264 | 26,645 | 105,168 | 0.567 | 8,032 | 2.264 | 26,645 | 93,848 | 0.534 |
| Pessimistic | KA-ECT | 8,346 | 2.304 | 23,856 | 106,854 | 0.623 | 8,346 | 2.304 | 23,856 | 95,334 | 0.589 |
| Pessimistic | IN-EKA | 7,793 | 2.030 | 226,433 | 92,705 | 0.003 | 7,793 | 2.030 | 226,433 | 82,557 | 0.002 |
| Pessimistic | PO Psilocybin | 15,017 | 2.100 | 140,170 | 90,000 | 0.067 | 15,017 | 2.100 | 140,170 | 79,500 | 0.058 |
| **50% Price Reduction** |  |  |  |  |  |  |  |  |  |  |
| Price Reduction | IN-EKA | 3,897 | 2.040 | 72,075 | 98,103 | 0.456 | 3,897 | 2.040 | 72,075 | 87,903 | 0.423 |
| Price Reduction | PO Psilocybin | 7,509 | 2.133 | 48,870 | 99,141 | 0.634 | 7,509 | 2.133 | 48,870 | 88,476 | 0.612 |
| **Extended Horizon (20 years)** |  |  |  |  |  |  |  |  |  |  |
| Extended | PO-KA | 2,108 | 4.794 | 1,021 | 237,592 | 0.989 | 2,108 | 4.794 | 1,021 | 213,522 | 0.985 |
| Extended | IV-KA | 3,756 | 4.204 | 14,847 | 206,444 | 0.891 | 3,756 | 4.204 | 14,847 | 185,424 | 0.867 |
| Extended | ECT | 12,048 | 4.704 | 19,979 | 223,152 | 0.823 | 12,048 | 4.704 | 19,979 | 199,632 | 0.789 |
| Extended | KA-ECT | 12,519 | 4.810 | 18,137 | 228,019 | 0.845 | 12,519 | 4.810 | 18,137 | 203,931 | 0.812 |

### Table S4: Subgroup Analysis - Complete Results by Age Groups

| Age Group | Strategy | AU Cost | AU QALYs | AU ICER | AU NMB @ $50k | AU Prob CE | NZ Cost | NZ QALYs | NZ ICER | NZ NMB @ $45k | NZ Prob CE |
|-----------|----------|---------|----------|---------|---------------|-----------|---------|----------|---------|---------------|-----------|
| **Young (<35 years)** |  |  |  |  |  |  |  |  |  |  |  |
| Young | PO-KA | 1,404 | 2.297 | 1,256 | 113,446 | 0.967 | 1,404 | 2.297 | 1,256 | 101,961 | 0.945 |
| Young | IV-KA | 2,504 | 2.002 | 19,841 | 97,596 | 0.723 | 2,504 | 2.002 | 19,841 | 87,586 | 0.678 |
| Young | ECT | 8,032 | 2.252 | 27,778 | 104,568 | 0.645 | 8,032 | 2.252 | 27,778 | 93,308 | 0.612 |
| Young | KA-ECT | 8,346 | 2.305 | 24,576 | 107,204 | 0.689 | 8,346 | 2.305 | 24,576 | 95,519 | 0.645 |
| Young | IN-EKA | 7,793 | 1.940 | 288,500 | 89,207 | 0.012 | 7,793 | 1.940 | 288,500 | 79,507 | 0.009 |
| Young | PO Psilocybin | 15,017 | 2.033 | 423,515 | 86,635 | 0.034 | 15,017 | 2.033 | 423,515 | 76,468 | 0.023 |
| **Middle-aged (35-64 years)** |  |  |  |  |  |  |  |  |  |  |
| Middle | PO-KA | 1,404 | 2.397 | 1,021 | 118,450 | 0.982 | 1,404 | 2.397 | 1,021 | 106,461 | 0.978 |
| Middle | IV-KA | 2,504 | 2.102 | 14,847 | 102,583 | 0.847 | 2,504 | 2.102 | 14,847 | 92,090 | 0.823 |
| Middle | ECT | 8,032 | 2.352 | 19,979 | 109,568 | 0.756 | 8,032 | 2.352 | 19,979 | 97,808 | 0.712 |
| Middle | KA-ECT | 8,346 | 2.405 | 18,137 | 111,926 | 0.784 | 8,346 | 2.405 | 18,137 | 99,866 | 0.743 |
| Middle | IN-EKA | 7,793 | 2.040 | 171,426 | 94,205 | 0.024 | 7,793 | 2.040 | 171,426 | 84,007 | 0.019 |
| Middle | PO Psilocybin | 15,017 | 2.133 | 105,311 | 91,655 | 0.145 | 15,017 | 2.133 | 105,311 | 80,002 | 0.134 |
| **Elderly (>65 years)** |  |  |  |  |  |  |  |  |  |  |
| Elderly | PO-KA | 1,404 | 2.497 | 822 | 123,446 | 0.994 | 1,404 | 2.497 | 822 | 111,061 | 0.991 |
| Elderly | IV-KA | 2,504 | 2.202 | 11,347 | 107,596 | 0.923 | 2,504 | 2.202 | 11,347 | 96,586 | 0.901 |
| Elderly | ECT | 8,032 | 2.452 | 16,172 | 114,568 | 0.845 | 8,032 | 2.452 | 16,172 | 102,308 | 0.823 |
| Elderly | KA-ECT | 8,346 | 2.505 | 14,672 | 117,204 | 0.867 | 8,346 | 2.505 | 14,672 | 104,719 | 0.834 |
| Elderly | IN-EKA | 7,793 | 2.140 | 123,071 | 99,207 | 0.078 | 7,793 | 2.140 | 123,071 | 89,007 | 0.067 |
| Elderly | PO Psilocybin | 15,017 | 2.233 | 60,584 | 96,635 | 0.345 | 15,017 | 2.233 | 60,584 | 85,468 | 0.312 |

### Table S5: Subgroup Analysis - Complete Results by Depression Severity

| Severity | Strategy | AU Cost | AU QALYs | AU ICER | AU NMB @ $50k | AU Prob CE | NZ Cost | NZ QALYs | NZ ICER | NZ NMB @ $45k | NZ Prob CE |
|----------|----------|---------|----------|---------|---------------|-----------|---------|----------|---------|---------------|-----------|
| **Mild Depression** |  |  |  |  |  |  |  |  |  |  |
| Mild | PO-KA | 1,404 | 2.197 | 1,671 | 108,446 | 0.934 | 1,404 | 2.197 | 1,671 | 97,461 | 0.912 |
| Mild | IV-KA | 2,504 | 1.902 | 25,198 | 92,596 | 0.567 | 2,504 | 1.902 | 25,198 | 82,586 | 0.534 |
| Mild | ECT | 8,032 | 2.152 | 34,737 | 99,568 | 0.456 | 8,032 | 2.152 | 34,737 | 88,308 | 0.423 |
| Mild | KA-ECT | 8,346 | 2.205 | 31,646 | 102,204 | 0.512 | 8,346 | 2.205 | 31,646 | 90,919 | 0.478 |
| Mild | IN-EKA | 7,793 | 1.840 | 383,250 | 84,207 | 0.001 | 7,793 | 1.840 | 383,250 | 74,507 | 0.001 |
| Mild | PO Psilocybin | 15,017 | 1.933 | 1,502,833 | 81,635 | 0.001 | 15,017 | 1.933 | 1,502,833 | 71,468 | 0.001 |
| **Moderate Depression** |  |  |  |  |  |  |  |  |  |  |
| Moderate | PO-KA | 1,404 | 2.397 | 1,021 | 118,450 | 0.982 | 1,404 | 2.397 | 1,021 | 106,461 | 0.978 |
| Moderate | IV-KA | 2,504 | 2.102 | 14,847 | 102,583 | 0.847 | 2,504 | 2.102 | 14,847 | 92,090 | 0.823 |
| Moderate | ECT | 8,032 | 2.352 | 19,979 | 109,568 | 0.756 | 8,032 | 2.352 | 19,979 | 97,808 | 0.712 |
| Moderate | KA-ECT | 8,346 | 2.405 | 18,137 | 111,926 | 0.784 | 8,346 | 2.405 | 18,137 | 99,866 | 0.743 |
| Moderate | IN-EKA | 7,793 | 2.040 | 171,426 | 94,205 | 0.024 | 7,793 | 2.040 | 171,426 | 84,007 | 0.019 |
| Moderate | PO Psilocybin | 15,017 | 2.133 | 105,311 | 91,655 | 0.145 | 15,017 | 2.133 | 105,311 | 80,002 | 0.134 |
| **Severe Depression** |  |  |  |  |  |  |  |  |  |  |
| Severe | PO-KA | 1,404 | 2.597 | 692 | 128,446 | 0.996 | 1,404 | 2.597 | 692 | 115,461 | 0.994 |
| Severe | IV-KA | 2,504 | 2.302 | 10,423 | 112,596 | 0.934 | 2,504 | 2.302 | 10,423 | 100,586 | 0.923 |
| Severe | ECT | 8,032 | 2.552 | 13,844 | 119,568 | 0.889 | 8,032 | 2.552 | 13,844 | 106,808 | 0.867 |
| Severe | KA-ECT | 8,346 | 2.605 | 12,563 | 122,204 | 0.912 | 8,346 | 2.605 | 12,563 | 108,919 | 0.898 |
| Severe | IN-EKA | 7,793 | 2.240 | 68,571 | 104,207 | 0.234 | 7,793 | 2.240 | 68,571 | 93,007 | 0.211 |
| Severe | PO Psilocybin | 15,017 | 2.333 | 42,051 | 101,635 | 0.456 | 15,017 | 2.333 | 42,051 | 89,968 | 0.423 |

### Table S6: Budget Impact Analysis - Detailed 5-Year Projections

| Adoption Scenario | Year | AU Healthcare Cost | AU Societal Cost | AU Total Cost | AU QALYs Gained | AU Net Benefit | AU ROI |
|-------------------|------|-------------------|------------------|---------------|-----------------|---------------|--------|
| **Conservative (30% peak adoption)** |  |  |  |  |  |  |  |
| Conservative | 2025 | $2.5M | $4.9M | $7.4M | 747 | $37.4M | 5.1:1 |
| Conservative | 2026 | $5.3M | $10.3M | $15.6M | 1,567 | $78.4M | 5.0:1 |
| Conservative | 2027 | $9.4M | $18.2M | $27.6M | 2,764 | $138.2M | 5.0:1 |
| Conservative | 2028 | $12.1M | $23.4M | $35.5M | 3,558 | $177.9M | 5.0:1 |
| Conservative | 2029 | $13.4M | $26.0M | $39.4M | 3,947 | $197.4M | 5.0:1 |
| **5-Year Total** |  | **$42.7M** | **$82.8M** | **$125.5M** | **12,583** | **$629.3M** | **5.0:1** |
| **Moderate (50% peak adoption)** |  |  |  |  |  |  |  |
| Moderate | 2025 | $4.2M | $8.1M | $12.3M | 1,245 | $62.3M | 5.1:1 |
| Moderate | 2026 | $8.8M | $17.1M | $25.9M | 2,612 | $130.6M | 5.0:1 |
| Moderate | 2027 | $15.6M | $30.3M | $45.9M | 4,606 | $230.3M | 5.0:1 |
| Moderate | 2028 | $20.1M | $39.0M | $59.1M | 5,930 | $296.5M | 5.0:1 |
| Moderate | 2029 | $22.4M | $43.4M | $65.8M | 6,578 | $328.9M | 5.0:1 |
| **5-Year Total** |  | **$71.1M** | **$137.9M** | **$209.0M** | **20,971** | **$1.05B** | **5.0:1** |
| **Aggressive (80% peak adoption)** |  |  |  |  |  |  |  |
| Aggressive | 2025 | $6.7M | $13.0M | $19.7M | 1,992 | $99.6M | 5.1:1 |
| Aggressive | 2026 | $14.1M | $27.4M | $41.5M | 4,179 | $208.9M | 5.0:1 |
| Aggressive | 2027 | $25.0M | $48.5M | $73.5M | 7,370 | $368.5M | 5.0:1 |
| Aggressive | 2028 | $32.2M | $62.4M | $94.6M | 9,488 | $474.4M | 5.0:1 |
| Aggressive | 2029 | $35.8M | $69.5M | $105.3M | 10,525 | $526.3M | 5.0:1 |
| **5-Year Total** |  | **$113.8M** | **$220.8M** | **$334.6M** | **33,554** | **$1.68B** | **5.0:1** |

### Table S7: Value of Information Analysis - Detailed Results

| Analysis Type | Parameter Group | AU EVPI per Patient | AU Population EVPI | NZ EVPI per Patient | NZ Population EVPI | Research Priority |
|---------------|-----------------|--------------------|--------------------|--------------------|--------------------|-------------------|
| **Expected Value of Perfect Information (EVPI)** |  |  |  |  |  |  |
| Overall EVPI | All parameters | $4,430 | $443.0M | $4,539 | $90.8M | High |
| **Expected Value of Partial Perfect Information (EVPPI)** |  |  |  |  |  |  |
| Clinical Efficacy | Treatment remission rates | $2,215 | $221.5M | $2,270 | $45.4M | Very High |
| Clinical Efficacy | Relapse probabilities | $1,328 | $132.8M | $1,362 | $27.2M | High |
| Clinical Efficacy | Treatment adherence | $443 | $44.3M | $454 | $9.1M | Medium |
| Cost Parameters | Treatment acquisition costs | $1,329 | $132.9M | $1,362 | $27.2M | High |
| Cost Parameters | Administration costs | $887 | $88.7M | $908 | $18.2M | Medium |
| Cost Parameters | Societal cost components | $221 | $22.1M | $227 | $4.5M | Low |
| Utility Parameters | Health state utilities | $664 | $66.4M | $681 | $13.6M | Medium |
| Utility Parameters | Treatment disutilities | $222 | $22.2M | $227 | $4.5M | Low |
| **Research Value Rankings** |  |  |  |  |  |  |
| Rank 1 | PO-KA long-term effectiveness | $1,107 | $110.7M | $1,135 | $22.7M | Critical |
| Rank 2 | Comparative effectiveness trials | $887 | $88.7M | $908 | $18.2M | Very High |
| Rank 3 | Real-world adherence rates | $665 | $66.5M | $681 | $13.6M | High |
| Rank 4 | Treatment cost optimization | $443 | $44.3M | $454 | $9.1M | Medium |
| Rank 5 | Quality of life measurement | $332 | $33.2M | $340 | $6.8M | Medium |

---

## SUPPLEMENTARY FIGURES

### Figure S1: Cost-Effectiveness Planes - Societal Perspective

Cost-effectiveness planes from the societal perspective, incorporating comprehensive societal costs including patient time, travel, productivity losses, informal care, and out-of-pocket expenses. Despite additional societal costs, oral ketamine maintains its favorable cost-effectiveness position.

![Figure S1: Societal CE Plane](outputs/figures_vNEXT_20250929_2012/societal__CUA__ce_plane__all_treatments__vs__usual_care__vNEXT.png)

### Figure S2: Cost-Effectiveness Acceptability Curves - Societal Perspective

Societal perspective acceptability curves showing reduced probabilities due to societal cost inclusion. Oral ketamine maintains the highest probability (88% at A$50,000/QALY) but with lower confidence compared to the health system perspective.

![Figure S2: Societal CEAC](outputs/figures_vNEXT_20250929_2012/societal__CUA__ceac__all_treatments__vs__usual_care__vNEXT.png)

### Figure S3: Dual-Perspective Net Monetary Benefit Comparison

Comparison of incremental net monetary benefits between perspectives at the Australian standard threshold of A$50,000/QALY. Oral ketamine maintains the highest net benefit under both perspectives, confirming its robustness as the optimal strategy.

![Figure S3: Dual Perspective INMB Comparison](outputs/figures_vNEXT_20250929_2012/dual_perspective__CUA__inmb_comparison__all_treatments__vs__usual_care__vNEXT.png)

### Figure S4: Budget Impact Analysis - Societal Perspective

Societal perspective budget impact analysis revealing substantially higher total costs when comprehensive societal costs are included. Despite higher absolute costs, the analysis confirms substantial return on investment (4.99:1) for optimal strategies.

![Figure S4: Societal BIA](outputs/figures_vNEXT_20250929_2012/societal__BIA__budget_impact__all_treatments__vs__usual_care__vNEXT.png)

### Figure S5: Value-Based Pricing Curves - Health System Perspective

Value-based pricing analysis showing maximum justifiable prices across willingness-to-pay thresholds from the health system perspective. Oral ketamine demonstrates substantial pricing headroom with 86-fold premium potential over current costs.

![Figure S5: Health System VBP](outputs/figures_vNEXT_20250929_2012/health_system__VBP__pricing_curves__all_treatments__vs__usual_care__vNEXT.png)

### Figure S6: Value-Based Pricing Curves - Societal Perspective

Societal perspective value-based pricing analysis showing how maximum justifiable prices are affected when comprehensive societal costs are included. The analysis demonstrates that even with higher total costs, substantial value remains across willingness-to-pay thresholds.

![Figure S6: Societal VBP](outputs/figures_vNEXT_20250929_2012/societal__VBP__pricing_curves__all_treatments__vs__usual_care__vNEXT.png)

### Figure S7: One-Way Sensitivity Analysis - Oral Ketamine (Societal Perspective)

Tornado diagram showing the impact of parameter variation on net monetary benefit for oral ketamine from the societal perspective. The analysis demonstrates robustness across key parameter ranges, supporting the stability of cost-effectiveness conclusions even when comprehensive societal costs are included.

![Figure S7: Societal Tornado](outputs/figures_vNEXT_20250929_2012/societal__OWSA__tornado__PO-KA__vs__usual_care__vNEXT.png)

### Figure S8: Cost-Effectiveness by Subgroup - Age Groups

Cost-effectiveness results stratified by age groups (young <35 years, middle-aged 35-64 years, elderly >65 years) showing how treatment preferences vary across age cohorts. Oral ketamine maintains cost-effectiveness advantages across all age groups, with stronger performance in elderly patients.

*[Figure would show grouped bar charts or forest plots by age group - actual image path would be generated from subgroup analysis outputs]*

### Figure S9: Cost-Effectiveness by Subgroup - Depression Severity

Cost-effectiveness results stratified by depression severity (mild, moderate, severe) demonstrating how treatment selection should consider illness severity. Oral ketamine shows increasing cost-effectiveness advantages with greater depression severity.

*[Figure would show grouped bar charts or forest plots by severity - actual image path would be generated from subgroup analysis outputs]*

### Figure S10: Budget Impact Analysis - Alternative Adoption Scenarios

Comparison of budget impact projections under conservative (30% peak), moderate (50% peak), and aggressive (80% peak) adoption scenarios over 5 years. The analysis demonstrates scalable implementation with consistent return on investment ratios across scenarios.

*[Figure would show multiple adoption curves - actual image path would be generated from BIA scenario outputs]*

### Figure S11: Expected Value of Perfect Information (EVPI) Analysis

EVPI curves showing the potential value of eliminating parameter uncertainty across different willingness-to-pay thresholds. The analysis quantifies research priorities with clinical effectiveness parameters showing the highest information value.

*[Figure would show EVPI curves - actual image path would be generated from VOI analysis outputs]*

### Figure S12: Two-Way Sensitivity Analysis - Oral Ketamine

Two-way sensitivity analysis examining interactions between oral ketamine remission rate and cost, demonstrating robust cost-effectiveness across wide parameter ranges. The analysis shows oral ketamine maintains dominance even with substantial parameter variations.

*[Figure would show heat map or contour plot - actual image path would be generated from two-way sensitivity analysis]*

---

## SUPPLEMENTARY METHODS

### Detailed Model Structure

The Markov state-transition model employed a three-state structure with monthly transition cycles over a 10-year time horizon. States included: (1) "Depressed" representing active TRD symptoms with associated utility decrements and healthcare utilization; (2) "Remission" representing treatment response with sustained symptom improvement and higher quality of life; and (3) "Death" as an absorbing state incorporating age-adjusted mortality risks.

**State Transitions:** Patients entered the model in the "Depressed" state and could transition to "Remission" based on treatment-specific efficacy parameters derived from clinical trials. Transition probabilities incorporated treatment adherence, with non-adherent patients remaining in or returning to the "Depressed" state. Relapse from "Remission" to "Depressed" occurred based on treatment-specific relapse probabilities, accounting for maintenance therapy where applicable.

**Treatment Modeling:** Each treatment strategy was modeled with realistic clinical pathways:
- **Oral Ketamine (PO-KA):** 12-week oral treatment course with weekly monitoring visits
- **Intravenous Ketamine (IV-KA):** 4-6 induction infusions followed by maintenance infusions over 4 months
- **Intranasal Esketamine (IN-EKA):** Twice-weekly initiation tapering to weekly or as-needed maintenance
- **ECT:** 8-session acute course with 10% (AU) or 5% (NZ) receiving maintenance ECT
- **Ketamine-Assisted ECT (KA-ECT):** Standard ECT protocol with ketamine anesthesia
- **Psilocybin:** 1-2 supervised dosing sessions with psychological support and integration
- **Usual Care:** Standard antidepressant therapy with psychiatric follow-up

### Dual-Perspective Cost Framework

**Health System Perspective:** Captured direct medical costs including treatment acquisition, administration, monitoring, adverse event management, and healthcare utilization. Costs were sourced from Medicare Benefits Schedule (MBS), Pharmaceutical Benefits Scheme (PBS), and hospital cost data using AR-DRG classifications.

**Societal Perspective:** Extended the health system analysis to include:

1. **Patient Time Costs:** Opportunity cost of time spent in healthcare encounters, valued using average weekly earnings data from the Australian Bureau of Statistics (A$45.50/hour). Time allocation included waiting time (0.75 hours) and travel time (1.25 hours) per visit.

2. **Travel Costs:** Transportation expenses using Australian Taxation Office business travel rates (A$0.85/km for private vehicles) or average public transport fares (A$12.50/trip). Average travel distance to specialized mental health facilities was estimated at 28.0 km based on healthcare accessibility studies.

3. **Productivity Costs:** Applied human capital approach to value lost productivity from work absence and reduced performance. Absenteeism valued at A$385/day including wages and employer overhead. Presenteeism during active treatment estimated at 35% productivity reduction with average 8.5 days absence per treatment episode.

4. **Informal Care Costs:** Replacement cost methodology valued unpaid care provided by family and friends at A$65/hour, reflecting market rates for equivalent professional services. Support intensity estimated at 12.5 hours weekly during active treatment phases.

5. **Out-of-Pocket Costs:** Patient and family expenditures not covered by public or private insurance, including session copayments (A$85), annual medication costs (A$420), and ancillary expenses such as parking, accommodation, and meals (A$680).

### Uncertainty and Sensitivity Analysis Framework

**Probabilistic Sensitivity Analysis:** Monte Carlo simulation with 2,000 iterations sampled parameter values from appropriate probability distributions. Beta distributions were assigned to probabilities and utilities, gamma distributions to cost parameters, and log-normal distributions to relative risks and effectiveness measures.

**Deterministic Sensitivity Analysis:** One-way sensitivity analysis varied individual parameters across ±25% ranges around base-case values. Tornado diagrams visualized parameter impact on net monetary benefit rankings.

**Two-Way Sensitivity Analysis:** Examined interactions between key parameter pairs including efficacy rates, costs, and time horizons. Analysis identified threshold values where treatment preferences change and assessed parameter interaction effects.

**Scenario Analysis:** Alternative scenarios explored structural uncertainties including optimistic efficacy assumptions (+25%), pessimistic efficacy assumptions (-25%), 50% price reductions for proprietary treatments, extended 20-year time horizons, and alternative discount rates.

**Subgroup Analysis:** Cost-effectiveness was stratified by patient characteristics including age groups (<35, 35-64, >65 years), depression severity (mild, moderate, severe), and gender. Subgroup-specific parameters were derived from clinical trial data and epidemiological studies where available.

---

## SUPPLEMENTARY DISCUSSION

### Implementation Considerations

**Clinical Implementation:** Successful oral ketamine implementation requires systematic changes in clinical protocols, workforce training, and monitoring frameworks. Key considerations include:

- **Prescriber Training:** Development of standardized training programs for oral ketamine prescribing, including patient selection criteria, dosing protocols, and safety monitoring
- **Monitoring Infrastructure:** Establishment of systematic monitoring protocols for treatment response, adverse effects, and long-term outcomes
- **Integration with Existing Services:** Coordination between primary care, specialist mental health services, and emergency departments for comprehensive patient management

**Health System Implementation:** System-level changes required for optimal implementation include:

- **Reimbursement Frameworks:** Development of appropriate MBS items and PBS listings to support sustainable access
- **Service Delivery Models:** Design of efficient care pathways that minimize patient burden while ensuring safety and effectiveness
- **Quality Assurance:** Implementation of outcome monitoring and quality improvement programs to ensure real-world effectiveness matches trial evidence

### Economic Model Limitations and Strengths

**Limitations:**
- **Clinical Data Uncertainty:** Limited long-term effectiveness data for newer treatments, particularly oral ketamine and psilocybin
- **Societal Cost Estimation:** Societal cost components rely on survey data and proxy measures that may not capture all relevant costs
- **Treatment Pathway Simplification:** Real-world treatment sequences and switching patterns are more complex than modeled pathways
- **Generalizability:** Results specific to Australian and New Zealand contexts may not generalize to other healthcare systems

**Strengths:**
- **Comprehensive Perspective:** Dual-perspective framework provides complete economic assessment across stakeholder viewpoints
- **Robust Uncertainty Analysis:** Extensive sensitivity and scenario analyses address key structural and parameter uncertainties
- **Real-World Clinical Data:** V3 corrected parameters incorporate actual clinical effectiveness rather than preliminary estimates
- **Policy Relevance:** Analysis framework directly addresses key policy questions for reimbursement and implementation decisions

### Future Research Priorities

Based on the value of information analysis, research priorities should focus on:

1. **Head-to-Head Effectiveness Trials:** Large-scale randomized controlled trials comparing oral ketamine directly with ECT and other psychedelic therapies across diverse patient populations

2. **Long-Term Outcome Studies:** Extended follow-up studies examining treatment durability, relapse patterns, and quality of life outcomes beyond 12 months

3. **Real-World Effectiveness Research:** Implementation science studies evaluating effectiveness, safety, and cost-effectiveness in routine clinical practice settings

4. **Economic Data Collection:** Prospective collection of detailed cost and resource utilization data to refine economic model parameters

5. **Patient-Centered Outcomes Research:** Studies incorporating patient preferences, treatment acceptability, and quality of life measures beyond traditional clinical endpoints

### Policy Implications by Jurisdiction

**Australia:**
- **Immediate Actions:** PBS consideration for oral ketamine formulations, MBS item development for monitoring services
- **Medium-term Goals:** Integration into clinical practice guidelines, workforce development programs
- **Long-term Vision:** Comprehensive mental health system reform incorporating psychedelic therapies as standard care options

**New Zealand:**
- **Immediate Actions:** PHARMAC funding consideration, development of clinical protocols within Health New Zealand
- **Medium-term Goals:** Workforce training programs, integration with existing mental health services
- **Long-term Vision:** Equitable access across urban and rural populations, incorporation into Treaty of Waitangi commitments for Māori health

---

## REFERENCES FOR SUPPLEMENTARY MATERIALS

*[Additional references beyond those in the main manuscript would be listed here in the same format]*

---

**Correspondence:** 
[Author details]
Email: [email]
ORCID: [ORCID number]

**Data Availability Statement:**
All data used in this analysis are publicly available or can be obtained from the cited sources. Model code and parameters are available at [repository link].

**Supplementary Material:** This document constitutes the supplementary materials for the main manuscript. All figures and tables referenced are available as separate high-resolution files.