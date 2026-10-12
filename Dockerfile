FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY config.json /app/config.json
COPY src /app/src
COPY tests /app/tests
COPY data/sample /app/data/sample
RUN python -m unittest discover -s tests -v
CMD ["python", "-m", "src.benchmark", "--config", "config.json", "--input", "data/sample/pilot_synthetic.csv", "--output", "results/pilot_summary.json"]
