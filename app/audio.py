import io

import soundfile as sf


def encode(samples, rate: int, fmt: str) -> bytes:
    """Кодирует numpy-семплы (float или int16) в OGG/Vorbis или WAV/PCM16."""
    buf = io.BytesIO()
    if fmt == "wav":
        sf.write(buf, samples, rate, format="WAV", subtype="PCM_16")
    else:
        sf.write(buf, samples, rate, format="OGG", subtype="VORBIS")
    return buf.getvalue()
