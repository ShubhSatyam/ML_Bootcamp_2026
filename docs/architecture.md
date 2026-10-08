# Architecture

```text
Browser (React / TypeScript)
  ├─ multipart upload
  ├─ status polling
  └─ JSON / text / Markdown downloads
             │
             ▼
FastAPI
  ├─ audio validation and UUID-scoped storage
  ├─ REST routes and Pydantic response schemas
  └─ pipeline service
       ├─ faster-whisper transcription (local)
       ├─ Gemini transcript refinement (LLM call 1)
       └─ Gemini meeting documentation (LLM call 2)
             │
             ▼
data/outputs/<meeting-uuid>/
  ├─ audio.<format>
  └─ meeting.json (atomic updates, persisted at each stage)
```

Routes handle HTTP behavior and delegate processing to services. Audio and meeting state use a small file-based repository so a database can replace it without changing model-service boundaries. Each meeting ID is UUID-validated before filesystem access. User filenames are reduced to a safe display name; they are not used to construct paths.

The `raw_transcript` and `refined_transcript` are distinct fields and are saved as their respective stages finish. Status includes current stage and progress so the UI displays backend state rather than simulated progress. Pipeline exceptions are logged and persisted as a user-facing failure message without returning stack traces through the API.

## Security and privacy

- Audio file extension, size, and content signature are validated server-side; the client MIME header is not trusted.
- API credentials are backend environment variables and are sent as an HTTP header, not logged.
- API responses do not expose filesystem locations or credentials.
- CORS origins are configurable. Upload and generated data are excluded from version control.
- The MVP has no authentication; deploy only behind an appropriate trusted boundary.
