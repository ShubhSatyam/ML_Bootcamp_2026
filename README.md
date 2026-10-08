# AI Meeting Assistant

An English meeting-audio assistant that creates a faithful transcript, a lightly corrected transcript, and structured meeting notes. It keeps transcription, transcript refinement, and meeting documentation as three distinct stages. The application is designed for new recordings; it does not contain sample-specific transcript or output logic.

## Overview

Upload an audio recording, start processing, and review raw and refined transcripts, a concise summary, meeting minutes, supported decisions, and action items. Export the transcripts, a human-readable Markdown record, or JSON. Task owners and deadlines not stated in the meeting are labeled **Unspecified**.

## Architecture

```text
React + TypeScript frontend
       │ REST / polling / downloads
       ▼
FastAPI API ─── local JSON + audio storage (data/outputs)
       │
       ├── Stage 1: faster-whisper (English transcription)
       ├── Stage 2: Gemini refinement call (raw transcript only)
       └── Stage 3: separate Gemini documentation call (refined transcript only)
```

See [docs/architecture.md](docs/architecture.md) and [docs/model_pipeline.md](docs/model_pipeline.md) for details.

## Pipeline

1. Validate file extension, size, and audio signature, then store the upload under a generated UUID.
2. Transcribe English speech with faster-whisper and persist the unmodified concatenated segment text as the raw transcript.
3. Make a separate LLM request to correct only plausible transcription errors; persist the refined transcript independently.
4. Send only the refined transcript to a separate documentation request. Validate the JSON using Pydantic, safely repair a trailing comma / parse a fenced JSON response, then make one schema-correction retry if needed.
5. Persist the final record and expose status, results, and downloadable formats through the API.

Processing state and intermediate transcripts are saved between stages. Failures mark the meeting as failed and retain the useful stages already completed.

## Models Used

| Stage | Default | Configuration |
|---|---|---|
| Speech-to-text | faster-whisper `small` | `STT_MODEL`, `STT_DEVICE`, `STT_COMPUTE_TYPE` |
| Transcript refinement | Gemini `gemini-2.5-flash` | `REFINEMENT_MODEL` |
| Meeting documentation | Gemini `gemini-2.5-flash` | `DOCUMENTATION_MODEL` |

## Why These Models

faster-whisper provides a locally executed Whisper transcription model without sending audio to the LLM provider. Gemini is accessed through a small HTTP client, so refinement and documentation model identifiers can be configured independently. The two text-generation calls have separate prompts and responsibilities. The default Whisper model balances quality and local resource requirements; larger Whisper models can be selected when more compute is available.

## Project Structure

```text
backend/
  app/api/                 REST endpoints
  app/core/                Environment configuration
  app/models/              Pydantic data models
  app/prompts/             Separate refinement/documentation prompts
  app/services/            STT, LLM, refinement, documentation, pipeline, storage
  tests/                   Backend tests
frontend/
  src/components/          Shared UI
  src/hooks/               Meeting API / status polling
  src/pages/               Upload, processing, and results screens
  src/services/            REST and download client
  src/types/               API data types
  src/utils/               File validation and display helpers
docs/                      Architecture, pipeline, and demo notes
data/inputs/<meeting-id>/   Uploaded source audio, isolated per recording (gitignored)
data/inputs/sample/         Local demo recordings
data/outputs/<meeting-id>/  Pipeline state (gitignored)
data/outputs/backups/<meeting-id>/
                            Separate raw/refined transcripts, summary, minutes,
                            decisions, action items, and Markdown/JSON records
```

## Setup

Requirements: Python 3.10+, Node.js 20+, npm, and network access for the Gemini API and first-time Whisper model download. A Gemini API key is required for refinement and documentation. faster-whisper uses PyAV for audio decoding.

Copy `backend/.env.example` to `backend/.env`; put your Gemini key in that local file. Copy `frontend/.env.example` to `frontend/.env` if you need to change the API address. Do not commit either `.env` file.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `STT_MODEL` | `small` | faster-whisper model name/size |
| `STT_DEVICE` | `auto` | `auto`, `cpu`, or a supported accelerator |
| `STT_COMPUTE_TYPE` | `auto` | faster-whisper compute type |
| `REFINEMENT_MODEL` | `gemini-2.5-flash` | Gemini model for Stage 2 |
| `DOCUMENTATION_MODEL` | `gemini-2.5-flash` | Gemini model for Stage 3 |
| `LLM_API_KEY` | unset | Gemini API key; backend-only |
| `MAX_FILE_SIZE_MB` | `100` | Maximum upload size |
| `DATA_DIR` | `data/outputs` | Local meeting storage directory |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated frontend origins |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL |
| `VITE_MAX_FILE_SIZE_MB` | `100` | Frontend upload-size validation limit |

### Running Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Add LLM_API_KEY to .env
uvicorn app.main:app --reload
```

Interactive API documentation is available at `http://localhost:8000/docs`; health check: `http://localhost:8000/health`.

### Running Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

### Docker Compose

Set `LLM_API_KEY` in the shell or a root `.env` file, then run `docker compose up --build`. The UI is served at `http://localhost:5173`; generated audio and meeting records persist in the ignored `data/outputs/` directory.

## End-to-End Usage

1. Start the backend and frontend.
2. Upload an English meeting recording in WAV, MP3, M4A, MP4, OGG, FLAC, or WebM format (maximum size is configurable).
3. Select **Start processing**. The page polls backend status and displays actual stage/progress updates.
4. Review the transcript, summary, minutes, decisions, and action items.
5. Download the human-readable meeting record, JSON, or either transcript from the results view.

## API Documentation

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/meetings/upload` | Validate and upload a recording |
| `POST` | `/api/meetings/{id}/process` | Start / retry background processing |
| `GET` | `/api/meetings/{id}` | Retrieve the meeting record |
| `GET` | `/api/meetings/{id}/status` | Retrieve processing status and progress |
| `GET` | `/api/meetings/{id}/download/{format}` | Download `raw-transcript`, `refined-transcript`, `record`, or `json` |
| `GET` | `/health` | Health check |

## Output Formats

- **Raw transcript:** concatenated segment text returned by the STT model, before refinement.
- **Refined transcript:** separate LLM result intended only to correct likely recognition errors.
- **Meeting record:** Markdown containing summary, minutes, decisions with supporting evidence, and action items.
- **JSON:** full meeting data model with the same decisions/tasks as the Markdown output, along with transcript and status fields.

## Testing

```powershell
cd backend
python -m pytest
```

Frontend production build:

```powershell
cd frontend
npm run build
```

Tests cover audio checks, upload/status API behavior, pipeline persistence and failure handling, schema parsing/repair, unspecified task metadata, and avoiding automatic classification of proposals as decisions.

## Known Limitations

- faster-whisper inference is local and can be slow on CPU; model weights are downloaded at first use.
- Refinement and documentation require network access and a valid Gemini API key.
- Local JSON/file storage is suitable for an MVP, not concurrent multi-instance deployment or long-term data management.
- Speaker diarization is not implemented. Very short recordings, noise, overlapping speech, and unclear names can reduce accuracy.
- LLM results are model-generated; review important records against the audio.

## Demo Instructions

Follow [docs/demo.md](docs/demo.md) for a concise live-demo workflow and readiness checks. No bundled sample output is used by the application.

## Technical Workflow

1. The frontend validates size and filename extension and submits multipart audio.
2. FastAPI independently checks the extension, size while streaming, and file signature before storing the upload beneath a generated meeting ID.
3. The pipeline saves progress and the raw transcript, calls the refinement service with its own prompt/model, then calls the documentation service separately with only the refined transcript.
4. The documentation response is parsed, validated against Pydantic models, and retried once if malformed. Missing owner/deadline values normalize to `Unspecified`.
5. The file repository atomically saves meeting JSON. API polling reads actual persisted stage/progress, and download endpoints render exports from that same record.

No ArUco or QR functionality is included because it is unrelated to the meeting-assistant specification.
