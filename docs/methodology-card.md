# Methodology Passport Card

## 1. Project information

**Title:** The Impact of Remote Work Conditions on Stress and Burnout Among IT Specialists and Their Relationship with Work Productivity  
**Author:** Asanali Talgat (individual project)  
**Public GitHub repository:** to be inserted after publication.

## 2. Research design

**Quantitative observational cross-sectional survey.** A single, anonymous questionnaire will collect remote-work characteristics, PSS-10 perceived stress, work-related CBI burnout and self-reported productivity from IT specialists working remotely. Predictors are **observed, not manipulated**. The design estimates conditional associations; it cannot identify causal effects. This extends the literature synthesis and research questions established in Task 1.

## 3. Research questions and testable hypotheses

| Question | Null (H0) | Alternative (H1) |
| --- | --- | --- |
| RQ1. What are the stress, burnout and productivity levels? | Descriptive question: no causal or inferential null is needed; report means, spread and sample size. | Descriptive output rather than a competing hypothesis. |
| RQ2. Which remote-work characteristics are associated with stress and burnout? | All adjusted coefficients for the four remote-work characteristics equal zero in both outcome models. | At least one adjusted coefficient differs from zero. |
| RQ3. Is greater work-related burnout associated with lower productivity after adjusting for stress and controls? | The adjusted burnout coefficient is nonnegative (β ≥ 0). | The adjusted burnout coefficient is negative (β < 0). |

The RQ3 test is directional and prespecified. Stress remains a separate predictor in the baseline model and is reported as a secondary association. For RQ2, report uncertainty and multiple-comparison handling before interpreting individual predictors. RQ1 is descriptive; the earlier Task 1 midpoint test was an artificial benchmark and is not required for a meaningful description.

## 4. Variable matrix

| Role | Variables | Measurement / handling |
| --- | --- | --- |
| RQ2 independent (observed) | Weekly hours; work-life balance; communication interactions per week; schedule flexibility | Hours (1–100); balance and flexibility ratings (0–10); communication count (0–100). Treat scales carefully, inspect nonlinearity. |
| RQ2 dependent | Perceived stress; work-related burnout | PSS-10 sum (0–40); CBI work subscale mean (0–100). |
| RQ3 independent | Work-related burnout (primary); stress (secondary) | CBI per 10 points; PSS-10 per point. |
| RQ3 dependent | Self-reported productivity | A prespecified rating from 0 to 10, not objective software output. |
| Adjustment variables | Age, gender, years of IT experience, job role, weekly hours for RQ3 | Collect uniformly and document category coding. Weekly hours are an RQ2 predictor, so do not relabel them as a control in that model. |
| Standardized protocol | Survey wording, scale anchors and reference window, inclusion criteria, scoring, software configuration | Same questions and scoring rules for every respondent; these are protocol constants, not demographic covariates. |

## 5. Primary metric, guardrails and baseline

**Primary estimand:** β for work-related CBI per 10 points from `productivity = α + β(CBI/10) + γ(PSS) + δ(controls) + ε`. Its unit is expected difference in the 0–10 self-report productivity rating per 10 CBI points, conditional on the listed covariates. Report the point estimate and confidence interval; the one-sided negative claim is supported only if an appropriately calibrated upper confidence bound is below zero. The pilot output uses a two-sided approximate 95% interval and makes no significance claim.

**Secondary metrics:** PSS-10 and CBI descriptive distributions; coefficients for RQ2 characteristics; stress coefficient; difference in R² between the baseline and full RQ3 models.

**Guardrail metrics:** proportion of rejected questionnaires (including incomplete records) ≤10%; no duplicate respondent IDs; valid instrument ranges; ≥80 complete cases to enable the pilot model. This threshold is not a formal power calculation. Revisit sample size and missing-data handling before collection; assess collinearity, model assumptions and confidence-interval calibration before final inference.

**Baseline:** RQ3 model using age, gender, experience, role, hours and PSS-10 stress. The full model adds CBI work-related burnout. Compare estimates on the same complete cases. There is **no randomized control group**. For RQ2, separate models of stress and burnout include the four observed remote-work characteristics and prespecified demographic/job controls.

## 6. Pilot execution and validity

The Week 6 repository includes eight explicitly synthetic rows to verify input validation, item reversal, scoring and JSON output. Since 8 < 80, no association is estimated from the sample. Real survey data must not be committed to the public repository. A cross-sectional self-report survey faces common-method bias, selection bias, reverse causation and limited generalizability; report recruitment and missingness, use consistent instruments, and avoid causal language.

**Sources for scoring:** [CMU PSS scoring](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/html/pssscoring.html); [original CBI work-related scale](https://nfa.dk/media/a4wheblj/cbi-scales.pdf).
