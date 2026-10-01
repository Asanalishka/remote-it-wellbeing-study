"""Validate synthetic pilot responses, score scales, and estimate models when eligible."""

import argparse
import csv
import json
import math
import sys
from pathlib import Path


REQUIRED = ("respondent_id", "age", "gender", "years_experience", "job_role",
            "weekly_hours", "work_life_balance_0_10", "communication_per_week",
            "schedule_flexibility_0_10", "productivity_0_10")
GENDERS = {"woman", "man", "nonbinary", "prefer_not_to_say"}
ROLES = {"developer", "qa", "devops", "manager", "other"}


def number(value, name, low, high, *, integer=False):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: expected a number") from None
    if not math.isfinite(value) or not low <= value <= high or (integer and not value.is_integer()):
        raise ValueError(f"{name}: expected {'integer ' if integer else ''}{low}..{high}")
    return int(value) if integer else value


def score_pss(row, config):
    names = config["variables"]["pss_items"]
    reversed_names = set(config["variables"]["pss_reverse"])
    return sum(4 - number(row[k], k, 0, 4, integer=True) if k in reversed_names
               else number(row[k], k, 0, 4, integer=True) for k in names)


def score_cbi_work(row, config):
    names = config["variables"]["cbi_work_items"]
    reverse = config["variables"]["cbi_reverse"]
    # Raw coding: 0=lowest degree / never, 4=highest degree / always.
    # Item 7 asks about energy and must be reversed.
    return sum((4 - number(row[k], k, 0, 4, integer=True) if k == reverse
                else number(row[k], k, 0, 4, integer=True)) * 25 for k in names) / len(names)


def validate_and_score(row, config):
    if not row["respondent_id"].strip():
        raise ValueError("respondent_id: empty")
    for key, allowed in (("gender", GENDERS), ("job_role", ROLES)):
        if row[key] not in allowed:
            raise ValueError(f"{key}: expected one of {sorted(allowed)}")
    ranges = {"age": (18, 80), "years_experience": (0, 60),
              "weekly_hours": (1, 100), "work_life_balance_0_10": (0, 10),
              "communication_per_week": (0, 100),
              "schedule_flexibility_0_10": (0, 10), "productivity_0_10": (0, 10)}
    numeric = {name: number(row[name], name, *bounds) for name, bounds in ranges.items()}
    if numeric["years_experience"] > numeric["age"] - 16:
        raise ValueError("years_experience: exceeds plausible working years")
    return {**row, **numeric, "pss_score": score_pss(row, config),
            "cbi_work_score": score_cbi_work(row, config)}


def solve(matrix, vector):
    """Gauss-Jordan solve; raises on non-identifiable designs."""
    n = len(vector)
    aug = [list(matrix[i]) + [vector[i]] for i in range(n)]
    for j in range(n):
        pivot = max(range(j, n), key=lambda i: abs(aug[i][j]))
        if abs(aug[pivot][j]) < 1e-10:
            raise ValueError("singular design; reduce collinear predictors")
        aug[j], aug[pivot] = aug[pivot], aug[j]
        scale = aug[j][j]
        aug[j] = [x / scale for x in aug[j]]
        for i in range(n):
            if i != j:
                factor = aug[i][j]
                aug[i] = [a - factor * b for a, b in zip(aug[i], aug[j])]
    return [r[-1] for r in aug]


def ols(x, y, target_index=None, z=1.96):
    n, p = len(y), len(x[0])
    if n <= p:
        raise ValueError("more complete cases than coefficients required")
    gram = [[sum(r[i] * r[j] for r in x) for j in range(p)] for i in range(p)]
    cross = [sum(r[j] * yy for r, yy in zip(x, y)) for j in range(p)]
    beta = solve(gram, cross)
    residuals = [yy - sum(b * xx for b, xx in zip(beta, row)) for row, yy in zip(x, y)]
    rss = sum(e * e for e in residuals)
    tss = sum((yy - sum(y) / n) ** 2 for yy in y)
    if tss <= 1e-12:
        raise ValueError("outcome has no variation")
    result = {"r_squared": round(1 - rss / tss, 5)}
    if target_index is not None:
        unit = [float(j == target_index) for j in range(p)]
        inv_column = solve(gram, unit)
        se = math.sqrt(max(0, rss / (n - p) * inv_column[target_index]))
        b = beta[target_index]
        result.update({"beta": round(b, 5), "standard_error": round(se, 5),
                       "approx_95pct_ci": [round(b - z * se, 5), round(b + z * se, 5)],
                       "standard_error_method": "classical OLS; assumes homoskedastic residuals"})
    return result


def fit_models(rows, config):
    y = [r["productivity_0_10"] for r in rows]
    # Use a reference category present in the analysed sample.
    genders = sorted({r["gender"] for r in rows})[1:]
    roles = sorted({r["job_role"] for r in rows})[1:]
    def baseline(r):
        return [1.0, r["age"], r["years_experience"], r["weekly_hours"],
                *[float(r["gender"] == g) for g in genders],
                *[float(r["job_role"] == role) for role in roles], r["pss_score"]]
    x0 = [baseline(r) for r in rows]
    x1 = [baseline(r) + [r["cbi_work_score"] / 10] for r in rows]
    base = ols(x0, y)
    full = ols(x1, y, target_index=len(x1[0]) - 1, z=config["analysis"]["confidence_z"])
    return {"status": "estimated", "n": len(rows), "baseline_r_squared": base["r_squared"],
            "full_r_squared": full["r_squared"],
            "delta_r_squared": round(full["r_squared"] - base["r_squared"], 5),
            "burnout_beta_per_10_points": full["beta"],
            "burnout_beta_standard_error": full["standard_error"],
            "burnout_beta_approx_95pct_ci": full["approx_95pct_ci"],
            "uncertainty_note": full["standard_error_method"]}


def run(config_path, input_path, output_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    with input_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        columns = set(reader.fieldnames or [])
        expected = set(REQUIRED + tuple(config["variables"]["pss_items"])
                       + tuple(config["variables"]["cbi_work_items"]))
        missing = expected - columns
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        raw = list(reader)
    if not raw:
        raise ValueError("CSV has no responses")
    seen, clean, rejected = set(), [], []
    for line, row in enumerate(raw, start=2):
        try:
            if None in row:
                raise ValueError("unexpected extra columns")
            scored = validate_and_score(row, config)
            key = scored["respondent_id"]
            if key in seen:
                raise ValueError("duplicate respondent_id")
            seen.add(key)
            clean.append(scored)
        except ValueError as error:
            rejected.append({"csv_line": line, "reason": str(error)})
    rate = len(rejected) / len(raw)
    result = {"source": str(input_path), "synthetic_demo": "sample" in input_path.parts,
              "n_input": len(raw), "n_valid": len(clean), "n_rejected": len(rejected),
              "rejection_rate": round(rate, 4), "rejections": rejected,
              "quality_pass": rate <= config["quality"]["max_rejection_rate"]}
    if clean:
        result["descriptive"] = {
            k: round(sum(r[k] for r in clean) / len(clean), 3)
            for k in ("pss_score", "cbi_work_score", "productivity_0_10")}
    n_min = config["quality"]["minimum_complete_cases_for_model"]
    if len(clean) >= n_min and result["quality_pass"]:
        try:
            result["primary_model"] = fit_models(clean, config)
        except ValueError as error:
            result["primary_model"] = {"status": "not_estimated", "reason": str(error)}
    else:
        result["primary_model"] = {"status": "not_estimated",
                                   "reason": f"requires >= {n_min} valid responses and passing quality checks"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}; valid={len(clean)}/{len(raw)}; model={result['primary_model']['status']}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        input_path = args.input or Path(config["input"])
        output_path = args.output or Path(config["output"])
        run(args.config, input_path, output_path)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Benchmark failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
