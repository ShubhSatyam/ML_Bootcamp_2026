from pathlib import Path

from app.models.meeting import Meeting, MeetingDocumentation, MeetingStatus
from app.services.pipeline import pipeline_service
from app.services.storage.repository import MeetingRepository


def test_pipeline_persists_each_stage_and_completes(tmp_path: Path, monkeypatch):
    repository = MeetingRepository(tmp_path)
    meeting = Meeting(id="d193ae8d-59ac-4d96-8d98-42de9be924e2", filename="audio.wav", status="uploaded")
    repository.create(meeting)
    audio = repository._meeting_directory(meeting.id) / "audio.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(pipeline_service, "transcribe_audio", lambda _: "Raw speech")
    monkeypatch.setattr(pipeline_service, "refine_transcript", lambda transcript: transcript + ".")
    monkeypatch.setattr(
        pipeline_service,
        "generate_meeting_documentation",
        lambda _: MeetingDocumentation(summary="A meeting.", minutes=[], decisions=[], tasks=[]),
    )
    pipeline_service.run_pipeline(meeting.id, repository)
    result = repository.get(meeting.id)
    assert result.status == MeetingStatus.completed
    assert result.raw_transcript == "Raw speech"
    assert result.refined_transcript == "Raw speech."
    assert result.progress == 100


def test_pipeline_records_failure_without_crashing(tmp_path: Path, monkeypatch):
    repository = MeetingRepository(tmp_path)
    meeting = Meeting(id="d193ae8d-59ac-4d96-8d98-42de9be924e2", filename="audio.wav", status="uploaded")
    repository.create(meeting)
    monkeypatch.setattr(pipeline_service, "transcribe_audio", lambda _: (_ for _ in ()).throw(RuntimeError("STT failed")))
    pipeline_service.run_pipeline(meeting.id, repository)
    result = repository.get(meeting.id)
    assert result.status == MeetingStatus.failed
    assert result.error == "STT failed"
