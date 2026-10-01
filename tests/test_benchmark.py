import json
import tempfile
import unittest
from pathlib import Path

from src.benchmark import fit_models, number, score_cbi_work, score_pss, run


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
            self.assertEqual(json.loads(output.read_text())["n_valid"], 8)

    def test_model_recovers_known_negative_association(self):
        rows = []
        for i in range(120):
            burnout = (i * 7) % 85
            stress = (i * 3) % 37
            age = 22 + i % 25
            experience = 1 + i % 10
            hours = 32 + i % 17
            rows.append({"age": age, "years_experience": experience,
                         "weekly_hours": hours, "gender": "woman", "job_role": "developer",
                         "pss_score": stress, "cbi_work_score": burnout,
                         "productivity_0_10": 8 - 0.35 * (burnout / 10) - 0.02 * stress
                         + 0.002 * age + 0.001 * hours})
        result = fit_models(rows, CONFIG)
        self.assertAlmostEqual(result["burnout_beta_per_10_points"], -0.35, places=3)


if __name__ == "__main__":
    unittest.main()

