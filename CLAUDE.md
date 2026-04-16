# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the service

```bash
# Local dev (auto-reload on file changes)
source .venv/bin/activate
uvicorn app.main:app --port 3004 --reload

# Docker
docker build -t stt-service .
docker run -p 3004:3004 -v /local/audio:/audio stt-service
```

**Important:** Changes to `.env` require a manual restart — uvicorn `--reload` does not watch `.env`.

## Environment variables (`.env`)

| Variable | Default | Notes |
|----------|---------|-------|
| `WHISPER_MODEL` | `base` | `base` / `small` / `medium` / `large-v3` — loaded once at startup |
| `WHISPER_LANGUAGE` | `th` | BCP-47 code. Empty string = Whisper auto-detects |
| `AUDIO_BASE_PATH` | `/audio` | Volume mount root for path-based input |
| `DEFAULT_SOURCE_TYPE` | `path` | `path` = read from volume, `url` = download from remote |

## Architecture

The service has three layers:

- **`app/config.py`** — `pydantic-settings` `BaseSettings`. All env vars land here. Every other module imports the `settings` singleton.
- **`app/transcriber.py`** — Pure functions wrapping Whisper. `load_model()` is called once at startup and stored in `app.state.model`. `transcribe()` handles volume files; `transcribe_from_url()` downloads to a temp file then transcribes, always cleaning up in `finally`.
- **`app/main.py`** — FastAPI app. The `lifespan` context manager loads the model before the server accepts requests. Two endpoints: `GET /health` and `POST /transcribe`.

## API

`POST /transcribe`
```json
{
  "source": "/audio/file.mp3",        // file path or URL
  "source_type": "path",              // optional — "path" | "url", overrides DEFAULT_SOURCE_TYPE
  "language": "th"                    // optional — overrides WHISPER_LANGUAGE; null = auto-detect
}
```

## Runtime characteristics

- Model is loaded into RAM at startup — first boot is slow (download + load). Subsequent requests only pay transcription time.
- CPU transcription is roughly 2–5× real-time for `medium`. A 57-minute file can take hours on CPU.
- Supported audio formats: `.mp3`, `.webm`, `.ogg` (requires `ffmpeg` installed).
- Python 3.9 is the runtime — use `Optional[X]` instead of `X | None` syntax.
