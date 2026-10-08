# Model Pipeline

## Stage 1 — Transcription

`app/services/transcription/transcription_service.py` lazily loads faster-whisper and requests English transcription. It consumes validated audio locally, concatenates the model's segment text without transcript rewriting, and saves this value to `raw_transcript`.

Configure the model using `STT_MODEL` (default `small`), `STT_DEVICE`, and `STT_COMPUTE_TYPE`. The first call may download model weights.

## Stage 2 — Transcript refinement

`app/services/refinement/refinement_service.py` loads `app/prompts/refinement_prompt.txt` and makes its own Gemini request using `REFINEMENT_MODEL`. It is instructed to correct only plausible recognition errors and preserve names, numbers, negations, commitments, uncertainty, and speaker intent. It must not summarize or add information. The result is saved separately to `refined_transcript`.

## Stage 3 — Meeting documentation

`app/services/documentation/documentation_service.py` makes a distinct Gemini request using `DOCUMENTATION_MODEL` and `documentation_prompt.txt`. Its input is the refined transcript, not the raw transcript. The response includes:

- `summary: string`
- `minutes: string[]`
- `decisions: { decision, evidence }[]`
- `tasks: { task, owner, deadline }[]`

Pydantic validates the structured result. JSON fences and trailing commas are handled with safe parsing. If parsing or schema validation fails, the service makes one correction-prompt retry with the transcript, then raises a controlled error if it remains invalid. Empty task owner/deadline fields are normalized to `Unspecified`; the model is explicitly prohibited from inferring them or turning proposals into decisions.

## Persisted artifacts

For every recording, the repository keeps pipeline state in `data/outputs/<meeting-uuid>/meeting.json` and stores durable user-facing artifacts separately in `data/outputs/backups/<meeting-uuid>/`. Raw and refined transcripts have different folders, while summary, minutes, decisions, action items, and the final Markdown/JSON records are each written as their corresponding stage succeeds. This makes each recording independently recoverable and prevents later uploads from overwriting earlier outputs.

## Configuration

The backend reads `backend/.env` when present, and existing process environment values take precedence. `LLM_API_KEY` is used only for Gemini requests. Model IDs can be changed independently for Stages 2 and 3. Prompts are files, not inline Python strings.
