import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env", override=False)


def setting(name: str, default: str) -> str:
    return os.getenv(name, default)


def max_file_size_bytes() -> int:
    try:
        size_mb = int(setting("MAX_FILE_SIZE_MB", "100"))
    except ValueError as exc:
        raise ValueError("MAX_FILE_SIZE_MB must be a positive integer") from exc
    if size_mb < 1:
        raise ValueError("MAX_FILE_SIZE_MB must be a positive integer")
    return size_mb * 1024 * 1024


def data_directory() -> Path:
    configured = Path(setting("DATA_DIR", str(PROJECT_ROOT / "data" / "outputs")))
    if not configured.is_absolute():
        configured = (BACKEND_DIR / configured).resolve()
    configured.mkdir(parents=True, exist_ok=True)
    return configured


def cors_origins() -> list[str]:
    return [origin.strip() for origin in setting("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
