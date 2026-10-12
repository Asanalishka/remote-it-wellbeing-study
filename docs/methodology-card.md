# Methodology Passport Card

## 1. Project information

**Title:** Associations Between Remote IT Work Conditions, Stress, Burnout and Self-Reported Productivity

**Author:** Asanali Talgat (individual project)  
**Public GitHub repository:** https://github.com/Asanalishka/remote-it-wellbeing-study

## 2. Research design

**Quantitative observational cross-sectional survey.** A single, anonymous questionnaire will collect remote-work characteristics, PSS-10 perceived stress, work-related CBI burnout and self-reported productivity from IT specialists working remotely. Quantitative measurement supports reproducible scale scoring and estimation of adjusted associations. Predictors are **observed, not manipulated**. The design estimates conditional associations; it cannot identify causal effects.

**Alignment with Task 1:** retain descriptive outcomes and secondary midpoint comparisons (RQ1), predicted outcomes across observed work-condition combinations (RQ2), and independent stress and burnout associations in one productivity model (RQ3). Refinements clarify the directional RQ3 null, multiplicity handling, the primary reporting metric, and remote-work intensity as a descriptive percentage. The title uses associations to match the observational design.

## 3. Research questions and testable hypotheses

| Question | Null (H0) | Alternative (H1) |
| --- | --- | --- |
| RQ1. What are the stress, burnout and self-reported productivity levels, and do their means differ from scale midpoints? | Population means equal 20 (PSS-10), 50 (CBI work) and 5 (productivity). | At least one population mean differs from its specified midpoint. |
| RQ2. Which observed combinations of weekly working hours, work-life balance, communication frequency and schedule flexibility correspond to lower adjusted stress and burnout? | All adjusted coefficients for the four work characteristics equal zero in both outcome models. | At least one adjusted coefficient differs from zero. |
| RQ3. Are higher stress and burnout associated with lower self-reported productivity after mutual adjustment and adjustment for covariates? | Both full-model coefficients are nonnegative: β_stress ≥ 0 and β_burnout ≥ 0. | At least one full-model coefficient is negative. |

**Planned inference:** RQ1 primarily describes means, spread and sample size. Its three secondary two-sided midpoint tests will use Holm adjustment with family-wise α = 0.05; midpoints are mathematical references, not clinical norms. RQ3 will use two one-sided tests of nonnegative versus negative coefficients from the same full model, with Holm adjustment at family-wise α = 0.05. Reject the corresponding family null only if at least one component null is rejected after adjustment. RQ1 and RQ3 are separate testing families; this does not control one combined error rate across all research questions. These tests are not implemented in the Week 6 pilot.

For RQ2, compare adjusted predictions for combinations actually observed in the sample, with covariate handling and joint/multiple-comparison testing specified before recruitment. Do not extrapolate to unobserved work regimes or interpret a lower predicted value as a causal optimum. Stress and burnout may favor different observed combinations; no single combined optimization score is prescribed.

## 4. Variable matrix

| Role | Variables | Measurement / handling |
| --- | --- | --- |
| RQ2 independent (observed) | Weekly hours; work-life balance; communication interactions per week; schedule flexibility | Hours (1–100); balance and flexibility ratings (0–10); communication count (0–100). Treat scales carefully, inspect nonlinearity. |
| RQ2 dependent | Perceived stress; work-related burnout | PSS-10 sum (0–40); CBI work subscale mean (0–100). |
| RQ3 independent | Work-related burnout (primary); stress (required secondary) | CBI per 10 points; PSS-10 per point; both coefficients from the same full model. |
| RQ3 dependent | Self-reported productivity | A prespecified rating from 0 to 10, not objective software output. |
| Adjustment variables | Age, gender, years of IT experience, job role, weekly hours for RQ3 | Collect uniformly and document category coding. Weekly hours are an RQ2 predictor, so do not relabel them as a control in that model. |
| Descriptive sample characteristic | Remote-work intensity (`remote_work_percent`) | Self-reported percentage of working hours performed remotely in a usual working week; finite number >0 and ≤100, fractions allowed. Required for every record, but not a regression covariate or one of the four RQ2 predictors. |
| Controlled variables / standardized conditions | Questionnaire version, wording, scale anchors, reference windows, eligibility rules, scoring and software configuration | Use one frozen questionnaire and eligibility protocol for all participants; finalize these before recruitment. These are protocol constants, not demographic covariates. |

**Fixed pilot conditions:** Python 3.12.14 in the digest-pinned Debian Bookworm container, standard-library-only code, `config.json`, and the same eight rows in `data/sample/pilot_synthetic.csv`. PSS-10 reverse items are 4, 5, 7 and 8; CBI work item 7 is reversed. Complete, valid records are required and duplicate IDs are excluded. Hardware is not an experimental factor: the pilot measures survey scores and associations, not execution speed or resource consumption.

## 5. Primary metric, guardrails and baseline

**Primary estimand:** β for work-related CBI per 10 points from `productivity = intercept + β(CBI/10) + γ(PSS) + δ(controls) + ε`. Its unit is expected difference in the 0–10 self-report productivity rating per 10 CBI points, conditional on stress and the listed covariates. Burnout is the primary reporting metric; this priority does not remove stress from RQ3 or exempt burnout from the two-test Holm procedure. Both full-model coefficients receive approximate two-sided 95% intervals in the pilot. These classical OLS intervals are neither multiplicity-adjusted nor the planned directional tests; no significance decision is emitted.

**Secondary metrics:** required full-model stress coefficient per PSS-10 point (adjusted for burnout and all covariates); difference in R² between baseline and full RQ3 models; outcome distributions and RQ1 midpoint comparisons; RQ2 coefficients and predictions across observed conditions. The pilot reports means, including remote-work percentage, and retains the baseline stress coefficient solely for comparison. Full distributions, hypothesis tests and RQ2 models are planned for Week 7.

**Guardrail metrics:** proportion of rejected questionnaires (including incomplete records) ≤10%; no duplicate respondent IDs; valid instrument ranges; ≥80 complete cases to enable the pilot model. This threshold is not a formal power calculation. Revisit sample size and missing-data handling before collection; assess collinearity, model assumptions and confidence-interval calibration before final inference.

**Baseline:** RQ3 model using age, gender, experience, role, hours and PSS-10 stress. The full model adds CBI work-related burnout. Compare estimates on the same complete cases; ΔR² measures the additional contribution of burnout. The baseline stress coefficient does not adjust for burnout and does not answer RQ3 on its own. There is **no randomized control group**. For RQ2, separate models of stress and burnout include the four observed work characteristics and prespecified demographic/job covariates.

## 6. Pilot execution and validity

The Week 6 repository includes eight explicitly synthetic rows, including invented remote-work percentages, to verify input validation, item reversal, scoring and JSON output. Since 8 < 80, no association is estimated from the sample and no hypothesis is tested. Real survey data must not be committed to the public repository. A cross-sectional self-report survey faces common-method bias, selection bias, reverse causation and limited generalizability; report recruitment and missingness, use consistent instruments, and avoid causal language.

**Sources for scoring:** [CMU PSS scoring](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/html/pssscoring.html); [original CBI work-related scale](https://nfa.dk/media/a4wheblj/cbi-scales.pdf).

## 7. Required decisions before recruitment (Week 7)

- Justify the sample size using a prespecified meaningful effect and sensitivity/power analysis; do not treat the 80-case engineering gate as that justification.
- Freeze questionnaire wording (including usual-week remote-work percentage), language, scale anchors, reference windows, eligibility criteria and recruitment/consent procedures.
- Prespecify missing-data handling, RQ2 joint tests and multiple-comparison control, how covariates are held constant or averaged for predictions, and model diagnostics.
- Finalize the individual RQ1 test and RQ3 standard-error/p-value methods before analysis; apply the separate Holm families specified above. The pilot's approximate intervals are not substitutes for these procedures.

These decisions require the author's study context. The synthetic pilot validates execution and scoring, not readiness to draw conclusions from real participants.
