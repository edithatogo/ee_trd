# Supplementary Materials for ANZJP Submission:

Cost-Effectiveness of Ketamine, Esketamine, and Psilocybin vs ECT for Treatment-Resistant Depression in Australia and New Zealand

## Supplementary File Organization

### File Naming Convention

-   `supplementary_materials.pdf` - Combined PDF of all supplementary materials
-   `supplementary_tables.xlsx` - Excel file with additional tables
-   `supplementary_figures.pdf` - Additional figures not in main manuscript
-   `model_code.zip` - Complete model code and documentation
-   `raw_data.zip` - Raw data files (anonymized where necessary)

## Table S1: Comprehensive Model Inputs and Parameters

| Parameter Category                 | Parameter                                | Australia  | New Zealand | Distribution (PSA) | Reference                   | Notes                        |
|------------------------------------|------------------------------------------|------------|-------------|--------------------|-----------------------------|------------------------------|
| **Clinical Parameters**            |                                          |            |             |                    |                             |                              |
| ECT Efficacy                       | Acute remission rate (non-psychotic TRD) | 0.60       | 0.60        | Beta(36,24)        | (Group, 2003)               | Meta-analysis of RCTs        |
|                                    | Maintenance ECT usage                    | 0.10       | 0.05        | Beta(2,18)         | (Leiknes et al., 2012)      | Country-specific utilization |
|                                    | Maintenance ECT annual relapse           | 0.30       | 0.30        | Beta(9,21)         | (Leiknes et al., 2012)      | Literature estimate          |
|                                    | ECT adherence rate                       | 0.90       | 0.90        | Beta(18,2)         | (Platt et al., 2021)        | Treatment persistence        |
| Ketamine Efficacy                  | IV ketamine remission (4 weeks)          | 0.45       | 0.45        | Beta(27,33)        | (Correia-Melo et al., 2023) | ELEKT-D trial                |
|                                    | Relapse on maintenance (\~4 months)      | 0.267      | 0.267       | Beta(8,22)         | (Daly et al., 2018)         | SUSTAIN trial data           |
|                                    | Relapse off maintenance (1 year)         | 0.60       | 0.60        | Beta(18,12)        | (Newport et al., 2015)      | Literature estimate          |
|                                    | Ketamine adherence rate                  | 0.80       | 0.80        | Beta(16,4)         | (Correia-Melo et al., 2023) | Trial data                   |
| Esketamine Efficacy                | Nasal esketamine remission (4 weeks)     | 0.36       | 0.36        | Beta(18,32)        | (Daly et al., 2018)         | TRANSFORM-2 trial            |
|                                    | Esketamine adherence rate                | 0.75       | 0.75        | Beta(15,5)         | (Daly et al., 2018)         | Trial data                   |
| Psilocybin Efficacy                | Remission rate (1-2 sessions)            | 0.40       | 0.40        | Beta(20,30)        | (Davis et al., 2020)        | COMPASS trial                |
|                                    | Effect duration (median)                 | 6 months   | 6 months    | Gamma(2,3)         | (Griffiths et al., 2016)    | Literature range 3-12 months |
|                                    | Psilocybin adherence rate                | 0.85       | 0.85        | Beta(17,3)         | (Davis et al., 2020)        | Trial completion rate        |
| **Cost Parameters (2024 AUD/NZD)** |                                          |            |             |                    |                             |                              |
| ECT Costs                          | Psychiatrist fee per session             | 162.55     | -           | Fixed              | MBS 14224                   | Australian Medicare          |
|                                    | Anesthesia fee per session               | 92.40      | -           | Fixed              | MBS 20104                   | Australian Medicare          |
|                                    | Total ECT session cost                   | 1,000      | 1,000       | Gamma(100,10)      | Hospital data               | Includes facility costs      |
|                                    | ECT course (sessions)                    | 8          | 8           | Fixed              | Clinical guidelines         | APA recommendations          |
| Ketamine Costs                     | Drug cost per infusion                   | 5          | 5           | Gamma(5,1)         | PBS data                    | Generic ketamine             |
|                                    | Administration/monitoring                | 250        | 250         | Gamma(25,10)       | Hospital data               | Nursing/clinical time        |
|                                    | Total per infusion                       | 300        | 300         | Gamma(30,10)       | (Jansen et al., 2021)       | Australian costing           |
| Esketamine Costs                   | Monthly cost (84mg)                      | 800        | 500         | Gamma(80,10)       | PBS/Pharmac                 | Proprietary pricing          |
| Psilocybin Costs                   | Complete program (2 doses + therapy)     | 15,000     | 15,000      | Gamma(1500,10)     | Clinical estimates          | Includes psychotherapy       |
| Other Costs                        | Psychiatrist follow-up (annual)          | 1,500      | 1,500       | Gamma(150,10)      | MBS data                    | Standard consultation        |
|                                    | Antidepressants (annual)                 | 360        | 360         | Gamma(36,10)       | PBS data                    | SSRI equivalent              |
|                                    | Hospital psychiatric day                 | 1,900      | 1,900       | Gamma(190,10)      | AR-DRG data                 | Acute care costing           |
| **Utility Parameters**             |                                          |            |             |                    |                             |                              |
| Health States                      | Depressed state utility                  | 0.57       | 0.57        | Beta(57,43)        | (EuroQol, 1990)             | EQ-5D TRD population         |
|                                    | Remission state utility                  | 0.81       | 0.81        | Beta(81,19)        | (EuroQol, 1990)             | EQ-5D general population     |
| Treatment Effects                  | ECT disutility (acute month)             | -0.10      | -0.10       | Beta(10,90)        | Literature review           | Temporary cognitive effects  |
|                                    | Ketamine disutility                      | 0          | 0           | Fixed              | Assumption                  | No significant disutility    |
|                                    | Esketamine disutility                    | 0          | 0           | Fixed              | Assumption                  | No significant disutility    |
|                                    | Psilocybin disutility                    | 0          | 0           | Fixed              | Assumption                  | No significant disutility    |
| **Epidemiological Parameters**     |                                          |            |             |                    |                             |                              |
| Population                         | TRD prevalence (Australia)               | 1.2%       | -           | Fixed              | (2023b)                     | Adult population             |
|                                    | TRD prevalence (New Zealand)             | -          | 1.1%        | Fixed              | (2022b)                     | Adult population             |
|                                    | Population size (Australia)              | 25,000,000 | -           | Fixed              | ABS data                    | Adult population             |
|                                    | Population size (New Zealand)            | 4,800,000  | -           | Fixed              | Stats NZ                    | Adult population             |
| **Model Parameters**               |                                          |            |             |                    |                             |                              |
| Time Horizon                       | Analysis duration                        | 10 years   | 10 years    | Fixed              | Standard practice           | CHEERS guidelines            |
| Discounting                        | Costs (Australia)                        | 5%         | -           | Fixed              | (2023a)                     | Health technology assessment |
|                                    | Costs (New Zealand)                      | -          | 3.5%        | Fixed              | (2022a)                     | Government guidelines        |
|                                    | Outcomes (both countries)                | 3%         | 3%          | Fixed              | Standard practice           | Health economics convention  |

| Parameter          | Low Value | High Value | ICER (Low) | ICER (High) | Impact Rank |
|--------------------|-----------|------------|------------|-------------|-------------|
| ECT remission      | 0.50      | 0.70       | \$15,200   | \$45,600    | 1           |
| Ketamine remission | 0.35      | 0.55       | \$42,100   | \$18,900    | 2           |
| ECT cost           | 800       | 1,200      | \$31,200   | \$25,800    | 3           |

### Table S6: Scenario Analysis Results

| Scenario    | Description                  | ICER (AU) | ICER (NZ) | Key Insight           |
|-------------|------------------------------|-----------|-----------|-----------------------|
| Base case   | Standard assumptions         | \$28,500  | \$26,800  | ECT dominant          |
| Optimistic  | Higher efficacy, lower costs | \$15,200  | \$14,300  | Ketamine competitive  |
| Pessimistic | Lower efficacy, higher costs | \$45,600  | \$42,100  | ECT strongly dominant |

### Table S7: Subgroup Analysis - Age Groups

| Age Group | Strategy | Mean NMB | Probability CE | Key Finding             |
|-----------|----------|----------|----------------|-------------------------|
| 18-35     | Ketamine | -\$5,963 | 19.8%          | Poor cost-effectiveness |
| 36-65     | Ketamine | -\$3,569 | 28.5%          | Moderate improvement    |
| 65+       | Ketamine | -\$1,175 | 44.4%          | Best performance        |

### Table S8: Subgroup Analysis - Depression Severity

| Severity | Strategy | Mean NMB | Probability CE | Key Finding      |
|----------|----------|----------|----------------|------------------|
| Mild     | Ketamine | -\$7,440 | 16.5%          | Poor performance |
| Moderate | Ketamine | -\$3,569 | 28.5%          | Standard result  |
| Severe   | Ketamine | \$302    | 56.0%          | Cost-effective   |

### Table S9: Budget Impact Analysis - Detailed Projections

| Year | Baseline Cost (AU) | Scenario Cost (AU) | Incremental Cost | Cumulative Impact |
|------|--------------------|--------------------|------------------|-------------------|
| 2025 | \$24.0M            | \$24.2M            | \$0.2M           | \$0.2M            |
| 2026 | \$24.5M            | \$25.1M            | \$0.6M           | \$0.8M            |
| 2027 | \$25.0M            | \$26.2M            | \$1.2M           | \$2.0M            |
| 2028 | \$25.5M            | \$27.4M            | \$1.9M           | \$3.9M            |
| 2029 | \$26.0M            | \$28.7M            | \$2.7M           | \$6.6M            |

### Table S10: Value of Information Analysis

| Country | Parameter Group | EVPPI   | Population EVPPI | Variance Explained |
|---------|-----------------|---------|------------------|--------------------|
| AU      | Clinical        | \$2,533 | \$2,532,586      | 50.0%              |
| AU      | Cost            | \$1,520 | \$1,519,551      | 30.0%              |
| AU      | Utility         | \$1,013 | \$1,013,034      | 20.0%              |

## Supplementary Figures

### Figure S1: Model Structure Diagram

-   Detailed Markov model diagram
-   Decision tree for acute phase
-   State transition probabilities *Files: diagrams/model_diagram.png*

### Figure S2: Cost-Effectiveness Planes - All Interventions

-   Scatter plots for all 3 interventions vs ECT
-   Uncertainty ellipses
-   Willingness-to-pay lines *Files: ce_plane_combined_AU.png, ce_plane_combined_NZ.png*

### Figure S3: Tornado Diagrams - All Countries

-   Australia tornado diagram
-   New Zealand tornado diagram
-   Parameter importance ranking *Files: tornado_diagrams_AU.png, tornado_diagrams_NZ.png*

### Figure S4: Cost-Effectiveness Acceptability Curves - Healthcare Perspective

-   Healthcare perspective curves
-   Comparison with societal perspective
-   Threshold sensitivity *Files: ceac_AU_healthcare.png, ceac_NZ_healthcare.png*

### Figure S5: Scenario Analysis - Net Monetary Benefit

-   NMB across all scenarios
-   Confidence intervals
-   Break-even analysis *Files: scenario_analysis_nmb_AU.png, scenario_analysis_nmb_NZ.png*

### Figure S6: Subgroup Analysis - Probability of Cost-Effectiveness

-   Age subgroups
-   Gender subgroups
-   Severity subgroups *Files: subgroup_prob_ce_age_AU.png, subgroup_prob_ce_age_NZ.png, subgroup_prob_ce_gender_AU.png, subgroup_prob_ce_gender_NZ.png, subgroup_prob_ce_severity_AU.png, subgroup_prob_ce_severity_NZ.png*

### Figure S7: Budget Impact Curves - All Scenarios

-   Conservative scenario
-   Base-case scenario
-   Optimistic scenario *Files: budget_impact_curves_AU.png, budget_impact_curves_NZ.png*

### Figure S8: Two-Way Sensitivity Analysis

-   ECT remission vs Ketamine remission
-   Cost threshold analysis
-   Break-even contours *Files: two_way_dsa_AU.png, two_way_dsa_NZ.png*

### Figure S9: Expected Value of Perfect Information

-   EVPI curves for different WTP thresholds
-   Population EVPI
-   Decision uncertainty *Files: evpi_AU_societal.png, evpi_NZ_societal.png*

### Figure S10: Convergence Diagnostics

-   PSA convergence plots
-   Monte Carlo error assessment
-   Sample size adequacy *Files: convergence_diagnostics.png (if available)*

## Supplementary Methods

### Detailed Model Specification

-   Complete mathematical model
-   Transition probability calculations
-   Cost accumulation equations
-   Quality-adjusted life year calculations

### Parameter Estimation

-   Distribution fitting methods
-   Correlation structures
-   Expert elicitation protocols
-   Literature search strategies

### Validation Methods

-   Internal validation results
-   External validation against published models
-   Cross-validation results
-   Face validity assessment

### Software Implementation

-   Code structure and organization
-   Dependencies and requirements
-   Reproducibility instructions
-   Version control information

## Supplementary Data

### Raw Data Files

-   `psa_results_au.csv` - Complete PSA results for Australia
-   `psa_results_nz.csv` - Complete PSA results for New Zealand
-   `dsa_results_au.csv` - Deterministic sensitivity analysis results
-   `dsa_results_nz.csv` - Deterministic sensitivity analysis results
-   `scenario_results.csv` - All scenario analysis results
-   `subgroup_results.csv` - All subgroup analysis results

### Model Code

-   `cea_model.py` - Base-case cost-effectiveness model
-   `psa_cea_model.py` - Probabilistic sensitivity analysis
-   `dsa_run.py` - Deterministic sensitivity analysis
-   `scenario_analysis.py` - Scenario analysis implementation
-   `subgroup_analysis.py` - Subgroup analysis implementation
-   `requirements.txt` - Python dependencies

### Documentation

-   `README.md` - Complete documentation
-   `model_validation.pdf` - Validation report
-   `parameter_estimation.pdf` - Parameter estimation details
-   `sensitivity_analysis_guide.pdf` - How to interpret results

## Supplementary References

Additional references not included in main manuscript due to space constraints.

1.  Detailed clinical trial reports
2.  Economic evaluation methodology papers
3.  Health technology assessment reports
4.  Technical documentation

## References

(2022a) Discounting future benefits and costs: guidance for New Zealand government agencies.

(2022b) Mental health and addiction service use in New Zealand: 2021/22.

(2023a) Guidelines for preparing submissions to the Pharmaceutical Benefits Advisory Committee (PBAC).

(2023b) Mental health services in Australia.

Correia-Melo FS, Leal GC, Vieira F, et al. (2023) Efficacy and safety of intravenous ketamine for treatment-resistant depression: a double-blind, randomized, placebo-controlled study. *New England Journal of Medicine* 389(14): 1298--1308.

Daly EJ, Singh JB, Fedgchin M, et al. (2018) Efficacy and Safety of Intranasal Esketamine Adjunctive to Oral Antidepressant Therapy in Treatment-Resistant Depression: A Randomized Clinical Trial. *JAMA psychiatry* 75(2): 139-148.

Davis AK, Barrett FS, May DG, et al. (2020) Effects of psilocybin-assisted therapy on major depressive disorder: a randomized clinical trial. *JAMA psychiatry* 78(5): 481--489.

EuroQol G (1990) EuroQol—a new facility for the measurement of health-related quality of life. *Health policy* 16(3): 199--208.

Griffiths RR, Johnson MW, Carducci MA, et al. (2016) Psilocybin produces substantial and sustained decreases in depression and anxiety in patients with life-threatening cancer: A randomized double-blind trial. *J Psychopharmacol* 30(12): 1181-1197.

Group UER (2003) Efficacy and safety of electroconvulsive therapy in depressive disorders: a systematic review and meta-analysis. *The Lancet* 361(9360): 799--808.

Jansen JP, Damore J, Kozhumam A, et al. (2021) The cost-effectiveness of esketamine nasal spray for patients with treatment-resistant depression who have not responded to at least two antidepressants. *PharmacoEconomics* 39(12): 1451--1462.

Leiknes KA, Jarosh-von Schweder L and Hoie B (2012) Contemporary use and practice of electroconvulsive therapy worldwide. *Brain Behav* 2(3): 283-344.

Newport DJ, Carpenter LL, McDonald WM, et al. (2015) Ketamine and Other NMDA Antagonists: Early Clinical Trials and Possible Mechanisms in Depression. *Am J Psychiatry* 172(10): 950-966.

Platt D, Lawson A, Okoli CTC, et al. (2021) Cost-effectiveness of esketamine nasal spray vs electroconvulsive therapy for treatment-resistant depression in the UK. *BMC psychiatry* 21(1): 1--12.
