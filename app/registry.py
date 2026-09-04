import logging

logger = logging.getLogger("tts")


class EngineRegistry:
    """Маршрутизирует запрос по speaker к нужному движку. Единый интерфейс синтеза."""

    def __init__(self, engines: list, default_speaker: str):
        self.engines = [e for e in engines if getattr(e, "speakers", None)]
        if not self.engines:
            raise RuntimeError("no TTS engines loaded")

        self.by_speaker: dict = {}
        for e in self.engines:
            for s in e.speakers:
                self.by_speaker.setdefault(s, e)  # первый движок выигрывает при коллизии

        if default_speaker in self.by_speaker:
            self.default_speaker = default_speaker
        else:
            self.default_speaker = next(iter(self.by_speaker))
        self.default_engine = self.by_speaker[self.default_speaker]

    @property
    def speakers(self) -> list:
        return list(self.by_speaker.keys())

    def resolve(self, speaker: str):
        """(engine, speaker) для запрошенного голоса; неизвестный -> дефолт."""
        if speaker == "random":
            for e in self.engines:
                if getattr(e, "supports_random", False):
                    return e, "random"
        engine = self.by_speaker.get(speaker)
        if engine is not None:
            return engine, speaker
        return self.default_engine, self.default_speaker

    def synthesize(self, text, speaker, sample_rate, ssml, put_accent, put_yo, fmt) -> bytes:
        engine, spk = self.resolve(speaker)
        return engine.synthesize(text, spk, sample_rate, ssml, put_accent, put_yo, fmt)


def build_registry(settings) -> "EngineRegistry":
    from .tts import SileroEngine

    logger.info("Loading Silero model from %s", settings.model_path)
    engines = [SileroEngine(
        model_path=settings.model_path,
        default_speaker=settings.default_speaker,
        torch_threads=settings.torch_threads,
    )]

    return EngineRegistry(engines, settings.default_speaker)
