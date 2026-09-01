import os
import threading

import numpy as np

from .audio import encode
from .ssml import strip_tags

# Piper голоса — отдельные ONNX-модели. Алиас -> имя файла ru_RU-<alias>-medium.
# Модели грузятся лениво (только при первом обращении) ради экономии памяти.


class PiperEngine:
    """Движок Piper: несколько русских голосов, быстрый CPU-синтез. SSML не поддерживает."""

    name = "piper"
    supports_random = False

    def __init__(self, models_dir: str, voices: list[str]):
        self.models_dir = models_dir
        # оставляем только те голоса, для которых реально есть файл модели
        self.speakers = [v for v in voices if os.path.isfile(self._onnx(v))]
        self._voices: dict = {}
        self._lock = threading.Lock()

    def _onnx(self, alias: str) -> str:
        return os.path.join(self.models_dir, f"ru_RU-{alias}-medium.onnx")

    def _load(self, alias: str):
        v = self._voices.get(alias)
        if v is None:
            from piper import PiperVoice

            onnx = self._onnx(alias)
            v = PiperVoice.load(onnx, config_path=onnx + ".json", use_cuda=False)
            self._voices[alias] = v
        return v

    def synthesize(self, text, speaker, sample_rate, ssml, put_accent, put_yo, fmt) -> bytes:
        if ssml:
            text = strip_tags(text)  # Piper без SSML — берём чистый текст

        alias = speaker if speaker in self.speakers else (self.speakers[0] if self.speakers else speaker)
        voice = self._load(alias)

        with self._lock:
            pcm = b"".join(voice.synthesize_stream_raw(text))

        audio = np.frombuffer(pcm, dtype=np.int16)
        rate = voice.config.sample_rate  # нативная частота голоса (обычно 22050)
        return encode(audio, rate, fmt)
