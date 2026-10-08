import logging
from pathlib import Path

from app.models.meeting import Meeting, MeetingStatus
from app.services.documentation.documentation_service import generate_meeting_documentation
from app.services.refinement.refinement_service import refine_transcript
from app.services.storage.repository import MeetingRepository
from app.services.transcription.transcription_service import transcribe_audio

logger = logging.getLogger(__name__)


def run_pipeline(meeting_id: str, repository: MeetingRepository | None = None) -> None:
    repo = repository or MeetingRepository()
    try:
        meeting = repo.get(meeting_id)
        meeting = meeting.model_copy(
            update={"status": MeetingStatus.processing, "current_stage": "Transcription", "progress": 10, "error": None}
        )
        repo.save(meeting)
        logger.info("[PIPELINE] Meeting %s started", meeting_id)

        raw_transcript = transcribe_audio(repo.audio_path(meeting_id))
        meeting = meeting.model_copy(update={"raw_transcript": raw_transcript, "progress": 35})
        repo.save(meeting)

        meeting = meeting.model_copy(update={"current_stage": "Transcript refinement", "progress": 45})
        repo.save(meeting)
        refined_transcript = refine_transcript(raw_transcript)
        meeting = meeting.model_copy(update={"refined_transcript": refined_transcript, "progress": 70})
        repo.save(meeting)

        meeting = meeting.model_copy(update={"current_stage": "Meeting documentation", "progress": 75})
        repo.save(meeting)
        documentation = generate_meeting_documentation(refined_transcript)

        meeting = meeting.model_copy(
            update={
                "current_stage": "Finalizing",
                "progress": 95,
                "summary": documentation.summary,
                "minutes": documentation.minutes,
                "decisions": documentation.decisions,
                "tasks": documentation.tasks,
            }
        )
        repo.save(meeting)
        completed = meeting.model_copy(
            update={"status": MeetingStatus.completed, "current_stage": None, "progress": 100}
        )
        repo.save(completed)
        logger.info("[PIPELINE] Meeting %s completed", meeting_id)
    except Exception as exc:
        logger.exception("[PIPELINE] Meeting %s failed", meeting_id)
        try:
            meeting = repo.get(meeting_id)
            failed = meeting.model_copy(
                update={
                    "status": MeetingStatus.failed,
                    "current_stage": None,
                    "error": str(exc)[:500] or "Meeting processing failed.",
                }
            )
            repo.save(failed)
        except Exception:
            logger.exception("[PIPELINE] Could not persist failure status for meeting %s", meeting_id)
