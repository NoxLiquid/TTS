import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, "1" if default else "0") not in ("0", "false", "False", "")


class Settings:
    api_token: str = os.getenv("TTS_API_TOKEN", "")
    model_path: str = os.getenv("TTS_MODEL_PATH", "/app/models/v4_ru.pt")
    default_speaker: str = os.getenv("TTS_DEFAULT_SPEAKER", "eugene")
    # движки
    enable_silero: bool = _bool("TTS_ENABLE_SILERO", True)
    enable_piper: bool = _bool("TTS_ENABLE_PIPER", True)
    piper_dir: str = os.getenv("TTS_PIPER_DIR", "/app/models/piper")
    piper_voices: list = [
        v.strip() for v in os.getenv("TTS_PIPER_VOICES", "irina,denis,dmitri,ruslan").split(",") if v.strip()
    ]
    default_sample_rate: int = _int("TTS_SAMPLE_RATE", 24000)
    torch_threads: int = _int("TTS_TORCH_THREADS", os.cpu_count() or 2)
    max_queue: int = _int("TTS_MAX_QUEUE", 48)
    max_text_len: int = _int("TTS_MAX_TEXT_LEN", 600)
    cache_size: int = _int("TTS_CACHE_SIZE", 512)
    host: str = os.getenv("TTS_HOST", "0.0.0.0")
    port: int = _int("TTS_PORT", 5000)
    log_level: str = os.getenv("TTS_LOG_LEVEL", "info")


settings = Settings()
