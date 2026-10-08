import logging
import uuid
from pathlib import Path
from shutil import rmtree

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.models.meeting import Meeting, MeetingStatus
from app.services.pipeline.pipeline_service import run_pipeline
from app.services.storage.repository import MeetingRepository, render_meeting_record, sanitize_filename
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
    repository.create(meeting)
    destination = repository.audio_path(meeting.id)
    try:
        await save_upload(audio, destination)
    except Exception:
        destination.unlink(missing_ok=True)
        rmtree(repository._meeting_directory(meeting.id), ignore_errors=True)
        rmtree(repository.input_directory(meeting.id), ignore_errors=True)
        rmtree(repository.backup_directory(meeting.id), ignore_errors=True)
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
        content = render_meeting_record(meeting)
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
