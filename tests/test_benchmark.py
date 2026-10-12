import contextlib
import csv
import io
import json
import math
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from src.benchmark import fit_models, main, number, score_cbi_work, score_pss, run


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text())


class ScoringTests(unittest.TestCase):
    def test_reverse_scoring_changes_positive_items(self):
        row = {f"pss_{i:02d}": "0" for i in range(1, 11)}
        self.assertEqual(score_pss(row, CONFIG), 16)
        cbi = {f"cbi_{i:02d}": "4" for i in range(1, 8)}
        self.assertAlmostEqual(score_cbi_work(cbi, CONFIG), 600 / 7)

    def test_out_of_range_and_nan_are_rejected(self):
        for value in ("5", "nan", "", "2.5"):
            with self.assertRaises(ValueError, msg=value):
                number(value, "item", 0, 4, integer=True)

    def test_pilot_produces_output_without_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "summary.json"
            result = run(ROOT / "config.json", ROOT / "data/sample/pilot_synthetic.csv", output)
            self.assertEqual(result["n_valid"], 8)
            self.assertTrue(result["quality_pass"])
            self.assertEqual(result["primary_model"]["status"], "not_estimated")
            self.assertEqual(result["descriptive"]["remote_work_percent"], 78.438)
            self.assertEqual(json.loads(output.read_text())["n_valid"], 8)

    def test_model_recovers_known_negative_association(self):
        rows = []
        for i in range(120):
            burnout = (i * 7) % 85
            # Correlation exposes the omitted-burnout bias in the baseline slope.
            stress = 0.3 * burnout + ((i * 3) % 37) / 4
            age = 22 + i % 25
            experience = 1 + i % 10
            hours = 32 + i % 17
            rows.append({"age": age, "years_experience": experience,
                         "weekly_hours": hours, "gender": "woman", "job_role": "developer",
                         "pss_score": stress, "cbi_work_score": burnout,
                         "productivity_0_10": 8 - 0.35 * (burnout / 10) - 0.02 * stress
                         + 0.002 * age + 0.001 * hours})
        # Paired residuals retain the exact slopes with nonzero uncertainty.
        rows = [{**row, "productivity_0_10": row["productivity_0_10"] + noise}
                for row in rows for noise in (-0.1, 0.1)]
        result = fit_models(rows, CONFIG)
        self.assertAlmostEqual(result["burnout_beta_per_10_points"], -0.35, places=3)
        self.assertAlmostEqual(result["full_stress_beta_per_point"], -0.02, places=3)
        self.assertGreater(abs(result["baseline_stress_beta_per_point"]
                               - result["full_stress_beta_per_point"]), 0.01)
        for prefix, beta_key in (("full_stress", "full_stress_beta_per_point"),
                                 ("burnout", "burnout_beta_per_10_points")):
            se = result[f"{prefix}_beta_standard_error"]
            low, high = result[f"{prefix}_beta_approx_95pct_ci"]
            self.assertTrue(all(math.isfinite(v) for v in (se, low, high)))
            self.assertGreater(se, 0)
            self.assertLess(low, result[beta_key])
            self.assertGreater(high, result[beta_key])
            self.assertAlmostEqual(high - low, 2 * 1.96 * se, delta=0.00003)
        existing_fields = {"status", "n", "baseline_r_squared", "full_r_squared",
                           "delta_r_squared", "baseline_stress_beta_per_point",
                           "burnout_beta_per_10_points", "burnout_beta_standard_error",
                           "burnout_beta_approx_95pct_ci", "uncertainty_note"}
        self.assertTrue(existing_fields <= result.keys())
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        # Remote intensity describes the sample and must not change either model.
        with_intensity = [{**row, "remote_work_percent": 25 + i % 76}
                          for i, row in enumerate(rows)]
        self.assertEqual(fit_models(with_intensity, CONFIG), result)

        # With no burnout contribution, the baseline must recover the stress slope.
        for row in rows:
            row["productivity_0_10"] = (8 - 0.02 * row["pss_score"]
                                      + 0.002 * row["age"] + 0.001 * row["weekly_hours"])
        result = fit_models(rows, CONFIG)
        self.assertAlmostEqual(result["baseline_stress_beta_per_point"], -0.02, places=3)


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.input = Path(folder.name) / "responses.csv"
        self.output = Path(folder.name) / "summary.json"
        with (ROOT / "data/sample/pilot_synthetic.csv").open(newline="") as fh:
            reader = csv.DictReader(fh)
            self.fields = reader.fieldnames
            self.rows = list(reader)

    def write_rows(self, rows, fields=None):
        with self.input.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields or self.fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def run_input(self):
        return run(ROOT / "config.json", self.input, self.output)

    def test_missing_header_column_fails(self):
        self.write_rows(self.rows, [f for f in self.fields if f != "age"])
        with self.assertRaisesRegex(ValueError, "missing columns: age"):
            self.run_input()

    def test_missing_remote_work_percent_fails_without_days_fallback(self):
        fields = [f for f in self.fields if f != "remote_work_percent"]
        self.write_rows([{**row, "remote_days_per_week": "4"} for row in self.rows],
                        fields + ["remote_days_per_week"])
        with self.assertRaisesRegex(ValueError, "missing columns: remote_work_percent"):
            self.run_input()

    def test_remote_work_percent_accepts_positive_fractions_and_upper_bound(self):
        for value in ("0.1", "62.5", "100"):
            with self.subTest(value=value):
                self.write_rows([{**self.rows[0], "remote_work_percent": value}])
                result = self.run_input()
                self.assertEqual(result["n_valid"], 1)
                self.assertEqual(result["descriptive"]["remote_work_percent"], float(value))

    def test_remote_work_percent_rejects_invalid_values(self):
        for value in ("0", "-1", "100.1", "", "nan", "inf", "unknown"):
            with self.subTest(value=value):
                self.write_rows([{**self.rows[0], "remote_work_percent": value}])
                result = self.run_input()
                self.assertEqual(result["n_valid"], 0)
                self.assertEqual(result["n_rejected"], 1)
                self.assertIn("remote_work_percent", result["rejections"][0]["reason"])

    def test_duplicate_header_column_fails(self):
        self.write_rows(self.rows, self.fields + ["age"])
        with self.assertRaisesRegex(ValueError, "duplicate CSV column"):
            self.run_input()

    def test_empty_file_cli_fails_clearly(self):
        self.input.touch()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            status = main(["--config", str(ROOT / "config.json"),
                           "--input", str(self.input), "--output", str(self.output)])
        self.assertEqual(status, 1)
        self.assertIn("Benchmark failed: missing columns", stderr.getvalue())
        self.assertFalse(self.output.exists())

    def test_header_without_responses_fails(self):
        self.write_rows([])
        with self.assertRaisesRegex(ValueError, "CSV has no responses"):
            self.run_input()

    def test_short_row_is_rejected_with_line_number(self):
        # Put the ID last to exercise a missing ID (None from DictReader).
        fields = [f for f in self.fields if f != "respondent_id"] + ["respondent_id"]
        self.write_rows(self.rows, fields)
        with self.input.open("a", newline="") as fh:
            csv.writer(fh).writerow([self.rows[0][f] for f in fields[:-1]])
        result = self.run_input()
        self.assertEqual(result["n_valid"], 8)
        self.assertEqual(result["n_rejected"], 1)
        self.assertEqual(result["rejections"][0]["csv_line"], 10)
        self.assertIn("incomplete row", result["rejections"][0]["reason"])

    def test_blank_fields_are_rejected(self):
        for field in ("respondent_id", "gender", "age", "cbi_07"):
            with self.subTest(field=field):
                self.write_rows([{**self.rows[0], field: ""}])
                result = self.run_input()
                self.assertEqual(result["n_valid"], 0)
                self.assertIn(field, result["rejections"][0]["reason"])

    def test_extra_columns_are_rejected(self):
        self.write_rows(self.rows)
        with self.input.open("a", newline="") as fh:
            csv.writer(fh).writerow([self.rows[0][f] for f in self.fields] + ["extra"])
        result = self.run_input()
        self.assertEqual(result["n_rejected"], 1)
        self.assertEqual(result["rejections"][0]["reason"], "unexpected extra columns")

    def test_ids_are_trimmed_before_duplicate_detection(self):
        rows = [{**self.rows[0], "respondent_id": " S001 "}, self.rows[0]]
        self.write_rows(rows)
        result = self.run_input()
        self.assertEqual(result["n_valid"], 1)
        self.assertEqual(result["rejections"][0]["reason"], "duplicate respondent_id")

    def test_quality_gate_blocks_model_even_with_80_valid_rows(self):
        rows = [{**self.rows[i % 8], "respondent_id": f"T{i}"} for i in range(80)]
        rows += [{**self.rows[0], "respondent_id": f"bad{i}", "age": ""} for i in range(10)]
        self.write_rows(rows)
        with patch("src.benchmark.fit_models") as fit:
            result = self.run_input()
            fit.assert_not_called()
        self.assertEqual(result["n_valid"], 80)
        self.assertFalse(result["quality_pass"])
        self.assertEqual(result["primary_model"]["status"], "not_estimated")

    def test_exactly_ten_percent_rejected_passes_quality_gate(self):
        rows = [{**self.rows[i % 8], "respondent_id": f"T{i}"} for i in range(9)]
        self.write_rows(rows + [{**self.rows[0], "age": ""}])
        result = self.run_input()
        self.assertEqual(result["rejection_rate"], 0.1)
        self.assertTrue(result["quality_pass"])


if __name__ == "__main__":
    unittest.main()
