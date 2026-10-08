import re
import tempfile
import json
from pathlib import Path
from uuid import UUID

from app.core.config import data_directory
from app.models.meeting import Meeting


class MeetingRepository:
    """File-backed meeting state plus durable, human-readable stage backups."""

    BACKUP_FILES = {
        "raw_transcript": Path("raw-transcripts") / "raw-transcript.txt",
        "refined_transcript": Path("refined-transcripts") / "refined-transcript.txt",
        "summary": Path("summary") / "summary.txt",
        "minutes": Path("minutes") / "minutes.md",
        "decisions": Path("decisions") / "decisions.json",
        "action_items": Path("action-items") / "action-items.json",
        "record": Path("records") / "meeting-record.md",
        "json": Path("records") / "meeting-record.json",
    }

    def __init__(self, root: Path | None = None):
        self.root = root or data_directory()
        self.input_root = self.root.parent / "inputs" if root is None else self.root / "inputs"

    def _meeting_directory(self, meeting_id: str) -> Path:
        try:
            safe_id = str(UUID(meeting_id))
        except ValueError as exc:
            raise FileNotFoundError("Meeting not found") from exc
        directory = (self.root / safe_id).resolve()
        if directory.parent != self.root.resolve():
            raise FileNotFoundError("Meeting not found")
        return directory

    def backup_directory(self, meeting_id: str) -> Path:
        """Return the separate backup tree for one UUID-scoped recording."""
        safe_id = self._meeting_directory(meeting_id).name
        directory = (self.root / "backups" / safe_id).resolve()
        if directory.parent != (self.root / "backups").resolve():
            raise FileNotFoundError("Meeting not found")
        return directory

    def input_directory(self, meeting_id: str) -> Path:
        """Return the UUID-scoped source-audio directory for one recording."""
        safe_id = self._meeting_directory(meeting_id).name
        directory = (self.input_root / safe_id).resolve()
        if directory.parent != self.input_root.resolve():
            raise FileNotFoundError("Meeting not found")
        return directory

    def backup_path(self, meeting_id: str, artifact: str) -> Path:
        try:
            relative_path = self.BACKUP_FILES[artifact]
        except KeyError as exc:
            raise ValueError("Invalid backup artifact") from exc
        return self.backup_directory(meeting_id) / relative_path

    def audio_path(self, meeting_id: str) -> Path:
        meeting = self.get(meeting_id)
        extension = Path(meeting.filename).suffix.lower()
        return self.input_directory(meeting_id) / f"audio{extension}"

    def create(self, meeting: Meeting) -> None:
        directory = self._meeting_directory(meeting.id)
        directory.mkdir(parents=True, exist_ok=False)
        backup_directory = self.backup_directory(meeting.id)
        for relative_path in self.BACKUP_FILES.values():
            (backup_directory / relative_path).parent.mkdir(parents=True, exist_ok=True)
        self.input_directory(meeting.id).mkdir(parents=True, exist_ok=False)
        self.save(meeting)

    def get(self, meeting_id: str) -> Meeting:
        path = self._meeting_directory(meeting_id) / "meeting.json"
        if not path.is_file():
            raise FileNotFoundError("Meeting not found")
        return Meeting.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, meeting: Meeting) -> None:
        directory = self._meeting_directory(meeting.id)
        directory.mkdir(parents=True, exist_ok=True)
        self._atomic_write_text(directory / "meeting.json", meeting.model_dump_json(indent=2))

    def save_raw_transcript(self, meeting: Meeting) -> None:
        if meeting.raw_transcript is None:
            raise ValueError("Raw transcript is not available.")
        self._atomic_write_text(
            self.backup_path(meeting.id, "raw_transcript"), meeting.raw_transcript)

    def save_refined_transcript(self, meeting: Meeting) -> None:
        if meeting.refined_transcript is None:
            raise ValueError("Refined transcript is not available.")
        self._atomic_write_text(
            self.backup_path(meeting.id, "refined_transcript"), meeting.refined_transcript)

    def save_documentation_outputs(self, meeting: Meeting) -> None:
        if meeting.summary is None:
            raise ValueError("Meeting documentation is not available.")
        self._atomic_write_text(self.backup_path(meeting.id, "summary"), meeting.summary)
        self._atomic_write_text(
            self.backup_path(meeting.id, "minutes"),
            "\n".join(f"- {minute}" for minute in meeting.minutes) or "- None identified",
        )
        self._atomic_write_text(
            self.backup_path(meeting.id, "decisions"),
            json.dumps([decision.model_dump() for decision in meeting.decisions], indent=2),
        )
        self._atomic_write_text(
            self.backup_path(meeting.id, "action_items"),
            json.dumps([task.model_dump() for task in meeting.tasks], indent=2),
        )
        self._atomic_write_text(self.backup_path(meeting.id, "record"), render_meeting_record(meeting))
        self._atomic_write_text(self.backup_path(meeting.id, "json"), meeting.model_dump_json(indent=2))

    @staticmethod
    def _atomic_write_text(destination: Path, content: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as temporary:
            temporary.write(content)
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


def render_meeting_record(meeting: Meeting) -> str:
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


def sanitize_filename(filename: str | None) -> str:
    name = Path(filename or "meeting-audio").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name[:120] or "meeting-audio"
