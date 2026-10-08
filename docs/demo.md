# Demo Guide

## Before the demo

1. Install backend requirements and frontend npm packages.
2. Add a valid Gemini key to `backend/.env`.
3. Ensure network access and enough disk space for the selected faster-whisper model.
4. Start FastAPI (`uvicorn app.main:app --reload`) and Vite (`npm run dev`).
5. Verify `http://localhost:8000/health` returns `{"status":"ok"}` and open `http://localhost:5173`.
6. Prepare an English meeting recording in a supported format. The application has no hardcoded demo recording or expected result.

## Live walkthrough

1. Drag the recording into the upload area (or browse to it) and upload.
2. Start processing. Explain that the displayed stage and progress are read from the backend pipeline.
3. Review raw and refined transcript separately, optionally use **Compare both**, then open summary, minutes, decisions, and action items.
4. Highlight that unsupported decisions are omitted and unstated task owners/deadlines appear as `Unspecified`.
5. Download the Markdown meeting record, JSON, and transcript files.

## Expected runtime considerations

The first run may spend time downloading faster-whisper model files. CPU transcription speed depends on recording length and hardware. Refinement and documentation need Gemini network access; failures are shown on the processing screen and persisted on the meeting record.
