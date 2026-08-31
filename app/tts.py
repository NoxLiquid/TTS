import io
import threading

import soundfile as sf
import torch

from .ssml import strip_tags, wrap_speak

_VALID_RATES = (8000, 24000, 48000)


class SileroTTS:
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

    def synthesize(
        self,
        text: str,
        speaker: str,
        sample_rate: int,
        ssml: bool,
        put_accent: bool,
        put_yo: bool,
        fmt: str,
    ) -> bytes:
        spk = self.resolve_speaker(speaker)
        rate = sample_rate if sample_rate in _VALID_RATES else 24000

        with self._lock:
            audio = self._apply(text, spk, rate, ssml, put_accent, put_yo)

        return self._encode(audio.numpy(), rate, fmt)

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

    @staticmethod
    def _encode(wav, rate: int, fmt: str) -> bytes:
        buf = io.BytesIO()
        if fmt == "wav":
            sf.write(buf, wav, rate, format="WAV", subtype="PCM_16")
        else:
            sf.write(buf, wav, rate, format="OGG", subtype="VORBIS")
        return buf.getvalue()
