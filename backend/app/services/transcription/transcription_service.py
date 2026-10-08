import logging
import os
from pathlib import Path
from threading import Lock

from app.core.config import setting
from app.utils.audio import validate_audio_file

logger = logging.getLogger(__name__)
_model = None
_model_lock = Lock()


def _apply_av_compat() -> None:
    import av

    if getattr(av.open, "_meeting_assistant_compat", False):
        return

    original = av.open

    def _compat_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return original(*args, **kwargs)

    _compat_open._meeting_assistant_compat = True
    av.open = _compat_open
    if hasattr(av, "container"):
        av.container.open = _compat_open


def transcribe_audio(audio_path: Path) -> str:
    validate_audio_file(audio_path)
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Speech recognition is unavailable. Install backend requirements and retry.") from exc

    _apply_av_compat()
    os.environ.setdefault("CT2_USE_CUDA", "0")

    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                model_name = setting("STT_MODEL", "small")
                logger.info("[STT] Loading model %s", model_name)
                _model = WhisperModel(
                    model_name,
                    device=setting("STT_DEVICE", "cpu"),
                    compute_type=setting("STT_COMPUTE_TYPE", "int8"),
                )
    logger.info("[STT] Starting transcription")
    segments, _ = _model.transcribe(
        str(audio_path), language="en", task="transcribe")
    raw_transcript = "".join(segment.text for segment in segments)
    if not raw_transcript.strip():
        raise RuntimeError(
            "No English speech could be recognized in the audio.")
    logger.info("[STT] Completed")
    return raw_transcript
