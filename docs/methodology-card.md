# Methodology Passport Card

## 1. Project information

**Title:** Associations Between Remote IT Work Conditions, Stress, Burnout and Self-Reported Productivity

**Author:** Asanali Talgat (individual project)  
**Public GitHub repository:** https://github.com/Asanalishka/remote-it-wellbeing-study

## 2. Research design

**Quantitative observational cross-sectional survey.** A single, anonymous questionnaire will collect remote-work characteristics, PSS-10 perceived stress, work-related CBI burnout and self-reported productivity from IT specialists working remotely. Quantitative measurement supports reproducible scale scoring and estimation of adjusted associations. Predictors are **observed, not manipulated**. The design estimates conditional associations; it cannot identify causal effects. The author must verify consistency with Task 1 before submission; its source materials are not included in this repository.

## 3. Research questions and testable hypotheses

| Question | Null (H0) | Alternative (H1) |
| --- | --- | --- |
| RQ1. What are the stress, burnout and productivity levels? | Descriptive question: no causal or inferential null is needed; report means, spread and sample size. | Descriptive output rather than a competing hypothesis. |
| RQ2. Which remote-work characteristics are associated with stress and burnout? | All adjusted coefficients for the four remote-work characteristics equal zero in both outcome models. | At least one adjusted coefficient differs from zero. |
| RQ3. Is greater work-related burnout associated with lower productivity after adjusting for stress and controls? | The adjusted burnout coefficient is nonnegative (β ≥ 0). | The adjusted burnout coefficient is negative (β < 0). |

The planned RQ3 test is directional, with a prespecified one-sided significance level of α = 0.05. Stress remains a separate predictor in the baseline model; its baseline coefficient per PSS-10 point is reported as a secondary association. Before collecting data for RQ2, specify the joint testing procedure and multiple-comparison handling. RQ1 is descriptive and does not require a midpoint hypothesis test.

## 4. Variable matrix

| Role | Variables | Measurement / handling |
| --- | --- | --- |
| RQ2 independent (observed) | Weekly hours; work-life balance; communication interactions per week; schedule flexibility | Hours (1–100); balance and flexibility ratings (0–10); communication count (0–100). Treat scales carefully, inspect nonlinearity. |
| RQ2 dependent | Perceived stress; work-related burnout | PSS-10 sum (0–40); CBI work subscale mean (0–100). |
| RQ3 independent | Work-related burnout (primary); stress (secondary) | CBI per 10 points; PSS-10 per point. |
| RQ3 dependent | Self-reported productivity | A prespecified rating from 0 to 10, not objective software output. |
| Adjustment variables | Age, gender, years of IT experience, job role, weekly hours for RQ3 | Collect uniformly and document category coding. Weekly hours are an RQ2 predictor, so do not relabel them as a control in that model. |
| Controlled variables / standardized conditions | Questionnaire version, wording, scale anchors, reference windows, eligibility rules, scoring and software configuration | Use one frozen questionnaire and eligibility protocol for all participants; finalize these before recruitment. These are protocol constants, not demographic covariates. |

**Fixed pilot conditions:** Python 3.12.14 in the digest-pinned Debian Bookworm container, standard-library-only code, `config.json`, and the same eight rows in `data/sample/pilot_synthetic.csv`. PSS-10 reverse items are 4, 5, 7 and 8; CBI work item 7 is reversed. Complete, valid records are required and duplicate IDs are excluded. Hardware is not an experimental factor: the pilot measures survey scores and associations, not execution speed or resource consumption.

## 5. Primary metric, guardrails and baseline

**Primary estimand:** β for work-related CBI per 10 points from `productivity = intercept + β(CBI/10) + γ(PSS) + δ(controls) + ε`. Its unit is expected difference in the 0–10 self-report productivity rating per 10 CBI points, conditional on the listed covariates. Report the point estimate and confidence interval; reject H0 for the planned one-sided α = 0.05 test only if an appropriately calibrated one-sided 95% upper confidence bound is below zero. The pilot output uses a two-sided approximate 95% interval and makes no significance claim; it does not implement the planned one-sided test.

**Secondary metrics:** PSS-10 and CBI descriptive distributions; coefficients for RQ2 characteristics; baseline stress coefficient per PSS-10 point; difference in R² between the baseline and full RQ3 models. The Week 6 runner reports descriptive means; full distributions and RQ2 models are planned for Week 7.

**Guardrail metrics:** proportion of rejected questionnaires (including incomplete records) ≤10%; no duplicate respondent IDs; valid instrument ranges; ≥80 complete cases to enable the pilot model. This threshold is not a formal power calculation. Revisit sample size and missing-data handling before collection; assess collinearity, model assumptions and confidence-interval calibration before final inference.

**Baseline:** RQ3 model using age, gender, experience, role, hours and PSS-10 stress. The full model adds CBI work-related burnout. Compare estimates on the same complete cases. There is **no randomized control group**. For RQ2, separate models of stress and burnout include the four observed remote-work characteristics and prespecified demographic/job controls.

## 6. Pilot execution and validity

The Week 6 repository includes eight explicitly synthetic rows to verify input validation, item reversal, scoring and JSON output. Since 8 < 80, no association is estimated from the sample. Real survey data must not be committed to the public repository. A cross-sectional self-report survey faces common-method bias, selection bias, reverse causation and limited generalizability; report recruitment and missingness, use consistent instruments, and avoid causal language.

**Sources for scoring:** [CMU PSS scoring](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/html/pssscoring.html); [original CBI work-related scale](https://nfa.dk/media/a4wheblj/cbi-scales.pdf).

## 7. Required decisions before recruitment (Week 7)

- Justify the sample size using a prespecified meaningful effect and sensitivity/power analysis; do not treat the 80-case engineering gate as that justification.
- Freeze questionnaire wording, language, scale anchors, reference windows, eligibility criteria and recruitment/consent procedures.
- Prespecify missing-data handling, RQ2 joint tests and multiple-comparison control, model diagnostics and the method for the final RQ3 confidence bound.

These decisions require the author's study context. The synthetic pilot validates execution and scoring, not readiness to draw conclusions from real participants.
