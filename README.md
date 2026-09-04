# Respiral TTS

Лёгкий CPU-TTS сервис для SS14 (Respiral). Синтез русской речи на модели
[Silero](https://github.com/snakers4/silero-models) `v5_cis_base_nostress`, совместим с
Corvax TTS API, который уже используется в игровом коде SS14.

## Почему так

- **Silero v5 (`v5_cis_base_nostress`)** — быстрый CPU-синтез без GPU, лицензия **MIT**,
  60 спикеров, из них **29 русских** (`ru_*`). Модель `_nostress` не требует ручной
  простановки ударений. Параметры игрового клиента (`put_accent`, `put_yo`, `speaker`,
  SSML `<prosody>`) — это ровно интерфейс Silero.
- **HTTP + JSON** — тот же протокол, что ждёт `Content.Server/_Corvax/TTS/TTSManager.cs`.
  Сервис — drop-in бэкенд: в игре достаточно указать `tts.api_url` и `tts.api_token`.

## Движок (Silero v5)

Один движок Silero (`app/registry.py`; каркас реестра оставлен под возможные будущие
движки), маршрутизация по полю `speaker`:

- **29 русских спикеров** `ru_*` (см. `Resources/Prototypes/_Corvax/TTS/voices.yml` в игре).
- Разнообразие расширяется через SSML `<prosody>` (pitch `low/high`, rate) — в игре на каждый
  голос заведены базовый + `low` + `high` варианты.
- Псевдо-спикера `random` в v5 **нет** (движок его не предлагает, если модель не содержит).

Неизвестный `speaker` → дефолт (`TTS_DEFAULT_SPEAKER`, по умолчанию `ru_eduard`).
Модель скачивается в образ при сборке (`v5_cis_base_nostress.pt`, ~90 МБ).

## API

`POST /tts` (а также `POST /`)

Запрос:

```json
{
  "api_token": "secret",
  "text": "<speak><prosody rate=\"fast\">Привет</prosody></speak>",
  "speaker": "ru_eduard",
  "ssml": true,
  "put_accent": true,
  "put_yo": false,
  "sample_rate": 24000,
  "format": "ogg"
}
```

Ответ:

```json
{ "results": [ { "audio": "<base64 ogg>" } ], "original_sha1": "..." }
```

- `401` — неверный `api_token` (если `TTS_API_TOKEN` задан).
- `429` — очередь синтеза переполнена (игровой клиент трактует это как rate-limit).
- `GET /health` — статус и число задач в обработке.

Спикеры — 29 русских голосов `ru_*` модели `v5_cis_base_nostress`
(`ru_eduard`, `ru_igor`, `ru_oksana`, `ru_zara`, …; полный список — в игровом `voices.yml`).

## Запуск

```bash
cp .env.example .env      # задать TTS_API_TOKEN
docker compose up -d --build
curl -s http://127.0.0.1:5000/health
```

Первая сборка скачивает модель `v5_cis_base_nostress.pt` в образ (работает офлайн после сборки).

## Настройка производительности

Синтез — CPU-bound; масштабируется процессами (`--workers`), не потоками.
Ориентир: `TTS_WORKERS * TTS_TORCH_THREADS ≈ выделенные под TTS ядра`.

| Переменная | По умолчанию | Смысл |
|---|---|---|
| `TTS_WORKERS` | 3 | процессов uvicorn (каждый держит свою копию модели, ~300–500 МБ RAM) |
| `TTS_TORCH_THREADS` | 2 | потоков torch на процесс |
| `TTS_MAX_QUEUE` | 48 | порог, после которого отдаём `429` |
| `TTS_CACHE_SIZE` | 512 | размер LRU-кэша аудио на процесс |
| `TTS_DEFAULT_SPEAKER` | ru_eduard | голос по умолчанию / для неизвестного спикера |
| `TTS_API_TOKEN` | — | общий секрет с игрой |

## Интеграция с игрой

В `server_config.toml` (или через CVar):

```toml
[tts]
enabled = true
api_url = "http://127.0.0.1:5000/tts"
api_token = "тот же секрет, что TTS_API_TOKEN"
```

Серверная часть TTS уже есть в `ss14-respiral` (`Content.Server/_Corvax/TTS`,
`Content.Shared/_Corvax/TTS`). Голоса заданы в `Resources/Prototypes/_Corvax/TTS/voices.yml`,
пол/имена — в `Resources/Locale/{ru-RU,en-US}/_corvax/tts.ftl`. При смене набора спикеров
модели правь оба репозитория согласованно (имена `speaker` в `voices.yml` = спикеры модели).
