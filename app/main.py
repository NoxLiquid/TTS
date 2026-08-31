import asyncio
import base64
import hashlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .cache import LruCache
from .config import settings
from .tts import SileroTTS

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger("tts")

state: dict = {}


class GenerateRequest(BaseModel):
    text: str = ""
    speaker: str = ""
    api_token: str = ""
    ssml: bool = False
    word_ts: bool = False
    put_accent: bool = True
    put_yo: bool = False
    sample_rate: int = Field(default=0)
    format: str = "ogg"


class VoiceResult(BaseModel):
    audio: str


class GenerateResponse(BaseModel):
    results: list[VoiceResult]
    original_sha1: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading Silero model from %s", settings.model_path)
    state["tts"] = SileroTTS(
        model_path=settings.model_path,
        default_speaker=settings.default_speaker,
        torch_threads=settings.torch_threads,
    )
    state["cache"] = LruCache(settings.cache_size)
    state["lock"] = asyncio.Lock()
    state["pending"] = 0
    logger.info(
        "Model ready. Speakers: %s. Default: %s",
        state["tts"].speakers,
        state["tts"].default_speaker,
    )
    yield
    state.clear()


app = FastAPI(title="Respiral TTS", version="1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    ready = "tts" in state
    return {"status": "ok" if ready else "loading", "pending": state.get("pending", 0)}


def _cache_key(req: GenerateRequest, speaker: str, rate: int) -> str:
    raw = f"{speaker}/{rate}/{req.format}/{int(req.ssml)}/{int(req.put_accent)}/{int(req.put_yo)}/{req.text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _generate(req: GenerateRequest) -> GenerateResponse:
    if settings.api_token and req.api_token != settings.api_token:
        raise HTTPException(status_code=401, detail="invalid api_token")

    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty text")
    if len(text) > settings.max_text_len:
        text = text[: settings.max_text_len]

    tts: SileroTTS = state["tts"]
    cache: LruCache = state["cache"]
    speaker = tts.resolve_speaker(req.speaker)
    rate = req.sample_rate if req.sample_rate else settings.default_sample_rate

    key = _cache_key(req, speaker, rate)
    sha1 = hashlib.sha1(text.encode("utf-8")).hexdigest()

    cached = cache.get(key)
    if cached is not None:
        return GenerateResponse(
            results=[VoiceResult(audio=base64.b64encode(cached).decode())],
            original_sha1=sha1,
        )

    if state["pending"] >= settings.max_queue:
        raise HTTPException(status_code=429, detail="overloaded")

    state["pending"] += 1
    try:
        async with state["lock"]:
            audio = await asyncio.to_thread(
                tts.synthesize,
                text,
                speaker,
                rate,
                req.ssml,
                req.put_accent,
                req.put_yo,
                req.format,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail="synthesis failed")
    finally:
        state["pending"] -= 1

    cache.put(key, audio)
    return GenerateResponse(
        results=[VoiceResult(audio=base64.b64encode(audio).decode())],
        original_sha1=sha1,
    )


@app.post("/tts", response_model=GenerateResponse)
@app.post("/", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if "tts" not in state:
        raise HTTPException(status_code=503, detail="model loading")
    return await _generate(req)
