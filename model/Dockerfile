# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
FROM python:3.12.8-slim AS builder

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_CREATE=false

ARG POETRY_VERSION=2.1.3
RUN pip install poetry==${POETRY_VERSION}

# Build context is the repo root so both model/ and config/ are available.
# WORKDIR /model ensures the ../config path dependency resolves to /config.
WORKDIR /model
COPY model/pyproject.toml model/poetry.lock ./
COPY config /config

FROM builder AS training

RUN poetry install --no-cache --no-interaction --without prediction --no-root
COPY model/training training

CMD python -m training

FROM builder AS prediction

RUN poetry install --no-cache --no-interaction --with prediction --no-root
COPY model/prediction prediction

CMD exec uvicorn prediction.main:app --host "0.0.0.0" --port "$AIP_HTTP_PORT"
