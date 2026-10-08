from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import max_file_size_bytes


SIGNATURES = {
    ".wav": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE",
    ".mp3": lambda data: data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0),
    ".flac": lambda data: data.startswith(b"fLaC"),
    ".ogg": lambda data: data.startswith(b"OggS"),
    ".m4a": lambda data: len(data) >= 8 and data[4:8] == b"ftyp",
    ".mp4": lambda data: len(data) >= 8 and data[4:8] == b"ftyp",
    ".webm": lambda data: data.startswith(bytes.fromhex("1A45DFA3")),
}


def validate_audio_file(path: Path, filename: str | None = None, max_bytes: int | None = None) -> None:
    name = filename or path.name
    extension = Path(name).suffix.lower()
    if extension not in SIGNATURES:
        raise ValueError("Unsupported audio format. Use WAV, MP3, M4A, MP4, OGG, FLAC, or WebM.")
    if not path.is_file():
        raise ValueError("The uploaded audio file could not be read.")
    size = path.stat().st_size
    if size == 0:
        raise ValueError("The uploaded audio file is empty.")
    if size > (max_bytes if max_bytes is not None else max_file_size_bytes()):
        raise ValueError("The audio file exceeds the configured upload size limit.")
    with path.open("rb") as audio:
        header = audio.read(16)
    if not SIGNATURES[extension](header):
        raise ValueError("The file contents do not match a supported audio format.")


async def save_upload(upload: UploadFile, destination: Path) -> None:
    max_bytes = max_file_size_bytes()
    written = 0
    header = b""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Audio file exceeds the configured upload size limit.",
                    )
                if len(header) < 16:
                    header += chunk[: 16 - len(header)]
                target.write(chunk)
        if written == 0:
            raise HTTPException(status_code=400, detail="The uploaded audio file is empty.")
        extension = Path(upload.filename or "").suffix.lower()
        if extension not in SIGNATURES:
            raise HTTPException(status_code=415, detail="Unsupported audio format. Use WAV, MP3, M4A, MP4, OGG, FLAC, or WebM.")
        if not SIGNATURES[extension](header):
            raise HTTPException(status_code=415, detail="The file contents do not match a supported audio format.")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
