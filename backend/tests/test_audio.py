from pathlib import Path

import pytest

from app.utils.audio import validate_audio_file


def test_accepts_valid_wav_header(tmp_path: Path):
    path = tmp_path / "meeting.wav"
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    validate_audio_file(path)


@pytest.mark.parametrize(
    ("name", "content", "error"),
    [
        ("audio.exe", b"RIFF\x00\x00\x00\x00WAVE", "Unsupported"),
        ("audio.wav", b"", "empty"),
        ("audio.wav", b"not an audio file", "do not match"),
    ],
)
def test_rejects_invalid_audio(tmp_path: Path, name: str, content: bytes, error: str):
    path = tmp_path / name
    path.write_bytes(content)
    with pytest.raises(ValueError, match=error):
        validate_audio_file(path)


def test_rejects_oversized_audio(tmp_path: Path):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    with pytest.raises(ValueError, match="size limit"):
        validate_audio_file(path, max_bytes=4)
