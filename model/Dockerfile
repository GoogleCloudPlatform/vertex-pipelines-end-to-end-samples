FROM python:3.9.16-slim AS builder

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

ARG POETRY_VERSION=1.5.1

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN pip install poetry==${POETRY_VERSION}
RUN poetry config virtualenvs.create false && poetry install

FROM builder AS training

COPY training/train.py training/train.py

FROM builder AS serving

RUN poetry install --with serving
COPY serving/main.py serving/main.py

CMD exec uvicorn serving.main:app --host "0.0.0.0" --port "$AIP_HTTP_PORT"
