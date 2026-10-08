from pathlib import Path

from app.models.meeting import ActionItem, Decision, Meeting, MeetingDocumentation, MeetingStatus
from app.services.pipeline import pipeline_service
from app.services.storage.repository import MeetingRepository


def test_pipeline_persists_each_stage_and_completes(tmp_path: Path, monkeypatch):
    repository = MeetingRepository(tmp_path)
    meeting = Meeting(id="d193ae8d-59ac-4d96-8d98-42de9be924e2", filename="audio.wav", status="uploaded")
    repository.create(meeting)
    audio = repository.audio_path(meeting.id)
    audio.write_bytes(b"audio")
    monkeypatch.setattr(pipeline_service, "transcribe_audio", lambda _: "Raw speech")
    monkeypatch.setattr(pipeline_service, "refine_transcript", lambda transcript: transcript + ".")
    monkeypatch.setattr(
        pipeline_service,
        "generate_meeting_documentation",
        lambda _: MeetingDocumentation(
            summary="A meeting.",
            minutes=["The upload was reviewed."],
            decisions=[Decision(decision="Use the current plan.", evidence="The team agreed to it.")],
            tasks=[ActionItem(task="Check the upload.", owner="Ava", deadline="Friday")],
        ),
    )
    pipeline_service.run_pipeline(meeting.id, repository)
    result = repository.get(meeting.id)
    assert result.status == MeetingStatus.completed
    assert result.raw_transcript == "Raw speech"
    assert result.refined_transcript == "Raw speech."
    assert result.progress == 100
    assert repository.backup_path(meeting.id, "raw_transcript").read_text() == "Raw speech"
    assert repository.backup_path(meeting.id, "refined_transcript").read_text() == "Raw speech."
    assert repository.backup_path(meeting.id, "summary").read_text() == "A meeting."
    assert "The upload was reviewed." in repository.backup_path(meeting.id, "minutes").read_text()
    assert "Use the current plan." in repository.backup_path(meeting.id, "decisions").read_text()
    assert "Check the upload." in repository.backup_path(meeting.id, "action_items").read_text()
    assert repository.backup_path(meeting.id, "record").is_file()
    assert repository.backup_path(meeting.id, "json").is_file()


def test_pipeline_records_failure_without_crashing(tmp_path: Path, monkeypatch):
    repository = MeetingRepository(tmp_path)
    meeting = Meeting(id="d193ae8d-59ac-4d96-8d98-42de9be924e2", filename="audio.wav", status="uploaded")
    repository.create(meeting)
    monkeypatch.setattr(pipeline_service, "transcribe_audio", lambda _: (_ for _ in ()).throw(RuntimeError("STT failed")))
    pipeline_service.run_pipeline(meeting.id, repository)
    result = repository.get(meeting.id)
    assert result.status == MeetingStatus.failed
    assert result.error == "STT failed"
