import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_tags(text: str) -> str:
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


def wrap_speak(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("<speak"):
        return stripped
    return f"<speak>{stripped}</speak>"
