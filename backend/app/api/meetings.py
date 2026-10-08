import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.models.meeting import Meeting, MeetingStatus
from app.services.pipeline.pipeline_service import run_pipeline
from app.services.storage.repository import MeetingRepository, sanitize_filename
from app.utils.audio import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def get_repository() -> MeetingRepository:
    return MeetingRepository()


@router.post("/upload", response_model=Meeting, status_code=status.HTTP_201_CREATED)
async def upload_meeting(
    audio: UploadFile = File(...),
    repository: MeetingRepository = Depends(get_repository),
) -> Meeting:
    filename = sanitize_filename(audio.filename)
    meeting = Meeting(id=str(uuid.uuid4()), filename=filename, status=MeetingStatus.uploaded)
    directory = repository._meeting_directory(meeting.id)
    directory.mkdir(parents=True, exist_ok=False)
    destination = directory / f"audio{Path(filename).suffix.lower()}"
    try:
        await save_upload(audio, destination)
        repository.save(meeting)
    except Exception:
        destination.unlink(missing_ok=True)
        try:
            directory.rmdir()
        except OSError:
            pass
        raise
    logger.info("[UPLOAD] Meeting %s uploaded", meeting.id)
    return meeting


@router.post("/{meeting_id}/process", response_model=Meeting, status_code=status.HTTP_202_ACCEPTED)
def process_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    repository: MeetingRepository = Depends(get_repository),
) -> Meeting:
    try:
        meeting = repository.get(meeting_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meeting not found.") from exc
    if meeting.status == MeetingStatus.processing:
        return meeting
    if meeting.status == MeetingStatus.completed:
        return meeting
    queued = meeting.model_copy(update={"status": MeetingStatus.processing, "current_stage": "Starting", "progress": 1})
    repository.save(queued)
    background_tasks.add_task(run_pipeline, meeting_id, repository)
    return queued


@router.get("/{meeting_id}/status")
def meeting_status(meeting_id: str, repository: MeetingRepository = Depends(get_repository)) -> dict:
    try:
        meeting = repository.get(meeting_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meeting not found.") from exc
    return {
        "id": meeting.id,
        "status": meeting.status,
        "current_stage": meeting.current_stage,
        "progress": meeting.progress,
        "error": meeting.error,
    }


@router.get("/{meeting_id}", response_model=Meeting)
def meeting_details(meeting_id: str, repository: MeetingRepository = Depends(get_repository)) -> Meeting:
    try:
        return repository.get(meeting_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meeting not found.") from exc


@router.get("/{meeting_id}/download/{format}")
def download_meeting(
    meeting_id: str,
    format: str,
    repository: MeetingRepository = Depends(get_repository),
) -> Response:
    try:
        meeting = repository.get(meeting_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meeting not found.") from exc
    if meeting.status != MeetingStatus.completed:
        raise HTTPException(status_code=409, detail="Meeting results are not ready to download.")
    if format == "raw-transcript":
        content, media_type, filename = meeting.raw_transcript, "text/plain; charset=utf-8", "raw-transcript.txt"
    elif format == "refined-transcript":
        content, media_type, filename = meeting.refined_transcript, "text/plain; charset=utf-8", "refined-transcript.txt"
    elif format == "record":
        content = _human_readable_record(meeting)
        media_type, filename = "text/markdown; charset=utf-8", "meeting-record.md"
    elif format == "json":
        return Response(
            content=repository.json_export(meeting_id),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="meeting-record.json"'},
        )
    else:
        raise HTTPException(status_code=404, detail="Unsupported download format.")
    return Response(
        content=content or "",
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _human_readable_record(meeting: Meeting) -> str:
    decisions = "\n".join(
        f"- {item.decision}\n  Evidence: {item.evidence}" for item in meeting.decisions
    ) or "- None identified"
    tasks = "\n".join(
        f"- **Task:** {item.task}\n  **Owner:** {item.owner}\n  **Deadline:** {item.deadline}" for item in meeting.tasks
    ) or "- None identified"
    minutes = "\n".join(f"- {item}" for item in meeting.minutes) or "- None identified"
    return (
        f"# Meeting Record: {meeting.filename}\n\n"
        f"## Meeting Summary\n{meeting.summary or ''}\n\n"
        f"## Meeting Minutes\n{minutes}\n\n"
        f"## Key Decisions\n{decisions}\n\n"
        f"## Action Items\n{tasks}\n"
    )
