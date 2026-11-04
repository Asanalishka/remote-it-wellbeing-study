"""Export publication-style figures for the synthetic survey pipeline check."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# A project-local writable cache also works on headless CI workers.
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parents[1] / ".cache"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
import seaborn as sns

from src.process_data import METRICS, NOTICE


LABELS = ("PSS-10 stress", "Work-related CBI", "Self-reported\nproductivity")
LIMITS = (40, 100, 10)
MARKERS = ("o", "s", "^")
FIGURE_NAMES = ("means_ci", "distributions", "burnout_productivity")


def set_theme():
    sns.set_theme(context="paper", style="whitegrid", palette="colorblind", font_scale=1.2,
                  rc={"pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False,
                      "axes.spines.right": False, "grid.alpha": .25,
                      "savefig.dpi": 300, "font.family": "DejaVu Sans"})


def panel_axes(title):
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 4.2))
    fig.subplots_adjust(left=.08, right=.98, bottom=.25, top=.76, wspace=.55)
    fig.suptitle(title, y=.97, fontsize=13)
    for ax, label, upper in zip(axes, LABELS, LIMITS):
        ax.set_title(label, fontsize=11, pad=12)
        ax.set_ylabel("Score (points)")
        ax.set_ylim(0, upper)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        ax.set_xticks([])
        ax.set_xlim(-.55, .55)
        ax.grid(axis="x", visible=False)
    return fig, axes


def annotate(fig, n, detail, quality_pass):
    quality = "" if quality_pass else " | QUALITY GUARDRAIL FAILED"
    fig.text(.5, .105, detail, ha="center", va="center", fontsize=9)
    fig.text(.5, .045, f"{NOTICE}\nSynthetic n = {n}{quality}",
             ha="center", va="center", fontsize=9, fontweight="medium")


def build_figures(clean, summary, report):
    set_theme()
    palette = sns.color_palette("colorblind", 3)
    n = len(clean)
    good = report["quality_pass"]
    figures = {}
    fig, axes = panel_axes("Means and educational 95% bootstrap intervals")
    for ax, metric, color, marker in zip(axes, METRICS, palette, MARKERS):
        row = summary.loc[metric]
        low, high = row["mean_ci95_low"], row["mean_ci95_high"]
        if pd.notna(low) and pd.notna(high):
            # Draw bounds directly: percentile CIs need not enclose the estimate.
            ax.vlines(0, low, high, color=color, linewidth=2, alpha=.7, zorder=2)
            ax.hlines([low, high], -.06, .06, color=color, linewidth=2, alpha=.7, zorder=2)
        else:
            ax.text(.5, .9, "CI unavailable", transform=ax.transAxes, ha="center", fontsize=9)
        ax.plot(0, row["mean"], marker=marker, color=color, markeredgecolor="black",
                markersize=7, linestyle="none", zorder=3)
    annotate(fig, n, "Points: means; capped intervals: bootstrap uncertainty, not individual spread.", good)
    figures["means_ci"] = fig

    fig, axes = panel_axes("Outcome distributions and all synthetic responses")
    for ax, metric, color, marker in zip(axes, METRICS, palette, MARKERS):
        ax.boxplot(clean[metric], positions=[0], widths=.42, orientation="vertical",
                   whis=1.5, showfliers=False, patch_artist=True, manage_ticks=False,
                   boxprops={"facecolor": color, "alpha": .35, "linewidth": 1.2},
                   medianprops={"color": "black"})
        # Deterministic horizontal offsets reveal coincident observations.
        offsets = np.linspace(-.12, .12, n)
        ax.scatter(offsets, clean[metric], marker=marker, s=28, facecolor=color,
                   edgecolor="black", linewidth=.6, zorder=3)
        flagged = clean[f"{metric}_iqr_flag"].to_numpy(dtype=bool)
        if flagged.any():
            ax.scatter(offsets[flagged], clean.loc[flagged, metric], marker="D", s=80,
                       facecolors="none", edgecolors="black", linewidth=1.2, zorder=4)
        ax.set_ylabel("Score (points)")
        ax.set_xticks([])
        ax.set_xlim(-.55, .55)
    annotate(fig, n, "Boxes: p25–p75; line: median; whiskers: 1.5×IQR rule. Diamonds: IQR flags.", good)
    figures["distributions"] = fig

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    fig.subplots_adjust(left=.12, right=.96, bottom=.29, top=.87)
    ax.scatter(clean["cbi_work_score"], clean["productivity_0_10"],
               color=palette[0], marker="o", s=48, edgecolor="black", linewidth=.6)
    ax.set(xlabel="Work-related CBI burnout (points)",
           ylabel="Self-reported productivity (points)", xlim=(0, 100), ylim=(0, 10),
           title="Burnout and self-reported productivity")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    annotate(fig, n, "Each point: one synthetic response. No model or association inference.", good)
    figures["burnout_productivity"] = fig
    return figures


def visualize(input_dir, output_dir):
    report = json.loads((input_dir / "quality_report.json").read_text(encoding="utf-8"))
    if report.get("processing_status") != "complete" or report.get("synthetic_demo") is not True:
        raise ValueError("requires a completed synthetic processing report")
    for name in ("cleaned_responses.csv", "metrics_summary.csv"):
        expected = report.get("artifacts_sha256", {}).get(name)
        actual = hashlib.sha256((input_dir / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"{name}: hash mismatch; rerun processing before plotting")
    clean = pd.read_csv(input_dir / "cleaned_responses.csv")
    summary = pd.read_csv(input_dir / "metrics_summary.csv").set_index("metric")
    if not len(clean) or len(clean) != report["n_valid"]:
        raise ValueError("cleaned row count does not match the quality report")
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = build_figures(clean, summary, report)
    try:
        for name, fig in figures.items():
            fig.savefig(output_dir / f"{name}.pdf",
                        metadata={"Title": name, "Subject": NOTICE,
                                  "CreationDate": None, "ModDate": None})
            fig.savefig(output_dir / f"{name}.png", dpi=300, metadata={"Description": NOTICE})
    finally:
        for fig in figures.values():
            plt.close(fig)
    print(f"{NOTICE}: wrote {len(figures)} PDF and {len(figures)} PNG figures to {output_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/figures"))
    args = parser.parse_args(argv)
    try:
        visualize(args.input_dir, args.output_dir)
    except (ValueError, KeyError, OSError) as error:
        print(f"Visualization failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
