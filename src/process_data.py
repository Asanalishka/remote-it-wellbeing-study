"""Reproducible descriptive processing for the synthetic survey studio."""

import argparse
import hashlib
import json
import platform
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from src.benchmark import load_responses


NOTICE = "Synthetic data — pipeline check, not research findings"
METRICS = ("pss_score", "cbi_work_score", "productivity_0_10")
SEED = 42
N_BOOT = 10_000


def summarize(frame):
    """Keep every valid row; flag IQR extremes and bootstrap respondent rows."""
    clean = frame.copy()
    n = len(clean)
    if not n:
        raise ValueError("no valid responses")
    # One shared resampling of whole respondents preserves the paired outcomes.
    rng = np.random.Generator(np.random.PCG64(SEED))
    means = None
    if n > 1:
        values = clean.loc[:, list(METRICS)].to_numpy(dtype=float)
        means = np.empty((N_BOOT, len(METRICS)))
        for start in range(0, N_BOOT, 100):
            stop = min(start + 100, N_BOOT)
            indices = rng.integers(0, n, size=(stop - start, n))
            means[start:stop] = values[indices].mean(axis=1)
    records = []
    for i, metric in enumerate(METRICS):
        series = clean[metric].astype(float)
        q = series.quantile([.25, .5, .75, .95, .99], interpolation="linear")
        iqr = q.loc[.75] - q.loc[.25]
        lower, upper = q.loc[.25] - 1.5 * iqr, q.loc[.75] + 1.5 * iqr
        flag = (series < lower) | (series > upper)
        clean[f"{metric}_iqr_flag"] = flag
        ci = (np.quantile(means[:, i], [.025, .975], method="linear")
              if means is not None else [np.nan, np.nan])
        records.append({
            "metric": metric, "unit": "points", "n": n,
            "mean": series.mean(), "sd": series.std(ddof=1),
            "p25": q.loc[.25], "p50": q.loc[.5], "p75": q.loc[.75],
            "p95": q.loc[.95], "p99": q.loc[.99],
            "mean_ci95_low": ci[0], "mean_ci95_high": ci[1],
            "iqr_lower_fence": lower, "iqr_upper_fence": upper,
            "n_iqr_flagged": int(flag.sum()),
            "ci_status": "educational_only" if n > 1 else "unavailable_n_lt_2",
            "synthetic_demo": True, "notice": NOTICE,
            "tail_percentile_note": "Unstable with eight observations; descriptive only",
        })
    clean["synthetic_demo"] = True
    clean["notice"] = NOTICE
    return clean, pd.DataFrame(records)


def write_report(path, report):
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
                    + "\n", encoding="utf-8")


def process(config_path, input_path, output_dir):
    """Process synthetic survey data; this studio is not a real-data workflow."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "quality_report.json"
    report = {
        "synthetic_demo": True, "notice": NOTICE, "source": str(input_path),
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "versions": {"python": platform.python_version(),
                     **{name: version(name) for name in ("numpy", "pandas", "matplotlib", "seaborn")}},
        "bootstrap": {"unit": "respondent", "statistic": "mean", "method": "percentile",
                      "resamples": N_BOOT, "seed": SEED, "rng": "PCG64",
                      "confidence_level": .95, "interpretation": "educational only"},
        "quantile_interpolation": "linear", "sd_ddof": 1,
        "outlier_policy": "flag outside Q1 - 1.5*IQR and Q3 + 1.5*IQR; never remove",
        "quality_threshold": config["quality"]["max_rejection_rate"],
        "model_minimum_complete_cases": config["quality"]["minimum_complete_cases_for_model"],
        "primary_model": {"status": "not_estimated", "reason": "descriptive synthetic studio only"},
        "processing_status": "failed",
    }
    try:
        rows, quality = load_responses(input_path, config)
        report.update({**quality, "synthetic_demo": True})
        report["rejection_reasons"] = dict(Counter(item["reason"] for item in quality["rejections"]))
        if not rows:
            raise ValueError("no valid responses; quality report saved")
        clean, summary = summarize(pd.DataFrame(rows))
        clean.to_csv(output_dir / "cleaned_responses.csv", index=False, float_format="%.10g")
        summary.to_csv(output_dir / "metrics_summary.csv", index=False, float_format="%.10g", na_rep="")
        report["iqr_flag_counts"] = dict(zip(summary["metric"], summary["n_iqr_flagged"].astype(int)))
        report["processing_status"] = "complete"
        report["artifacts_sha256"] = {
            name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
            for name in ("cleaned_responses.csv", "metrics_summary.csv")}
        write_report(report_path, report)
    except (ValueError, KeyError, OSError) as error:
        report["error"] = str(error)
        write_report(report_path, report)
        raise
    print(f"{NOTICE}: valid={report['n_valid']}/{report['n_input']}; "
          f"rejected={report['n_rejected']}; quality_pass={report['quality_pass']}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--input", type=Path, default=Path("data/sample/pilot_synthetic.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)
    try:
        process(args.config, args.input, args.output_dir)
    except (ValueError, KeyError, OSError) as error:
        print(f"Processing failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
