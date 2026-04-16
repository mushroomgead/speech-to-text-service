# Speech-to-Text Service

Transcribes audio files using [OpenAI Whisper](https://github.com/openai/whisper), exposed as a REST API via FastAPI. Runs on port 3004.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) — required by Whisper to decode audio files

## Setup

```bash
# Install ffmpeg
brew install ffmpeg        # macOS

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
```

## Configuration

Edit `.env` before starting the service:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Model size: `base` / `small` / `medium` / `large-v3` |
| `WHISPER_LANGUAGE` | `th` | Language code (e.g. `th`, `en`). Leave empty for auto-detect |
| `AUDIO_BASE_PATH` | `/audio` | Root directory for audio files (used in path mode) |
| `DEFAULT_SOURCE_TYPE` | `path` | `path` = read from volume, `url` = download from URL |

> Larger models are more accurate but slower. `medium` is recommended for Thai.

## Running

```bash
# Local
source .venv/bin/activate
uvicorn app.main:app --port 3004 --reload

# Docker
docker build -t stt-service .

# Run with volume mount (path mode)
docker run -p 3004:3004 -v /your/audio:/audio stt-service

# Run in URL mode (no volume needed)
docker run -p 3004:3004 -e DEFAULT_SOURCE_TYPE=url stt-service

# Run with custom model and language
docker run -p 3004:3004 \
  -e WHISPER_MODEL=medium \
  -e WHISPER_LANGUAGE=th \
  -v /your/audio:/audio \
  stt-service
```

## API

### `GET /health`
```json
{ "status": "ok", "model": "medium", "default_source_type": "url" }
```

### `POST /transcribe`

**From a URL:**
```bash
curl -X POST http://localhost:3004/transcribe \
  -H "Content-Type: application/json" \
  -d '{"source": "https://example.com/audio.mp3", "source_type": "url"}'
```

**From a file path (volume mount):**
```bash
curl -X POST http://localhost:3004/transcribe \
  -H "Content-Type: application/json" \
  -d '{"source": "recording.mp3"}'
```

**Override language per request:**
```bash
curl -X POST http://localhost:3004/transcribe \
  -H "Content-Type: application/json" \
  -d '{"source": "https://example.com/audio.mp3", "source_type": "url", "language": "en"}'
```

**Response:**
```json
{ "text": "สวัสดีครับ" }
```

Supported formats: `.mp3`, `.webm`, `.ogg`

## Tests

```bash
pytest tests/ -v
```
