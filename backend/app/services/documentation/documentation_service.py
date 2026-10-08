import json
import logging
import re
from pathlib import Path

from pydantic import ValidationError

from app.core.config import setting
from app.models.meeting import MeetingDocumentation
from app.services.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).resolve(
).parents[2] / "prompts" / "documentation_prompt.txt"


def _parse_documentation(response: str) -> MeetingDocumentation:
    candidate = response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```",
                          candidate, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            payload = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Documentation response is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Documentation response must be a JSON object.")
    try:
        return MeetingDocumentation.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            "Documentation response does not match the required schema.") from exc


def generate_meeting_documentation(
    refined_transcript: str, client: GeminiClient | None = None
) -> MeetingDocumentation:
    if not refined_transcript.strip():
        raise ValueError("Cannot document an empty transcript.")
    llm = client or GeminiClient()
    model = setting("DOCUMENTATION_MODEL", "gemini-3.8-flash")
    template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.replace("{transcript}", refined_transcript)
    logger.info("[DOCUMENTATION] Starting")
    try:
        result = _parse_documentation(
            llm.generate(model, prompt, json_mode=True))
    except ValueError:
        correction_prompt = (
            "Return only valid JSON matching this schema exactly: summary (string), minutes (array of strings), "
            "decisions (array of objects with decision and evidence strings), and tasks (array of objects with "
            "task, owner, and deadline strings). Use Unspecified for unstated task owners and deadlines. "
            "Never invent owners, deadlines, decisions, tasks, commitments, or suggestions. "
            "Do not convert proposals, possibilities, questions, hypotheticals, or discussion into final decisions or actions. "
            "Do not use common sense or assumptions to fill missing information.\n\n"
            + template.replace("{transcript}", refined_transcript)
        )
        try:
            result = _parse_documentation(llm.generate(
                model, correction_prompt, json_mode=True))
        except ValueError as exc:
            raise RuntimeError(
                "The documentation model returned invalid structured output after one retry.") from exc
    logger.info("[DOCUMENTATION] Completed")
    return result
