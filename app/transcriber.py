import os
import tempfile
import urllib.request
import urllib.parse
from typing import Optional
import whisper

from app.config import settings

SUPPORTED_EXTENSIONS = {".mp3", ".webm", ".ogg"}


def _validate_extension(ext: str) -> None:
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )


def load_model(model_name: str) -> whisper.Whisper:
    return whisper.load_model(model_name)


def transcribe(model: whisper.Whisper, file_path: str, language: Optional[str]) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    _validate_extension(ext)

    # Prevent path traversal outside the audio base directory
    resolved = os.path.realpath(file_path)
    base = os.path.realpath(settings.audio_base_path)
    if not resolved.startswith(base + os.sep) and resolved != base:
        raise ValueError("Access denied: path is outside audio base directory")

    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    result = model.transcribe(resolved, language=language)
    return result["text"]


def transcribe_from_url(model: whisper.Whisper, url: str, language: Optional[str]) -> str:
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are supported")

    ext = os.path.splitext(parsed.path)[1].lower()
    _validate_extension(ext)

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response, open(tmp_path, "wb") as f:
            f.write(response.read())

        if os.path.getsize(tmp_path) == 0:
            raise ValueError("Downloaded file is empty — check the URL")

        result = model.transcribe(tmp_path, language=language)
        return result["text"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
