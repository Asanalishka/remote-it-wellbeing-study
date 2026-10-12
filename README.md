# Associations Between Remote IT Work Conditions, Stress, Burnout and Self-Reported Productivity

**Author:** Asanali Talgat  
**Research design:** quantitative, observational, cross-sectional survey  
**Repository:** https://github.com/Asanalishka/remote-it-wellbeing-study

**Research question:** How are remote-work conditions associated with stress and work-related burnout among IT specialists, and how are these outcomes related to self-reported productivity?

## Overview

This Week 6 pilot validates a small **synthetic** CSV, scores PSS-10 and the work-related subscale of the Copenhagen Burnout Inventory (CBI), reports data-quality indicators and descriptive means, and writes JSON output. It estimates the prespecified productivity models only when at least 80 complete, valid responses pass quality checks. The synthetic examples are not human-subject data and do not support research conclusions.

The primary planned association is the adjusted coefficient for **10 additional CBI work-related burnout points** in a productivity model. RQ3 also requires the stress coefficient from that same full model: `productivity = intercept + beta_burnout * (CBI / 10) + beta_stress * PSS + covariates + error`. Covariates are age, years of experience, weekly hours, gender and job role. The baseline includes these covariates and stress; the full model adds burnout, so ΔR² represents burnout's additional contribution. Associations from a cross-sectional survey are not causal effects.

Aligned with Task 1, RQ1 describes outcome levels and plans secondary comparisons with mathematical scale midpoints (20, 50 and 5). RQ2 will model stress and burnout and compare adjusted predictions across **observed combinations of working hours, work-life balance, communication frequency and schedule flexibility**, after its protocol is finalized and real data are collected. Predictions do not establish a causal optimum and will not be extrapolated to unobserved work regimes. `remote_work_percent` describes the sample; it is not a regression covariate or one of the four RQ2 predictors.

The model formulas are fixed in `src/benchmark.py`. `config.json` controls input/output paths, instrument column mappings, quality thresholds and the confidence-interval multiplier (default `1.96` for an approximate two-sided 95% interval; retain this value for the documented output). When model estimation is enabled, `primary_model` retains all previous fields and adds `full_stress_beta_per_point`, `full_stress_beta_standard_error` and `full_stress_beta_approx_95pct_ci`. These describe stress per one PSS-10 point **after adjustment for burnout**. `baseline_stress_beta_per_point` remains available for comparison; it does not adjust for burnout.

## System requirements and quickstart

- Python **3.12.14**; the runner uses only the Python standard library, so there are no pip packages.
- Clone or download the repository, then run these commands from its root directory:

```bash
python3 -m src.benchmark --config config.json --input data/sample/pilot_synthetic.csv --output results/pilot_summary.json
python3 -m unittest discover -s tests -v
```

The first command writes `results/pilot_summary.json` and prints `valid=8/8; model=not_estimated`. Expected JSON fields include `n_input: 8`, `n_valid: 8`, `n_rejected: 0`, `quality_pass: true`, `descriptive.remote_work_percent: 78.438`, and `primary_model.status: "not_estimated"`. Descriptive fields are means of valid records. With eight artificial records, model estimation is disabled by design. Invalid rows are listed with their CSV line numbers; a malformed header or empty file fails with a nonzero exit code. IDs are trimmed before duplicate detection; later valid rows with the same ID are rejected. The second command checks scale scoring, malformed input, remote-work percentages, quality gates, pilot output and recovery of both full-model coefficients with correlated predictors.

Docker quickstart (Docker Engine or running Docker Desktop required; commands below use a POSIX shell on macOS/Linux):

```bash
docker build -t remote-it-wellbeing-study .
mkdir -p results
docker run --rm --mount "type=bind,source=$(pwd)/results,target=/app/results" remote-it-wellbeing-study
```

The image pins Python `3.12.14-slim-bookworm` by tag and immutable multi-platform digest; it runs the same tests during build. The bind mount preserves `results/pilot_summary.json` on the host after the container exits. Only the configuration, source, tests and synthetic sample are copied into the image. The Docker CLI is unavailable in the local authoring workspace; [Pilot verification in GitHub Actions](https://github.com/Asanalishka/remote-it-wellbeing-study/actions/workflows/pilot.yml) builds the container, runs the tests and checks the persisted JSON on pushes and pull requests.

## Layout

```text
remote-it-wellbeing-study/
├── README.md, LICENSE, Dockerfile, .gitignore, .dockerignore
├── .github/workflows/pilot.yml   # container build, tests and persisted-output check
├── config.json                  # thresholds, variable mappings and paths
├── docs/methodology-card.md    # hypothesis, variables, baseline and validity
├── data/sample/pilot_synthetic.csv  # eight fictional responses only
├── src/benchmark.py            # validation, scale scoring and baseline model
├── tests/test_benchmark.py     # executable tests
├── notebooks/                  # later exploratory analysis
└── results/                    # generated JSON ignored by Git
```

## Planned evaluation

| Stage | Metric | Baseline / comparison | Output |
| --- | --- | --- | --- |
| Week 6 pilot | Valid rows; rejected-row rate; mean PSS-10 (0–40), work CBI (0–100), productivity (0–10) and remote-work percentage (>0–100) | Scoring rules and input ranges | `results/pilot_summary.json`; no sample inference |
| Full study RQ1 | Outcome distributions; secondary comparisons of means with 20, 50 and 5 | Mathematical scale midpoints, not clinical norms | Three two-sided tests with Holm adjustment; Week 7 implementation |
| Full study RQ2 | Adjusted associations and predicted stress/burnout across observed combinations of hours, balance, communication and flexibility | Models controlling for age, gender, experience and role | Regression and prediction summaries; Week 7 implementation |
| RQ3 estimation | Primary: burnout beta per 10 points; required secondary: full-model stress beta per PSS point; approximate 95% intervals; change in R² | Covariates + stress versus covariates + stress + burnout, on identical cases | Implemented; only if quality and sample gates pass |
| Full study RQ3 inference | Negative stress and/or burnout association in the full model | H0: both coefficients nonnegative; H1: at least one negative | Two one-sided tests with Holm adjustment; Week 7 implementation |

**Guardrails:** rejection rate at most 10%; at least 80 complete cases before model estimation; finite bounded responses and unique respondent IDs. The 80-case gate is a provisional engineering safeguard, **not** a power calculation. A final sample-size and sensitivity plan should be specified before recruitment. The current confidence interval uses classical OLS standard errors and needs diagnostic checks on real responses.

**Inference boundary:** the planned three two-sided RQ1 tests and two one-sided RQ3 tests use Holm adjustment in separate families, each at family-wise α = 0.05. The pilot reports approximate two-sided 95% intervals without multiplicity adjustment; it implements neither family of tests and claims no significance. Burnout's primary reporting status does not remove stress from RQ3 or bypass the two-test adjustment. Before recruitment, finalize sample-size justification, missing-data handling, individual test methods, the RQ2 testing/prediction protocol, and questionnaire/eligibility rules. Full distributions, hypothesis tests and RQ2 estimation remain Week 7 work.

## Data and instrument notes

- **Input-format update:** `remote_work_percent` is now required. It means the self-reported percentage of working hours performed remotely in a usual working week; finite values must be greater than 0 and at most 100, with fractions allowed. All eight sample values are fictional. CSVs without this column fail clearly; no value is imputed. A days-per-week field is not required and is not accepted as a substitute. Days cannot be converted into hour percentages without information about working-day lengths. Final survey wording must be frozen before recruitment.
- PSS-10 items `pss_01..pss_10` are numeric 0–4. Items 4, 5, 7 and 8 are reverse coded. Sum ranges from 0 to 40. [Original scoring instructions](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/html/pssscoring.html).
- Work-related CBI items `cbi_01..cbi_07` are entered as 0–4 from least to most frequent/intense, multiplied by 25 and averaged; item 7, about energy for family and friends, is reversed. The first three and last four questions have different verbal anchors in the [original instrument](https://nfa.dk/media/a4wheblj/cbi-scales.pdf); survey wording must preserve them. This repository contains only answer codes, not the questionnaire text.
- `productivity_0_10` is a single, explicitly self-reported rating. It is not an objective measure of software output and has not been validated as a stand-alone scale.
- Real survey responses must be collected with appropriate consent, stored outside the public repository, and analysed only in de-identified form. The included CSV is fictional.

## Citation and license

Study protocol: Talgat, A. (2026). *Associations Between Remote IT Work Conditions, Stress, Burnout and Self-Reported Productivity* (course project; methodology passport and pilot pipeline).

PSS-10: Cohen, S., Kamarck, T., & Mermelstein, R. (1983), *Journal of Health and Social Behavior*, 24(4), 385–396.  
CBI: Kristensen, T. S., Borritz, M., Villadsen, E., & Christensen, K. B. (2005), *Work & Stress*, 19(3), 192–207.

Code is released under the [MIT License](LICENSE). The license does not override permissions for third-party questionnaires; check questionnaire permissions before distributing survey materials.
