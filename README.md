# Associations Between Remote IT Work Conditions, Stress, Burnout and Self-Reported Productivity

**Author:** Asanali Talgat  
**Research design:** quantitative, observational, cross-sectional survey  
**Repository:** https://github.com/Asanalishka/remote-it-wellbeing-study

**Research question:** How are remote-work conditions associated with stress and work-related burnout among IT specialists, and how are these outcomes related to self-reported productivity?

## Overview

This Week 6 pilot validates a small **synthetic** CSV, scores PSS-10 and the work-related subscale of the Copenhagen Burnout Inventory (CBI), reports data-quality indicators and descriptive means, and writes JSON output. It estimates the prespecified productivity models only when at least 80 complete, valid responses pass quality checks. The synthetic examples are not human-subject data and do not support research conclusions.

The primary planned association is the adjusted coefficient for **10 additional CBI work-related burnout points** in a productivity model. The baseline uses age, years of experience, weekly hours, gender, job role, and PSS-10 stress; the full model adds burnout. RQ2 will separately examine working hours, work-life balance, communication frequency and schedule flexibility in models for stress and burnout once its analysis protocol is finalized and real responses exist. Associations from a cross-sectional survey are not causal effects.

The model formulas are fixed in `src/benchmark.py`. `config.json` controls input/output paths, instrument column mappings, quality thresholds and the confidence-interval multiplier (default `1.96` for an approximate two-sided 95% interval; retain this value for the documented output). The secondary stress coefficient is from the **baseline** model and is exported as `primary_model.baseline_stress_beta_per_point`, per one PSS-10 point.

## System requirements and quickstart

- Python **3.12.14**; the runner uses only the Python standard library, so there are no pip packages.
- Clone or download the repository, then run these commands from its root directory:

```bash
python3 -m src.benchmark --config config.json --input data/sample/pilot_synthetic.csv --output results/pilot_summary.json
python3 -m unittest discover -s tests -v
```

The first command writes `results/pilot_summary.json` and prints `valid=8/8; model=not_estimated`. Expected JSON fields include `n_input: 8`, `n_valid: 8`, `n_rejected: 0`, `quality_pass: true`, and `primary_model.status: "not_estimated"`. With eight artificial records, model estimation is disabled by design. Invalid rows are listed with their CSV line numbers; a malformed header or empty file fails with a nonzero exit code. IDs are trimmed before duplicate detection; later valid rows with the same ID are rejected. The second command checks scale scoring, malformed input, quality gates, pilot output and recovery of known simulated regression coefficients.

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
| Week 6 pilot | Valid rows; rejected-row rate; PSS-10 (0–40); work CBI (0–100); productivity (0–10) | Scoring rules and input ranges | `results/pilot_summary.json` |
| Full study RQ2 | Adjusted associations of hours, balance, communication and flexibility with stress and burnout | Models controlling for age, gender, experience and role | Regression summary, after real data collection |
| Full study RQ3 | Primary: burnout beta per 10 points and approximate 95% CI; secondary: change in R² and baseline stress coefficient | Controls + stress versus controls + stress + burnout | Only if quality and sample gates pass |

**Guardrails:** rejection rate at most 10%; at least 80 complete cases before model estimation; finite bounded responses and unique respondent IDs. The 80-case gate is a provisional engineering safeguard, **not** a power calculation. A final sample-size and sensitivity plan should be specified before recruitment. The current confidence interval uses classical OLS standard errors and needs diagnostic checks on real responses.

**Inference boundary:** the planned RQ3 test is one-sided at α = 0.05. The pilot reports an approximate two-sided 95% interval and does not implement that hypothesis test or claim significance. Before recruitment, finalize sample-size justification, the missing-data policy, the RQ2 testing/multiple-comparison protocol, and the final questionnaire and eligibility criteria. RQ2 estimation and full descriptive distributions are Week 7 work; the Week 6 pilot reports descriptive means.

## Data and instrument notes

- PSS-10 items `pss_01..pss_10` are numeric 0–4. Items 4, 5, 7 and 8 are reverse coded. Sum ranges from 0 to 40. [Original scoring instructions](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/html/pssscoring.html).
- Work-related CBI items `cbi_01..cbi_07` are entered as 0–4 from least to most frequent/intense, multiplied by 25 and averaged; item 7, about energy for family and friends, is reversed. The first three and last four questions have different verbal anchors in the [original instrument](https://nfa.dk/media/a4wheblj/cbi-scales.pdf); survey wording must preserve them. This repository contains only answer codes, not the questionnaire text.
- `productivity_0_10` is a single, explicitly self-reported rating. It is not an objective measure of software output and has not been validated as a stand-alone scale.
- Real survey responses must be collected with appropriate consent, stored outside the public repository, and analysed only in de-identified form. The included CSV is fictional.

## Citation and license

Study protocol: Talgat, A. (2026). *Associations Between Remote IT Work Conditions, Stress, Burnout and Self-Reported Productivity* (course project; methodology passport and pilot pipeline).

PSS-10: Cohen, S., Kamarck, T., & Mermelstein, R. (1983), *Journal of Health and Social Behavior*, 24(4), 385–396.  
CBI: Kristensen, T. S., Borritz, M., Villadsen, E., & Christensen, K. B. (2005), *Work & Stress*, 19(3), 192–207.

Code is released under the [MIT License](LICENSE). The license does not override permissions for third-party questionnaires; check questionnaire permissions before distributing survey materials.
