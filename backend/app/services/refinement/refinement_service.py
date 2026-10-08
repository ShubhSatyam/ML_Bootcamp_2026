import logging
from pathlib import Path

from app.core.config import setting
from app.services.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).resolve(
).parents[2] / "prompts" / "refinement_prompt.txt"


def refine_transcript(raw_transcript: str, client: GeminiClient | None = None) -> str:
    if not raw_transcript.strip():
        raise ValueError("Cannot refine an empty transcript.")
    prompt = PROMPT_PATH.read_text(
        encoding="utf-8").replace("{transcript}", raw_transcript)
    logger.info("[REFINEMENT] Starting")
    result = (client or GeminiClient()).generate(
        setting("REFINEMENT_MODEL", "gemini-3.8-flash"), prompt)
    result = result.strip()
    if not result:
        raise RuntimeError(
            "The refinement model returned an empty transcript.")
    logger.info("[REFINEMENT] Completed")
    return result
