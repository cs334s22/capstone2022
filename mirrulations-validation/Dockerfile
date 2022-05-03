FROM python:3.8-slim-buster

WORKDIR /app

RUN python3 -m venv .venv

COPY mirrulations-validation .
COPY mirrulations-work-generator /mirrulations-work-generator
COPY mirrulations-core /mirrulations-core

RUN .venv/bin/pip install -e .
RUN .venv/bin/pip install -e /mirrulations-core/
RUN .venv/bin/pip install -e /mirrulations-work-generator/

CMD [".venv/bin/python", "src/mirrval/job_validator.py"]
