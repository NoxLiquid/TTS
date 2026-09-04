FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    OMP_NUM_THREADS=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Silero v5_cis_base_nostress (MIT): 60 спикеров, из них 29 русских (ru_*), авто-ударения не требуются.
RUN mkdir -p /app/models \
    && curl -fsSL https://models.silero.ai/models/tts/ru/v5_cis_base_nostress.pt -o /app/models/v5_cis_base_nostress.pt

COPY app ./app

EXPOSE 5000

ENV TTS_MODEL_PATH=/app/models/v5_cis_base_nostress.pt \
    TTS_HOST=0.0.0.0 \
    TTS_PORT=5000 \
    TTS_WORKERS=1

CMD ["sh", "-c", "uvicorn app.main:app --host ${TTS_HOST} --port ${TTS_PORT} --workers ${TTS_WORKERS}"]
