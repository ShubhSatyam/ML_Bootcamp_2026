import os
import time

import httpx


class GeminiClient:
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, timeout_seconds: float = 90):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.timeout_seconds = timeout_seconds

    def generate(self, model: str, prompt: str, json_mode: bool = False) -> str:
        if not self.api_key:
            raise RuntimeError(
                "LLM_API_KEY is not configured. Add a Gemini API key to backend/.env.")
        generation_config = {"temperature": 0}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = httpx.post(
                    self.endpoint.format(model=model),
                    headers={"x-goog-api-key": self.api_key},
                    json={
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": generation_config,
                    },
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                break
            except httpx.TimeoutException as exc:
                last_error = RuntimeError(
                    "The language model request timed out. Please retry.")
                if attempt == 2:
                    raise last_error from exc
                time.sleep(2 ** attempt)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {401, 403}:
                    raise RuntimeError(
                        "The language model rejected the configured API key.") from exc
                if exc.response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                    last_error = RuntimeError(
                        f"The language model request failed (HTTP {exc.response.status_code}).")
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(
                    f"The language model request failed (HTTP {exc.response.status_code}).") from exc
            except httpx.HTTPError as exc:
                last_error = RuntimeError(
                    "Could not connect to the language model service.")
                if attempt == 2:
                    raise last_error from exc
                time.sleep(2 ** attempt)
        else:
            if last_error is not None:
                raise last_error

        try:
            result = response.json()[
                "candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "The language model returned an empty or invalid response.") from exc
        if not isinstance(result, str) or not result.strip():
            raise RuntimeError(
                "The language model returned an empty response.")
        return result
