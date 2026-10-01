# Remote IT Work, Burnout, Stress and Productivity

**Author:** Asanali Talgat  
**Research design:** quantitative, observational, cross-sectional survey  
**Repository:** add the public GitHub URL after publication  
**Research question:** How are remote-work conditions associated with stress and work-related burnout among IT specialists, and how are these outcomes related to self-reported productivity?

## Overview

This Week 6 pilot validates a small **synthetic** CSV, scores PSS-10 and the work-related subscale of the Copenhagen Burnout Inventory (CBI), reports data-quality indicators and descriptive means, and writes JSON output. It estimates the prespecified productivity models only when at least 80 complete, valid responses pass quality checks. The synthetic examples are not human-subject data and do not support research conclusions.

The primary planned effect is the adjusted coefficient for **10 additional CBI work-related burnout points** in a productivity model. The baseline uses age, years of experience, weekly hours, gender, job role, and PSS-10 stress; the full model adds burnout. RQ2 will separately examine working hours, work-life balance, communication frequency and schedule flexibility in models for stress and burnout once real responses exist. Associations from a cross-sectional survey are not causal effects.

## System requirements and quickstart

- Python **3.12.14**; the runner uses only the Python standard library, so there are no pip packages.
- From the repository root, run:

```bash
python3 -m src.benchmark --config config.json --input data/sample/pilot_synthetic.csv --output results/pilot_summary.json
python3 -m unittest discover -s tests -v
```

The first command writes `results/pilot_summary.json` and prints the valid-response count. With eight artificial records, `primary_model.status` is `not_estimated` by design. Invalid rows are listed with their CSV line numbers; a malformed header fails clearly. The second command checks scale reversal, input validation, pilot output and recovery of a known simulated regression coefficient.

Optional Docker run:

```bash
docker build -t remote-it-wellbeing-study .
docker run --rm remote-it-wellbeing-study
```

The image pins the Python base image tag to `3.12.14-slim-bookworm`; it runs the same tests during build. No Docker build has been run in this workspace because the Docker CLI is unavailable here.

## Layout

```text
remote-it-wellbeing-study/
├── README.md, LICENSE, Dockerfile, .gitignore, .dockerignore
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
| Full study RQ3 | Primary: burnout beta per 10 points and approximate 95% CI; secondary: change in R² and stress coefficient | Controls + stress versus controls + stress + burnout | Only if quality and sample gates pass |

**Guardrails:** rejection rate at most 10%; at least 80 complete cases before model estimation; finite bounded responses and unique respondent IDs. The 80-case gate is a provisional engineering safeguard, **not** a power calculation. A final sample-size and sensitivity plan should be specified before recruitment. The current confidence interval uses classical OLS standard errors and needs diagnostic checks on real responses.

## Data and instrument notes

- PSS-10 items `pss_01..pss_10` are numeric 0–4. Items 4, 5, 7 and 8 are reverse coded. Sum ranges from 0 to 40. [Original scoring instructions](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/html/pssscoring.html).
- Work-related CBI items `cbi_01..cbi_07` are entered as 0–4 from least to most frequent/intense, multiplied by 25 and averaged; item 7, about energy for family and friends, is reversed. The first three and last four questions have different verbal anchors in the [original instrument](https://nfa.dk/media/a4wheblj/cbi-scales.pdf); survey wording must preserve them. This repository contains only answer codes, not the questionnaire text.
- `productivity_0_10` is a single, explicitly self-reported rating. It is not an objective measure of software output and has not been validated as a stand-alone scale.
- Real survey responses must be collected with appropriate consent, stored outside the public repository, and analysed only in de-identified form. The included CSV is fictional.

## Citation and license

Study protocol: Talgat, A. (2026). *Remote IT Work, Burnout, Stress and Productivity: Methodology Passport and Pilot Pipeline* (course project).  
PSS-10: Cohen, S., Kamarck, T., & Mermelstein, R. (1983), *Journal of Health and Social Behavior*, 24(4), 385–396.  
CBI: Kristensen, T. S., Borritz, M., Villadsen, E., & Christensen, K. B. (2005), *Work & Stress*, 19(3), 192–207.

Code is released under the [MIT License](LICENSE). The license does not override permissions for third-party questionnaires; check questionnaire permissions before distributing survey materials.

