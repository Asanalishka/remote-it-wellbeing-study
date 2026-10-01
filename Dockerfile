FROM python:3.12.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN python -m unittest discover -s tests -v
CMD ["python", "-m", "src.benchmark", "--config", "config.json", "--input", "data/sample/pilot_synthetic.csv", "--output", "results/pilot_summary.json"]

