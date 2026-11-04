"""Describe the completed Russian Google Forms survey without changing responses.

Accepts the original CSV or a ZIP containing one CSV. Writes aggregate JSON only.
The form used four combined CBI answers (100, 75, 25, 0), so its burnout
measure is an adapted CBI work score, not the standard five-category scale.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import sys
import zipfile
from collections import Counter
from pathlib import Path

from src.benchmark import fit_models


PSS_VALUES = {"Никогда": 0, "Почти никогда": 1, "Иногда": 2,
              "Часто": 3, "Очень часто": 4}
PSS_REVERSE = {4, 5, 7, 8}
CBI_VALUES = {
    "Никогда / очень редко или совсем незначительно": 0,
    "Иногда или в некоторой степени": 25,
    "Часто или в сильной степени": 75,
    "Постоянно или в очень сильной степени": 100,
}
COMMUNICATION = (
    "Реже", "Примерно раз в неделю", "Несколько раз в неделю",
    "Примерно раз в день", "Несколько раз в день",
)
FIELDS = {
    "it": "2.", "remote_eligibility": "3.", "job_role": "4.",
    "weekly_hours": "5.", "remote_work_percent": "6.",
    "schedule_flexibility_1_5": "7.", "work_life_balance_1_5": "8.",
    "communication_frequency": "9.", "productivity_0_10": "10.",
    "age": "11.", "years_experience": "12.", "gender": "13.",
}


def read_export(path):
    data = path.read_bytes()
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = [m for m in archive.infolist()
                       if not m.is_dir() and m.filename.lower().endswith(".csv")]
            if len(members) != 1:
                raise ValueError("ZIP must contain exactly one CSV")
            if members[0].file_size > 20_000_000:
                raise ValueError("CSV exceeds 20 MB limit")
            data = archive.read(members[0])
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as error:
        raise ValueError("CSV must be UTF-8") from error
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    if not headers or len(headers) != len(set(headers)):
        raise ValueError("missing or duplicate CSV headers")
    rows = [(reader.line_num, row) for row in reader]
    if not rows:
        raise ValueError("CSV has no responses")
    return headers, rows, hashlib.sha256(path.read_bytes()).hexdigest()


def column_map(headers):
    result = {}
    for name, prefix in FIELDS.items():
        matches = [header for header in headers if header.startswith(prefix + " ")]
        if len(matches) != 1:
            raise ValueError(f"expected one column for question {prefix}")
        result[name] = matches[0]
    for family, prefix, count in (("pss", "PSS-10 / ", 10),
                                  ("cbi", "CBI work / ", 7)):
        for number in range(1, count + 1):
            matches = [header for header in headers
                       if header.startswith(f"{prefix}{number:02d} — ")]
            if len(matches) != 1:
                raise ValueError(f"expected one column for {family} item {number:02d}")
            result[f"{family}_{number:02d}"] = matches[0]
    return result


def numeric(value, name, low, high, *, integer=False):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: expected a number") from None
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{name}: expected {low}..{high}")
    if integer and not number.is_integer():
        raise ValueError(f"{name}: expected an integer")
    return int(number) if integer else number


def parse_response(raw, columns):
    def answer(name):
        value = raw.get(columns[name])
        if value is None or not value.strip():
            raise ValueError(f"{name}: missing answer")
        return value.strip()

    values = {}
    for name, lo, hi, integer in (
        ("weekly_hours", 1, 100, False), ("remote_work_percent", 0, 100, False),
        ("schedule_flexibility_1_5", 1, 5, True),
        ("work_life_balance_1_5", 1, 5, True),
        ("productivity_0_10", 0, 10, False), ("age", 18, 80, True),
        ("years_experience", 0, 60, True),
    ):
        values[name] = numeric(answer(name), name, lo, hi, integer=integer)
    if values["remote_work_percent"] == 0:
        raise ValueError("remote_work_percent: must be greater than zero")
    values["job_role"] = answer("job_role")
    values["gender"] = (raw.get(columns["gender"]) or "").strip() or "Не указано"
    communication = answer("communication_frequency")
    if communication not in COMMUNICATION:
        raise ValueError("communication_frequency: unknown category")
    values["communication_frequency"] = communication
    pss = 0
    for number in range(1, 11):
        label = answer(f"pss_{number:02d}")
        if label not in PSS_VALUES:
            raise ValueError(f"pss_{number:02d}: unknown answer")
        code = PSS_VALUES[label]
        pss += 4 - code if number in PSS_REVERSE else code
    cbi_scores = []
    for number in range(1, 8):
        label = answer(f"cbi_{number:02d}")
        if label not in CBI_VALUES:
            raise ValueError(f"cbi_{number:02d}: unknown answer")
        score = CBI_VALUES[label]
        cbi_scores.append(100 - score if number == 7 else score)
    values["pss_score"] = pss
    values["adapted_cbi_work_score"] = statistics.mean(cbi_scores)
    return values


def describe(values):
    ordered = sorted(values)
    n = len(ordered)
    return {"n": n, "mean": round(statistics.mean(ordered), 3),
            "median": round(statistics.median(ordered), 3),
            "sd": round(statistics.stdev(ordered), 3) if n > 1 else None,
            "min": ordered[0], "max": ordered[-1]}


def analyze(path, config, *, origin="unspecified", return_rows=False):
    headers, raw_rows, source_hash = read_export(path)
    columns = column_map(headers)
    rows, rejected = [], []
    excluded = 0
    flags = Counter()
    for line, raw in raw_rows:
        if None in raw:
            rejected.append({"csv_line": line, "reason": "unexpected extra columns"})
            continue
        eligibility = [(raw.get(columns[name]) or "").strip()
                       for name in ("it", "remote_eligibility")]
        if any(answer not in {"Да", "Нет"} for answer in eligibility):
            rejected.append({"csv_line": line, "reason": "eligibility: missing or unknown answer"})
            continue
        if "Нет" in eligibility:
            excluded += 1
            continue
        try:
            row = parse_response(raw, columns)
        except ValueError as error:
            rejected.append({"csv_line": line, "reason": str(error)})
            continue
        rows.append(row)
        if row["weekly_hours"] >= 80:
            flags["weekly_hours_ge_80_review"] += 1
        if row["years_experience"] > row["age"] - 16:
            flags["experience_exceeds_age_minus_16_review"] += 1
    eligible = len(raw_rows) - excluded
    rejection_rate = len(rejected) / eligible if eligible else None
    quality_pass = bool(eligible and rejection_rate <= config["quality"]["max_rejection_rate"])
    result = {
        "origin": origin,
        "source_file": path.name, "source_sha256": source_hash,
        "survey_version": "completed_form_with_four_option_cbi",
        "consent": "obtained before substantive questions, per study owner",
        "n_input": len(raw_rows), "n_eligible": eligible,
        "n_excluded_eligibility": excluded, "n_valid": len(rows),
        "n_rejected": len(rejected), "rejections": rejected,
        "rejection_rate_among_eligible": (round(rejection_rate, 4)
                                          if rejection_rate is not None else None),
        "quality_pass": quality_pass, "review_flags": dict(flags),
        "scoring": {
            "pss_10": "standard 0..40; items 4, 5, 7, 8 reversed",
            "cbi_work": "adapted four-answer form: 0, 25, 75, 100; item 7 reversed; not standard five-answer CBI",
            "communication": "ordered categories; no conversion to contacts per week",
            "flexibility_and_balance": "original 1..5 ratings; no rescaling to 0..10",
        },
    }
    if rows:
        result["descriptive"] = {
            name: describe([row[name] for row in rows])
            for name in ("pss_score", "adapted_cbi_work_score", "productivity_0_10",
                         "weekly_hours", "remote_work_percent",
                         "schedule_flexibility_1_5", "work_life_balance_1_5")
        }
        counts = Counter(row["communication_frequency"] for row in rows)
        result["communication_frequency"] = {
            label: counts[label] for label in COMMUNICATION if counts[label]
        }
        result["job_role_counts"] = dict(Counter(row["job_role"] for row in rows))
    threshold = config["quality"]["minimum_complete_cases_for_model"]
    if len(rows) >= threshold and quality_pass:
        try:
            model_rows = [{**row, "cbi_work_score": row["adapted_cbi_work_score"]}
                          for row in rows]
            result["rq3_model"] = fit_models(model_rows, config)
            result["rq3_model"]["measure_note"] = "adapted CBI score; observational associations only"
        except ValueError as error:
            result["rq3_model"] = {"status": "not_estimated", "reason": str(error)}
    else:
        result["rq3_model"] = {
            "status": "not_estimated",
            "reason": f"requires >= {threshold} valid answers and passing quality checks",
        }
    result["rq2_model"] = {"status": "not_estimated",
                           "reason": "categorical communication requires a prespecified RQ2 model"}
    result["interpretation"] = ("Descriptive values only; no population inference or causal claim"
                                 if len(rows) < threshold else
                                 "Associations require diagnostics and a prespecified analysis protocol")
    return (result, rows) if return_rows else result


def write_labeled_rows(path, real_rows, synthetic_rows):
    """Write a private, timestamp-free table with explicit record provenance."""
    fields = ("origin", "record_id", "age", "gender", "years_experience", "job_role",
              "weekly_hours", "remote_work_percent", "schedule_flexibility_1_5",
              "work_life_balance_1_5", "communication_frequency", "productivity_0_10",
              "pss_score", "adapted_cbi_work_score")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for origin, prefix, records in (("real", "R", real_rows),
                                        ("synthetic", "S", synthetic_rows)):
            for index, row in enumerate(records, 1):
                writer.writerow({"origin": origin, "record_id": f"{prefix}{index:03d}",
                                 **{key: row[key] for key in fields if key in row}})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="original CSV or ZIP export")
    parser.add_argument("--synthetic-input", type=Path,
                        help="fictional answers in the same completed-form schema")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--output", type=Path, default=Path("results/survey_summary.json"))
    parser.add_argument("--records-output", type=Path,
                        default=Path("results/survey_records_labeled.csv"))
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if args.synthetic_input:
            real_report, real_rows = analyze(args.input, config, origin="real", return_rows=True)
            synthetic_report, synthetic_rows = analyze(args.synthetic_input, config,
                                                       origin="synthetic", return_rows=True)
            write_labeled_rows(args.records_output, real_rows, synthetic_rows)
            report = {
                "schema": "completed_survey_as_administered",
                "n_labeled_records": len(real_rows) + len(synthetic_rows),
                "real": real_report,
                "synthetic": synthetic_report,
                "records_file": str(args.records_output),
                "pooled_statistics": "not_computed; synthetic answers are not human observations",
            }
        else:
            report = analyze(args.input, config, origin="real")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
                               + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print(f"Survey analysis failed: {error}", file=sys.stderr)
        return 1
    if args.synthetic_input:
        print(f"Wrote {args.output} and {args.records_output}; "
              f"real={report['real']['n_valid']}; synthetic={report['synthetic']['n_valid']}")
    else:
        print(f"Wrote {args.output}; valid={report['n_valid']}/{report['n_input']}; "
              f"RQ3={report['rq3_model']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
