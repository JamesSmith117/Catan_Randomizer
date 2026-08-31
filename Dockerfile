# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="bettercatan" \
      org.opencontainers.image.description="Catan board randomizer" \
      org.opencontainers.image.source="https://github.com/example/bettercatan"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY catan/ ./catan/

RUN chown -R app:app /app

USER app

ENTRYPOINT ["python", "catan/catan_randomizer.py"]
CMD ["--mode", "34", "--no-open"]
