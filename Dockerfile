FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY config/requirements.txt config/requirements-dev.txt ./config/
RUN python -m pip install --upgrade pip && \
    pip install -r config/requirements.txt && \
    pip install -r config/requirements-dev.txt && \
    pip install nox

COPY . .

RUN nox -s lint tests typecheck

FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY config/requirements.txt ./config/
RUN python -m pip install --upgrade pip && \
    pip install -r config/requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
