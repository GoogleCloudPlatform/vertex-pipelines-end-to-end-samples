FROM python:3.8.13-alpine3.15

WORKDIR /root
RUN pip3 -U install poetry
COPY pyproject.toml pyproject.toml
RUN poetry install --no-dev
COPY . .
