# Backend

FastAPI REST API and processing services for the AI Meeting Assistant. The API lives in `app/api/`; model and pipeline logic are isolated under `app/services/`.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Configure LLM_API_KEY in .env
uvicorn app.main:app --reload
```

The API docs are at `http://localhost:8000/docs`. Configure models, file size, storage, and CORS using `.env.example`. Uploads and JSON records are stored under `data/outputs/` by default (gitignored).

## Test

```powershell
python -m pytest
```

The first transcription downloads the selected faster-whisper model. Audio decoding is provided by PyAV.
