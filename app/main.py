from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.transcriber import load_model, transcribe, transcribe_from_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(settings.whisper_model)
    yield


app = FastAPI(title="Speech-to-Text Service", lifespan=lifespan)


class TranscribeRequest(BaseModel):
    source: str
    # Override per-request; falls back to DEFAULT_SOURCE_TYPE env var when omitted
    source_type: Optional[Literal["path", "url"]] = None
    # Override language per-request; falls back to WHISPER_LANGUAGE env var when omitted
    language: Optional[str] = None


class TranscribeResponse(BaseModel):
    text: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": settings.whisper_model,
        "default_source_type": settings.default_source_type,
    }


@app.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(request: TranscribeRequest):
    source_type = request.source_type or settings.default_source_type

    language = request.language or settings.whisper_language or None

    try:
        if source_type == "url":
            text = transcribe_from_url(app.state.model, request.source, language)
        else:
            file_path = request.source
            if not file_path.startswith("/"):
                file_path = f"{settings.audio_base_path}/{file_path}"
            text = transcribe(app.state.model, file_path, language)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    return TranscribeResponse(text=text)
