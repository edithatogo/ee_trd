# V4 Assumption Register

Complete documentation of all model assumptions with justifications.

## Model Structure Assumptions

### Markov Model
- **Assumption**: Health states can be adequately represented by discrete states
- **Justification**: Standard approach in depression modeling, validated in previous studies
- **Impact**: Simplifies continuous disease progression
- **Sensitivity**: Tested via structural sensitivity analysis

### Time Horizon
- **Assumption**: 10-year time horizon captures relevant outcomes
- **Justification**: Balances long-term outcomes with parameter uncertainty
- **Impact**: May underestimate very long-term benefits
- **Sensitivity**: Tested at 5, 15, 20 years

### Cycle Length
- **Assumption**: Monthly cycles adequately capture disease dynamics
- **Justification**: Treatment phases and relapse patterns occur over weeks-months
- **Impact**: May miss very rapid changes
- **Sensitivity**: Half-cycle correction applied

### Tunnel States
- **Assumption**: Relapse risk varies with time since remission
- **Justification**: Clinical evidence shows waning effects over time
- **Impact**: More realistic modeling of treatment durability
- **Sensitivity**: Compared with constant relapse rate model

## Clinical Assumptions

### Treatment Pathways

#### ECT
- **Assumption**: 8-session acute course, selective maintenance
- **Justification**: Standard clinical practice in AU/NZ
- **Impact**: Reflects real-world utilization
- **Sensitivity**: Tested with 6-12 session range

#### Ketamine Therapies
- **Assumption**: Induction phase followed by maintenance
- **Justification**: Evidence-based protocols from clinical trials
- **Impact**: Captures both acute and maintenance costs/effects
- **Sensitivity**: Tested with varying maintenance durations

#### Psilocybin
- **Assumption**: 1-2 supervised sessions with psychological support
- **Justification**: Current trial protocols
- **Impact**: May underestimate real-world therapy requirements
- **Sensitivity**: Tested with 1-3 session range

### Treatment Adherence
- **Assumption**: 85% adherence for oral therapies, 95% for supervised
- **Justification**: Literature on psychiatric medication adherence
- **Impact**: Affects real-world effectiveness
- **Sensitivity**: Tested at 70-95% range

### Treatment Switching
- **Assumption**: Patients can switch therapies after failure
- **Justification**: Reflects clinical practice
- **Impact**: Increases costs but improves outcomes
- **Sensitivity**: Tested with no-switching scenario

## Economic Assumptions

### Discount Rates

#### Australia
- **Assumption**: 5% for costs and effects
- **Justification**: PBAC Guidelines (2023)
- **Impact**: Standard approach for AU health technology assessment
- **Sensitivity**: Tested at 0%, 3%, 7%

#### New Zealand
- **Assumption**: 3.5% for costs and effects
- **Justification**: PHARMAC Guidelines (2022)
- **Impact**: Standard approach for NZ health technology assessment
- **Sensitivity**: Tested at 0%, 2.5%, 5%

### Perspective Definitions

#### Health System Perspective
- **Assumption**: Includes only direct medical costs
- **Justification**: Primary perspective for reimbursement decisions
- **Impact**: Excludes broader societal costs
- **Sensitivity**: Compared with societal perspective

#### Societal Perspective
- **Assumption**: Includes productivity, informal care, patient time
- **Justification**: Comprehensive economic impact assessment
- **Impact**: Higher costs but captures full economic burden
- **Sensitivity**: Tested with/without productivity costs

### Cost Components

#### Productivity Costs
- **Assumption**: Human capital approach (full wage)
- **Justification**: Standard in health economics
- **Impact**: May overestimate productivity losses
- **Sensitivity**: Tested with friction cost method

#### Informal Care
- **Assumption**: Valued at formal care worker wage
- **Justification**: Opportunity cost approach
- **Impact**: Captures family burden
- **Sensitivity**: Tested at 50-150% of formal wage

## Population Assumptions

### Eligibility Criteria
- **Assumption**: Adults 18+ with TRD (failed ≥2 antidepressants)
- **Justification**: Standard TRD definition
- **Impact**: Defines target population
- **Sensitivity**: Tested with broader/narrower definitions

### Subgroup Definitions

#### Age Groups
- **Assumption**: 18-44, 45-64, 65+ years
- **Justification**: Clinically meaningful age categories
- **Impact**: Captures age-related differences
- **Sensitivity**: Tested with alternative groupings

#### Severity
- **Assumption**: Mild, moderate, severe based on MADRS scores
- **Justification**: Standard depression severity classification
- **Impact**: Captures treatment response heterogeneity
- **Sensitivity**: Tested with continuous severity measure

### Indigenous Populations
- **Assumption**: Aboriginal, Māori, Pacific Islander have different baseline characteristics
- **Justification**: Health equity considerations and documented disparities
- **Impact**: Enables equity analysis
- **Sensitivity**: Tested with pooled analysis

## Treatment Effect Assumptions

### Efficacy Estimates
- **Assumption**: Trial efficacy translates to real-world effectiveness
- **Justification**: Best available evidence
- **Impact**: May overestimate real-world outcomes
- **Sensitivity**: Tested with 20% effectiveness reduction

### Durability
- **Assumption**: Treatment effects wane over time
- **Justification**: Clinical evidence of relapse
- **Impact**: Reduces long-term benefits
- **Sensitivity**: Tested with constant vs time-varying effects

### Comparative Effectiveness
- **Assumption**: Network meta-analysis provides valid indirect comparisons
- **Justification**: Standard approach when head-to-head trials limited
- **Impact**: Enables comparison of all therapies
- **Sensitivity**: Tested with direct evidence only

## Safety Assumptions

### Adverse Events
- **Assumption**: AE rates from trials apply to real-world
- **Justification**: Best available evidence
- **Impact**: May underestimate real-world AE burden
- **Sensitivity**: Tested with 50-150% of trial rates

### Mortality
- **Assumption**: Age-adjusted general population mortality
- **Justification**: TRD mortality similar to general population with treatment
- **Impact**: Conservative assumption
- **Sensitivity**: Tested with elevated mortality for TRD

## Implementation Assumptions

### Healthcare System Capacity
- **Assumption**: Sufficient capacity for new therapies
- **Justification**: Simplifying assumption for base case
- **Impact**: May underestimate implementation barriers
- **Sensitivity**: Tested with capacity constraints

### Training and Credentialing
- **Assumption**: Clinicians can be trained for new therapies
- **Justification**: Feasible with appropriate training programs
- **Impact**: Implementation costs included
- **Sensitivity**: Tested with varying training costs

### Market Adoption
- **Assumption**: Linear or S-curve adoption over 5 years
- **Justification**: Typical technology adoption patterns
- **Impact**: Affects budget impact timing
- **Sensitivity**: Tested with rapid vs slow adoption

## Equity Assumptions

### Inequality Aversion
- **Assumption**: Epsilon = 1.5 for social welfare function
- **Justification**: Moderate inequality aversion, standard in DCEA
- **Impact**: Weights outcomes toward disadvantaged groups
- **Sensitivity**: Tested at epsilon = 0, 1, 2

### Indigenous Health Equity
- **Assumption**: Indigenous populations have lower baseline utilities
- **Justification**: Documented health disparities
- **Impact**: Affects equity analysis
- **Sensitivity**: Tested with equal baseline utilities

## Validation

### Internal Validation
- Model structure reviewed by clinical experts
- Parameters checked against primary sources
- Calculations verified independently

### External Validation
- Results compared with published studies where available
- Face validity assessed by clinicians
- Calibration to real-world data where possible

## Limitations

### Data Limitations
- Limited head-to-head trial data for some comparisons
- Long-term relapse data sparse for novel therapies
- Indigenous-specific data limited

### Model Limitations
- Simplified health states may not capture full disease complexity
- Assumes homogeneous treatment effects within subgroups
- Does not model individual patient heterogeneity

### Uncertainty
- High uncertainty for novel therapies (PO-PSI, PO-KA)
- Limited real-world effectiveness data
- Extrapolation required for long-term outcomes

---

**Last Updated**: February 10, 2025  
**Version**: V4.0.0  
**Review Status**: All assumptions documented and justified
