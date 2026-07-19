FROM python:3.12-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt gunicorn

COPY --chown=appuser:appuser . .

RUN mkdir -p /data && chown appuser:appuser /data

USER appuser

ENV SEEDBANK_HOST=0.0.0.0 \
    SEEDBANK_PORT=5050 \
    SEEDBANK_DATA=/data \
    SEEDBANK_SSH=0 \
    SEEDBANK_DEBUG=0 \
    PYTHONUNBUFFERED=1

EXPOSE 5050

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
