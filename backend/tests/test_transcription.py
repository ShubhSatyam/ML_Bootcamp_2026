import sys
from types import SimpleNamespace

from app.services.transcription import transcription_service


class _FakeModel:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, str]]] = []

    def transcribe(self, audio_path: str, **kwargs):
        self.calls.append((audio_path, kwargs))
        return iter([SimpleNamespace(text=" Team stand-up."), SimpleNamespace(text=" Upload is complete.")]), None


def test_transcribe_audio_returns_raw_segment_text(monkeypatch, tmp_path):
    audio_path = tmp_path / "meeting.mp3"
    audio_path.write_bytes(b"\xff\xf3" + b"sample audio")
    model = _FakeModel()

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=lambda *_args, **_kwargs: model))
    monkeypatch.setattr(transcription_service, "_model", None)
    monkeypatch.setattr(transcription_service, "_apply_av_compat", lambda: None)

    transcript = transcription_service.transcribe_audio(audio_path)

    assert transcript == " Team stand-up. Upload is complete."
    assert model.calls == [(str(audio_path), {"language": "en", "task": "transcribe"})]
