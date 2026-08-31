# Respiral TTS

Лёгкий CPU-TTS сервис для SS14 (Respiral). Синтез русской речи на моделях
[Silero](https://github.com/snakers4/silero-models) (`v4_ru`), совместим с
Corvax TTS API, который уже используется в игровом коде SS14.

## Почему так

- **Silero v4** — быстрый CPU-синтез без GPU, хорошее качество русского языка,
  маленькая модель (~60 МБ). Параметры игрового клиента (`put_accent`, `put_yo`,
  `speaker`, SSML `<prosody>`) — это ровно интерфейс Silero.
- **HTTP + JSON** — тот же протокол, что ждёт `Content.Server/Corvax/TTS/TTSManager.cs`.
  Сервис — drop-in бэкенд: в игре достаточно указать `tts.api_url` и `tts.api_token`.

## API

`POST /tts` (а также `POST /`)

Запрос:

```json
{
  "api_token": "secret",
  "text": "<speak><prosody rate=\"fast\">Привет</prosody></speak>",
  "speaker": "eugene",
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

Спикеры Silero `v4_ru`: `aidar`, `baya`, `kseniya`, `xenia`, `eugene`, `random`.

## Запуск

```bash
cp .env.example .env      # задать TTS_API_TOKEN
docker compose up -d --build
curl -s http://127.0.0.1:5000/health
```

Первая сборка скачивает модель `v4_ru.pt` в образ (работает офлайн после сборки).

## Настройка производительности

Синтез — CPU-bound; масштабируется процессами (`--workers`), не потоками.
Ориентир: `TTS_WORKERS * TTS_TORCH_THREADS ≈ выделенные под TTS ядра`.

| Переменная | По умолчанию | Смысл |
|---|---|---|
| `TTS_WORKERS` | 3 | процессов uvicorn (каждый держит свою копию модели, ~300–500 МБ RAM) |
| `TTS_TORCH_THREADS` | 2 | потоков torch на процесс |
| `TTS_MAX_QUEUE` | 48 | порог, после которого отдаём `429` |
| `TTS_CACHE_SIZE` | 512 | размер LRU-кэша аудио на процесс |
| `TTS_DEFAULT_SPEAKER` | eugene | голос по умолчанию / для неизвестного спикера |
| `TTS_API_TOKEN` | — | общий секрет с игрой |

## Интеграция с игрой

В `server_config.toml` (или через CVar):

```toml
[tts]
enabled = true
api_url = "http://127.0.0.1:5000/tts"
api_token = "тот же секрет, что TTS_API_TOKEN"
```

Внимание: репозиторий `ss14-respiral` пока **не содержит** серверной части TTS —
её нужно портировать из сборки `space-station-14` (`Content.Server/Corvax/TTS`,
`Content.Shared/Corvax/TTS`, `Content.Client/.../TTS`, `CCCVars`).
