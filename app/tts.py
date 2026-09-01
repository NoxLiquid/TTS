import threading

import torch

from .audio import encode
from .ssml import strip_tags, wrap_speak

_VALID_RATES = (8000, 24000, 48000)


class SileroEngine:
    """Движок Silero v4_ru: 5 русских спикеров + random, поддержка SSML-prosody."""

    name = "silero"
    supports_random = True

    def __init__(self, model_path: str, default_speaker: str, torch_threads: int):
        torch.set_num_threads(max(1, torch_threads))
        self.device = torch.device("cpu")
        importer = torch.package.PackageImporter(model_path)
        self.model = importer.load_pickle("tts_models", "model")
        self.model.to(self.device)
        self.speakers = list(getattr(self.model, "speakers", []))
        self.default_speaker = (
            default_speaker if default_speaker in self.speakers
            else (self.speakers[0] if self.speakers else "random")
        )
        self._lock = threading.Lock()

    def resolve_speaker(self, speaker: str) -> str:
        if speaker and (speaker in self.speakers or speaker == "random"):
            return speaker
        return self.default_speaker

    def synthesize(self, text, speaker, sample_rate, ssml, put_accent, put_yo, fmt) -> bytes:
        spk = self.resolve_speaker(speaker)
        rate = sample_rate if sample_rate in _VALID_RATES else 24000

        with self._lock:
            audio = self._apply(text, spk, rate, ssml, put_accent, put_yo)

        return encode(audio.numpy(), rate, fmt)

    def _apply(self, text, speaker, rate, ssml, put_accent, put_yo):
        if ssml:
            try:
                return self.model.apply_tts(
                    ssml_text=wrap_speak(text),
                    speaker=speaker,
                    sample_rate=rate,
                    put_accent=put_accent,
                    put_yo=put_yo,
                )
            except Exception:
                text = strip_tags(text)
        return self.model.apply_tts(
            text=text,
            speaker=speaker,
            sample_rate=rate,
            put_accent=put_accent,
            put_yo=put_yo,
        )
