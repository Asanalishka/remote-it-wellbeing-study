"""Optional studio suite: run with -s tests/studio after installing dependencies."""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from src.benchmark import load_responses, run
from src.process_data import METRICS, NOTICE, process, summarize
from src.visualize import FIGURE_NAMES, build_figures, visualize
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.json"
SAMPLE = ROOT / "data/sample/pilot_synthetic.csv"
CONFIG = json.loads(CONFIG_PATH.read_text())


class StudioTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.output = self.folder / "processed"
        self.addCleanup(plt.close, "all")
        with SAMPLE.open(newline="") as fh:
            reader = csv.DictReader(fh)
            self.fields = reader.fieldnames
            self.rows = list(reader)

    def write_rows(self, rows, fields=None):
        path = self.folder / "synthetic.csv"
        with path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields or self.fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return path

    def process(self, source=SAMPLE):
        with contextlib.redirect_stdout(io.StringIO()):
            return process(CONFIG_PATH, source, self.output)

    def test_sample_scoring_and_legacy_result_agree(self):
        report = self.process()
        clean = pd.read_csv(self.output / "cleaned_responses.csv")
        summary = pd.read_csv(self.output / "metrics_summary.csv").set_index("metric")
        expected, _ = load_responses(SAMPLE, CONFIG)
        with contextlib.redirect_stdout(io.StringIO()):
            legacy = run(CONFIG_PATH, SAMPLE, self.folder / "legacy.json")
        self.assertEqual((report["n_input"], report["n_valid"], report["n_rejected"]), (8, 8, 0))
        self.assertTrue(report["quality_pass"])
        self.assertEqual(legacy["primary_model"]["status"], "not_estimated")
        for metric in METRICS:
            np.testing.assert_allclose(clean[metric], [r[metric] for r in expected])
            self.assertAlmostEqual(summary.loc[metric, "mean"], legacy["descriptive"][metric], places=3)
        self.assertTrue(clean["synthetic_demo"].all())
        self.assertTrue((summary["notice"] == NOTICE).all())

    def test_known_statistics_and_flagged_value_retained(self):
        values = [0, 1, 1, 1, 2, 2, 2, 10]
        clean, summary = summarize(pd.DataFrame({m: values for m in METRICS}))
        row = summary.iloc[0]
        self.assertEqual(len(clean), 8)
        self.assertEqual(row["mean"], 2.375)
        self.assertAlmostEqual(row["sd"], (69.875 / 7) ** .5)
        self.assertEqual((row["p25"], row["p50"], row["p75"]), (1, 1.5, 2))
        self.assertAlmostEqual(row["p95"], 7.2)
        self.assertAlmostEqual(row["p99"], 9.44)
        self.assertEqual(row["n_iqr_flagged"], 1)
        self.assertTrue(clean.iloc[-1]["pss_score_iqr_flag"])
        self.assertEqual(clean.iloc[-1]["pss_score"], 10)

    def test_bootstrap_matches_independent_reference_and_repeats(self):
        frame = pd.DataFrame({m: [0., 1., 2.] for m in METRICS})
        _, summary = summarize(frame)
        # A separate direct implementation of the specified respondent bootstrap.
        rng = np.random.Generator(np.random.PCG64(42))
        draws = rng.integers(0, 3, size=(10_000, 3))
        means = np.array([0., 1., 2.])[draws].mean(axis=1)
        expected = np.quantile(means, [.025, .975], method="linear")
        np.testing.assert_allclose(summary[["mean_ci95_low", "mean_ci95_high"]],
                                   np.tile(expected, (3, 1)))
        self.process()
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.process()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_singleton_and_constant_outcomes(self):
        _, single = summarize(pd.DataFrame({m: [2.] for m in METRICS}))
        self.assertTrue(single[["sd", "mean_ci95_low", "mean_ci95_high"]].isna().all().all())
        self.assertTrue((single["ci_status"] == "unavailable_n_lt_2").all())
        clean, constant = summarize(pd.DataFrame({m: [2.] * 8 for m in METRICS}))
        self.assertTrue((constant[["mean_ci95_low", "mean_ci95_high"]] == 2).all().all())
        self.assertFalse(clean.filter(like="_iqr_flag").any().any())

    def test_rejection_denominator_duplicates_and_incomplete_rows(self):
        source = self.write_rows(self.rows + [
            {**self.rows[0], "respondent_id": " S001 "},
            {**self.rows[1], "respondent_id": "bad", "pss_01": ""},
        ])
        report = self.process(source)
        self.assertEqual((report["n_input"], report["n_valid"], report["n_rejected"]), (10, 8, 2))
        self.assertEqual(report["rejection_rate"], .2)
        self.assertFalse(report["quality_pass"])
        self.assertEqual(report["rejections"][0]["csv_line"], 10)
        self.assertEqual(report["rejections"][0]["reason"], "duplicate respondent_id")

    def test_failed_processing_report_blocks_stale_figures(self):
        self.process()
        bad = self.write_rows([{**self.rows[0], "age": "nan"}])
        with self.assertRaisesRegex(ValueError, "no valid responses"):
            self.process(bad)
        report = json.loads((self.output / "quality_report.json").read_text())
        self.assertEqual(report["processing_status"], "failed")
        self.assertEqual(report["n_valid"], 0)
        with self.assertRaisesRegex(ValueError, "completed synthetic"):
            visualize(self.output, self.folder / "figures")

    def test_schema_error_saves_failed_report(self):
        bad = self.write_rows(self.rows, [f for f in self.fields if f != "age"])
        with self.assertRaisesRegex(ValueError, "missing columns: age"):
            self.process(bad)
        report = json.loads((self.output / "quality_report.json").read_text())
        self.assertEqual(report["processing_status"], "failed")
        self.assertIn("missing columns: age", report["error"])

    def test_stale_or_modified_summary_is_rejected(self):
        self.process()
        with (self.output / "metrics_summary.csv").open("a") as fh:
            fh.write("\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            visualize(self.output, self.folder / "figures")

    def test_figures_show_bounds_units_notices_and_all_points(self):
        report = self.process()
        clean = pd.read_csv(self.output / "cleaned_responses.csv")
        summary = pd.read_csv(self.output / "metrics_summary.csv").set_index("metric")
        figures = build_figures(clean, summary, report)
        for fig in figures.values():
            self.assertTrue(any(NOTICE in t.get_text() for t in fig.texts))
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            # Captions and axis labels must be fully contained in the exported page.
            for text in [*fig.texts, *[a for ax in fig.axes for a in
                                      (ax.xaxis.label, ax.yaxis.label, ax.title)]]:
                bounds = text.get_window_extent(renderer)
                self.assertGreaterEqual(bounds.x0, -1)
                self.assertGreaterEqual(bounds.y0, -1)
                self.assertLessEqual(bounds.x1, fig.bbox.width + 1)
                self.assertLessEqual(bounds.y1, fig.bbox.height + 1)
        for ax, metric, upper in zip(figures["means_ci"].axes, METRICS, (40, 100, 10)):
            self.assertEqual(ax.get_ylim(), (0, upper))
            self.assertIn("points", ax.get_ylabel())
            segment = ax.collections[0].get_segments()[0]
            np.testing.assert_allclose(segment[:, 1], summary.loc[metric, ["mean_ci95_low", "mean_ci95_high"]].to_numpy(dtype=float))
        for ax in figures["distributions"].axes:
            self.assertEqual(len(ax.collections[0].get_offsets()), 8)
        self.assertEqual(len(figures["burnout_productivity"].axes[0].collections[0].get_offsets()), 8)

    def test_export_pdf_and_300_dpi_png(self):
        self.process()
        output = self.folder / "figures"
        with contextlib.redirect_stdout(io.StringIO()):
            visualize(self.output, output)
        for name in FIGURE_NAMES:
            self.assertTrue((output / f"{name}.pdf").read_bytes().startswith(b"%PDF-"))
            with Image.open(output / f"{name}.png") as image:
                self.assertAlmostEqual(image.info["dpi"][0], 300, places=1)
                self.assertEqual(image.info["Description"], NOTICE)
                self.assertGreaterEqual(image.width, 2000)


if __name__ == "__main__":
    unittest.main()
