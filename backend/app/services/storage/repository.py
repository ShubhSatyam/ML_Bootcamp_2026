import re
import tempfile
from pathlib import Path
from uuid import UUID

from app.core.config import data_directory
from app.models.meeting import Meeting


class MeetingRepository:
    def __init__(self, root: Path | None = None):
        self.root = root or data_directory()

    def _meeting_directory(self, meeting_id: str) -> Path:
        try:
            safe_id = str(UUID(meeting_id))
        except ValueError as exc:
            raise FileNotFoundError("Meeting not found") from exc
        directory = (self.root / safe_id).resolve()
        if directory.parent != self.root.resolve():
            raise FileNotFoundError("Meeting not found")
        return directory

    def audio_path(self, meeting_id: str) -> Path:
        meeting = self.get(meeting_id)
        extension = Path(meeting.filename).suffix.lower()
        return self._meeting_directory(meeting_id) / f"audio{extension}"

    def create(self, meeting: Meeting) -> None:
        directory = self._meeting_directory(meeting.id)
        directory.mkdir(parents=True, exist_ok=False)
        self.save(meeting)

    def get(self, meeting_id: str) -> Meeting:
        path = self._meeting_directory(meeting_id) / "meeting.json"
        if not path.is_file():
            raise FileNotFoundError("Meeting not found")
        return Meeting.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, meeting: Meeting) -> None:
        directory = self._meeting_directory(meeting.id)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / "meeting.json"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as temporary:
            temporary.write(meeting.model_dump_json(indent=2))
            temporary_path = Path(temporary.name)
        temporary_path.replace(destination)

    def transcript(self, meeting_id: str, field: str) -> str:
        if field not in {"raw_transcript", "refined_transcript"}:
            raise ValueError("Invalid transcript type")
        value = getattr(self.get(meeting_id), field)
        if value is None:
            raise FileNotFoundError("Transcript is not available yet")
        return value

    def json_export(self, meeting_id: str) -> bytes:
        return self.get(meeting_id).model_dump_json(indent=2).encode("utf-8")


def sanitize_filename(filename: str | None) -> str:
    name = Path(filename or "meeting-audio").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name[:120] or "meeting-audio"
