import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.analyze_survey import analyze, write_labeled_rows


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


class CompletedSurveyTests(unittest.TestCase):
    def make_csv(self, path, *, eligible="Да", cbi_answer="Иногда или в некоторой степени"):
        headers = [
            "Отметка времени", "2. Работаете ли вы сейчас в IT-сфере?",
            "3. Выполняли ли вы часть работы удалённо?", "4. Должность?",
            "5. Часы?", "6. Процент удалённо?", "7. Гибкость?",
            "8. Баланс?", "9. Общение?",
            *[f"PSS-10 / {i:02d} — Вопрос" for i in range(1, 11)],
            *[f"CBI work / {i:02d} — Вопрос" for i in range(1, 8)],
            "10. Продуктивность?", "11. Возраст?", "12. Стаж?", "13. Пол?",
        ]
        values = [
            "2026/11/03", eligible, "Да", "Разработчик", "100", "70",
            "5", "4", "Несколько раз в день",
            *["Иногда"] * 10, *[cbi_answer] * 6,
            "Постоянно или в очень сильной степени", "8", "21", "6", "Мужчина",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerow(values)

    def test_scores_as_administered_and_flags_instead_of_excluding(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.csv"
            self.make_csv(path)
            report = analyze(path, CONFIG)
        self.assertEqual(report["n_valid"], 1)
        self.assertEqual(report["descriptive"]["pss_score"]["mean"], 20)
        # Six "sometimes" answers score 25 each; item 7 is reverse-coded.
        self.assertAlmostEqual(report["descriptive"]["adapted_cbi_work_score"]["mean"],
                               150 / 7, places=3)
        self.assertEqual(report["communication_frequency"], {"Несколько раз в день": 1})
        self.assertEqual(report["review_flags"], {
            "weekly_hours_ge_80_review": 1,
            "experience_exceeds_age_minus_16_review": 1,
        })
        self.assertEqual(report["rq3_model"]["status"], "not_estimated")

    def test_ineligible_and_unknown_categories_are_not_silently_recoded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.csv"
            self.make_csv(path, eligible="Нет")
            report = analyze(path, CONFIG)
            self.assertEqual(report["n_excluded_eligibility"], 1)
            self.assertEqual(report["n_valid"], 0)
            self.make_csv(path, cbi_answer="Неизвестный ответ")
            report = analyze(path, CONFIG)
            self.assertEqual(report["n_rejected"], 1)
            self.assertIn("cbi_01: unknown answer", report["rejections"][0]["reason"])

    def test_real_and_synthetic_records_share_scoring_and_keep_origin_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            real_path = Path(folder) / "real_fixture.csv"
            output = Path(folder) / "labeled.csv"
            self.make_csv(real_path)
            real_report, real_rows = analyze(real_path, CONFIG, origin="real", return_rows=True)
            synthetic_report, synthetic_rows = analyze(
                ROOT / "data/sample/completed_survey_synthetic.csv", CONFIG,
                origin="synthetic", return_rows=True)
            write_labeled_rows(output, real_rows, synthetic_rows)
            with output.open(newline="", encoding="utf-8") as handle:
                labeled = list(csv.DictReader(handle))
        self.assertEqual((real_report["n_valid"], synthetic_report["n_valid"]), (1, 8))
        self.assertEqual([row["origin"] for row in labeled], ["real"] + ["synthetic"] * 8)
        self.assertEqual(len({row["record_id"] for row in labeled}), 9)
        self.assertNotIn("Отметка времени", labeled[0])
        self.assertEqual(labeled[0]["adapted_cbi_work_score"],
                         str(real_report["descriptive"]["adapted_cbi_work_score"]["min"]))


if __name__ == "__main__":
    unittest.main()
