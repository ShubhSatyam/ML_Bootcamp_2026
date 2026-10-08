from pathlib import Path

from fastapi.testclient import TestClient

from app.api.meetings import get_repository
from app.main import app
from app.models.meeting import Decision, Meeting, MeetingStatus, Task
from app.services.storage.repository import MeetingRepository


def test_upload_status_and_missing_meeting(tmp_path: Path):
    repository = MeetingRepository(tmp_path)
    app.dependency_overrides[get_repository] = lambda: repository
    client = TestClient(app)
    try:
        wav = b"RIFF\x00\x00\x00\x00WAVEfmt "
        response = client.post(
            "/api/meetings/upload", files={"audio": ("meeting.wav", wav, "text/plain")})
        assert response.status_code == 201
        meeting_id = response.json()["id"]
        status_response = client.get(f"/api/meetings/{meeting_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "uploaded"
        assert client.get("/api/meetings/not-a-uuid").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_upload_rejects_content_that_does_not_match_extension(tmp_path: Path):
    app.dependency_overrides[get_repository] = lambda: MeetingRepository(
        tmp_path)
    client = TestClient(app)
    try:
        response = client.post(
            "/api/meetings/upload", files={"audio": ("meeting.wav", b"not audio", "audio/wav")})
        assert response.status_code == 415
    finally:
        app.dependency_overrides.clear()


def test_download_exports_share_the_same_decisions_and_tasks(tmp_path: Path):
    repository = MeetingRepository(tmp_path)
    meeting = Meeting(
        id="d193ae8d-59ac-4d96-8d98-42de9be924e2",
        filename="meeting.wav",
        status=MeetingStatus.completed,
        raw_transcript="Raw words",
        refined_transcript="Refined words",
        summary="A concise summary.",
        minutes=["The report was discussed."],
        decisions=[Decision(decision="Keep the current plan.",
                            evidence="We agreed to keep the current plan.")],
        tasks=[Task(task="Prepare the report.",
                    owner="Unspecified", deadline="Friday")],
    )
    repository.create(meeting)
    app.dependency_overrides[get_repository] = lambda: repository
    client = TestClient(app)
    try:
        json_response = client.get(f"/api/meetings/{meeting.id}/download/json")
        record_response = client.get(
            f"/api/meetings/{meeting.id}/download/record")
        assert json_response.status_code == 200
        assert record_response.status_code == 200
        exported = json_response.json()
        assert exported["decisions"][0]["decision"] in record_response.text
        assert exported["tasks"][0]["task"] in record_response.text
        assert exported["tasks"][0]["owner"] == "Unspecified"
        assert "Unspecified" in record_response.text
        assert client.get(
            f"/api/meetings/{meeting.id}/download/unknown").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_download_rejects_unfinished_meeting(tmp_path: Path):
    repository = MeetingRepository(tmp_path)
    meeting = Meeting(id="d193ae8d-59ac-4d96-8d98-42de9be924e2",
                      filename="meeting.wav", status="uploaded")
    repository.create(meeting)
    app.dependency_overrides[get_repository] = lambda: repository
    client = TestClient(app)
    try:
        response = client.get(f"/api/meetings/{meeting.id}/download/json")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_transcription_compat_removes_metadata_errors(monkeypatch):
    import av

    from app.services.transcription import transcription_service

    calls = []

    def fake_open(*args, **kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(av, "open", fake_open)
    monkeypatch.setattr(av, "container", type(
        "Container", (), {"open": fake_open}), raising=False)

    transcription_service._apply_av_compat()
    av.open("demo.mp3", "r", metadata_errors="ignore")

    assert calls and "metadata_errors" not in calls[0]
