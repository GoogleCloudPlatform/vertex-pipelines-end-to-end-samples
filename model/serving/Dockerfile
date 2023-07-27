FROM python:3.9.16-slim
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY main.py main.py

CMD exec uvicorn main:app --host "0.0.0.0" --port "$AIP_HTTP_PORT"
