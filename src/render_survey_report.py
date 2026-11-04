"""Render a privacy-conscious Results & Discussion draft from grouped aggregates."""

import argparse
import json
from pathlib import Path


OUTCOMES = (
    ("pss_score", "PSS-10", "0–40 points"),
    ("adapted_cbi_work_score", "Adapted work CBI", "0–100 points"),
    ("productivity_0_10", "Self-rated productivity", "0–10 points"),
)


def format_number(value):
    return "—" if value is None else f"{value:.2f}"


def group_table(report):
    lines = ["| Outcome | n | Mean ± SD | Median | Min–max | Scale |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for key, name, scale in OUTCOMES:
        item = report["descriptive"][key]
        lines.append(f"| {name} | {item['n']} | {format_number(item['mean'])} ± "
                     f"{format_number(item['sd'])} | {format_number(item['median'])} | "
                     f"{format_number(item['min'])}–{format_number(item['max'])} | {scale} |")
    return "\n".join(lines)


def render(report):
    real, synthetic = report["real"], report["synthetic"]
    n_real, n_synthetic = real["n_valid"], synthetic["n_valid"]
    status = ("Small-sample descriptive report: no population inference."
              if n_real < 80 else "Draft: verify methods and diagnostics before inference.")
    real_table = group_table(real) if n_real else "No valid real questionnaires are available."
    synthetic_table = group_table(synthetic) if n_synthetic else "No synthetic fixture was processed."
    flags = ", ".join(f"{name}: {count}" for name, count in real["review_flags"].items()) or "none"
    comm = ", ".join(f"{name}: {count}" for name, count in real.get("communication_frequency", {}).items()) or "none"
    model = real["rq3_model"]
    model_note = ("The RQ3 model was not estimated: " + model["reason"] + "."
                  if model["status"] != "estimated" else
                  "RQ3 coefficients are exploratory and require diagnostics before interpretation.")
    return f"""# 4. Results & Discussion

> **{status}** Real and synthetic questionnaires use the same validation and scoring rules, but are reported as separate groups. Synthetic records are not participants and are never included in a pooled estimate.

## 4.1 Data provenance and quality

Recruitment and response collection took place on **3–4 November 2026** among former colleagues and friends, according to the study owner. Collection is closed; no further responses are expected. This convenience sample limits generalizability. The final export contains {real['n_input']} submitted rows. Of these, {real['n_eligible']} met the two eligibility questions, {real['n_rejected']} eligible rows were rejected for missing or invalid answers, and **{n_real} real questionnaires** were valid for descriptive analysis. The two review-flagged answers ({flags}) were retained as reported at the study owner's direction; their values were not corrected or silently excluded. Consent was obtained before the substantive questions, according to the study owner. The source export is stored privately and is not part of the public repository.

The separate fictional fixture contains {n_synthetic} valid records generated with a fixed seed. It verifies the same question formats and scoring code but contributes no evidence about IT workers. **{n_real} real + {n_synthetic} synthetic is not a research sample of {n_real + n_synthetic}.**

## 4.2 Real responses

**Table 1. Descriptive outcomes for real respondents.** SD is the sample standard deviation of observed answers, not a confidence interval. CBI is an adapted four-answer work score. Values are rounded to two decimals; calculations use unrounded scores.

{real_table}

Communication frequency was recorded categorically: {comm}. The questionnaire does not supply an exact weekly contact count. Work-life balance and schedule flexibility retain their original 1–5 scales.

**Figure 1. Descriptive outcomes in the {n_real} real questionnaires.** Panels show PSS-10 (0–40 points), adapted work CBI (0–100 points), and self-rated productivity (0–10 points). Points are sample means; capped bars show ±1 sample SD, the spread of observed responses, **not** 95% confidence intervals. With this sample, the figure does not support population claims.

![Mean and sample SD of the real survey outcomes](figures/real_survey_outcomes.png) ([vector PDF](figures/real_survey_outcomes.pdf))

## 4.3 Synthetic pipeline check

**Table 2. Fictional answers used only to verify the analysis pipeline.** These rows were generated independently of the human answers with a fixed seed and the completed form's answer options. They must not be compared as a treatment or baseline group.

{synthetic_table}

The executed notebook also produces a local comparison figure at `results/figures/survey_outcomes_by_origin.pdf` and `.png`. Blue circles mark real aggregates and orange squares mark synthetic demonstration aggregates; these sources are never pooled. This comparison figure is kept outside the public report to avoid treating fictional responses as a study baseline.

## 4.4 Interpretation and limitations

{model_note} The RQ2 model is also not estimated because communication is an ordered category and its model specification is unfinished. With {n_real} real answers, these summaries describe only the observed respondents; they do not establish population differences, associations, or causal effects. The adapted CBI form used four combined response options scored 0, 25, 75, and 100; its values are not directly interchangeable with the original five-category CBI scale. Self-reported productivity is not an objective measure of work output.

The closed sample contains {n_real} real questionnaires. The review-flagged answers have been retained by decision, but their plausibility remains a limitation. The methodology and equations are in [`docs/domain_model.md`](../docs/domain_model.md) and [`docs/completed-survey-codebook.md`](../docs/completed-survey-codebook.md).
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/survey_comparison.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/paper_section_4.md"))
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    if not {"real", "synthetic"} <= report.keys():
        raise ValueError("input must be a grouped survey comparison report")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(report), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
