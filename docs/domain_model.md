# Mathematical model of the completed survey

This study is a cross-sectional questionnaire, not a performance benchmark. Its domain model describes eligibility, scale scoring, aggregate metrics, and the planned association model. Recruitment and response collection among former colleagues and friends took place on 3–4 November 2026; the study owner confirmed that collection is closed. The final five human responses support descriptive summaries only. Both review-flagged human answers were retained without alteration by the study owner's decision. The 75 synthetic responses validate the pipeline and are never pooled with human responses. The research sample size is five, not 80.

## Notation

| Symbol | Meaning | Unit / range |
| --- | --- | --- |
| \(\mathcal R\), \(\mathcal S\) | Sets of valid real and synthetic questionnaires | Respondents; disjoint groups |
| \(N_g\) | Number of valid questionnaires in group \(g\in\{\mathcal R,\mathcal S\}\) | Persons / records |
| \(p_{ij}\) | PSS-10 answer code for respondent \(i\), item \(j\) | Integer 0–4 |
| \(c_{ij}\) | Adapted CBI answer score for respondent \(i\), item \(j\) | 0, 25, 75, or 100 points |
| \(P_i\) | PSS-10 total | 0–40 points |
| \(B_i\) | Adapted work-related burnout score | 0–100 points |
| \(Y_i\) | Self-reported productivity | 0–10 points |
| \(H_i\) | Mean weekly working hours | Hours/week |
| \(L_i,F_i\) | Work-life balance and schedule flexibility | Ratings 1–5 |
| \(C_i\) | Communication frequency | Ordered category, not a weekly count |

## Eligibility and scoring

A record is eligible only if the respondent answered “Да” to both current IT employment and remote work in the last four weeks. A valid record also has all required item answers in their administered ranges. Invalid answers are reported with CSV line numbers; unusual hours or experience are flagged for review without automatic exclusion. Let \(V_i\) be 1 for an eligible, complete, valid record and 0 otherwise.

For PSS-10, reverse-code items \(J_+=\{4,5,7,8\}\):

\[
P_i=\sum_{j=1}^{10}\begin{cases}4-p_{ij},&j\in J_+,\\p_{ij},&j\notin J_+.\end{cases}
\]

The administered form offered four combined CBI answers with scores 0, 25, 75, and 100. Item 7 is reverse-coded:

\[
B_i=\frac{1}{7}\left(\sum_{j=1}^{6}c_{ij}+100-c_{i7}\right).
\]

This is an **adapted CBI work score**. The original CBI work subscale uses five answer categories, including a 50-point response, and separate degree/frequency anchors. The unoffered 50-point answer is not imputed. See the [completed-survey codebook](completed-survey-codebook.md) and the [original CBI instrument](https://nfa.dk/media/a4wheblj/cbi-scales.pdf).

## Grouped descriptive metrics

For each outcome \(X_i\in\{P_i,B_i,Y_i\}\) and each origin group \(g\), calculate:

\[
\bar X_g=\frac{1}{N_g}\sum_{i\in g}X_i,\qquad
s_g=\sqrt{\frac{1}{N_g-1}\sum_{i\in g}(X_i-\bar X_g)^2}\quad(N_g>1).
\]

Also report the median, minimum, maximum, and valid count. Communication is summarized by category counts. Report the rejected-eligible fraction as \(N_{\mathrm{rejected}}/N_{\mathrm{eligible}}\). No statistic uses \(\mathcal R\cup\mathcal S\) as a single research sample. A plot of mean ± SD shows **observed spread**, not a confidence interval. With only five real answers, uncertainty about a population mean is too large for a useful inferential claim.

## Planned association model, not estimated for the current sample

The protocol's RQ3 model for real respondents only is:

\[
Y_i=\beta_0+\beta_B\frac{B_i}{10}+\beta_P P_i+\boldsymbol\gamma^\top\mathbf Z_i+\varepsilon_i,
\]

where \(\mathbf Z_i\) contains age, gender, IT experience, job role, and weekly hours. Its ordinary least-squares objective would be \(\min_{\boldsymbol\theta}\sum_{i\in\mathcal R}(Y_i-\hat Y_i)^2\). The existing 80-case guardrail is a software threshold, not a power justification. RQ2 additionally needs a model that treats \(C_i\) as categorical. Both require adequate real data, prespecified methods, and diagnostics before interpretation. A cross-sectional self-report model estimates associations, not causal effects.
