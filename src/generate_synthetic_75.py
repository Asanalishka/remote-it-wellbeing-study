"""Generate 75 fictional completed-form rows for pipeline demonstrations only."""

import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample/completed_survey_synthetic.csv"
OUTPUT = ROOT / "data/sample/completed_survey_synthetic_75.csv"
PSS = ("Никогда", "Почти никогда", "Иногда", "Часто", "Очень часто")
CBI = (
    "Никогда / очень редко или совсем незначительно",
    "Иногда или в некоторой степени",
    "Часто или в сильной степени",
    "Постоянно или в очень сильной степени",
)
COMMUNICATION = (
    "Реже", "Примерно раз в неделю", "Несколько раз в неделю",
    "Примерно раз в день", "Несколько раз в день",
)
ROLES = ("Разработчик", "Тестировщик", "DevOps или системный инженер",
         "Менеджер проекта или продукта", "Другое")
GENDERS = ("Женщина", "Мужчина", "Другое", "Предпочитаю не отвечать")


def main():
    rng = random.Random(42)
    with TEMPLATE.open(newline="", encoding="utf-8") as handle:
        headers = csv.DictReader(handle).fieldnames
    if headers is None:
        raise ValueError("Synthetic template has no headers")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for index in range(1, 76):
            age = rng.randint(21, 55)
            answers = {
                headers[0]: f"SYNTHETIC-{index:03d}",
                headers[1]: "Да",
                headers[2]: "Да",
                headers[3]: rng.choice(ROLES),
                headers[4]: str(rng.randint(25, 60)),
                headers[5]: str(rng.choice((20, 40, 60, 80, 100))),
                headers[6]: str(rng.randint(1, 5)),
                headers[7]: str(rng.randint(1, 5)),
                headers[8]: rng.choice(COMMUNICATION),
                headers[26]: str(rng.randint(0, 10)),
                headers[27]: str(age),
                headers[28]: str(rng.randint(0, age - 18)),
                headers[29]: rng.choice(GENDERS),
            }
            for header in headers[9:19]:
                answers[header] = rng.choice(PSS)
            for header in headers[19:26]:
                answers[header] = rng.choice(CBI)
            writer.writerow(answers)
    print(f"Wrote 75 fictional rows: {OUTPUT}")


if __name__ == "__main__":
    main()
