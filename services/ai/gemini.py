import asyncio
from typing import Any

import httpx

from core.config import settings
from core.exceptions import LLMUnavailableError
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# 429 is deliberately absent: a quota window resets in tens of seconds, so
# retrying inside a request only burns the remaining quota three times faster
# and still makes the caller wait. Fail fast and let them try again.
RETRY_ON = {408, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
QUOTA_EXHAUSTED = 429

_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    """One client for the whole process.

    A client per call throws away the connection pool, so every AI request pays
    for a fresh TCP connection and TLS handshake to Google. The timeout is
    passed per request instead, because each caller may set its own.
    """
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient()
    return _client


async def close_http() -> None:
    """Release the shared client. Called once, when the app shuts down."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


class GeminiProvider:
    """Talks to Gemini over its REST API.

    Deliberately not the vendor SDK: httpx is already a dependency, the timeout
    is ours to set, and the payload stays readable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self._model = model or settings.LLM_MODEL
        self._timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self._max_output_tokens = max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS

    def _payload(self, system: str, user: str, json_schema: dict[str, Any] | None) -> dict[str, Any]:
        generation: dict[str, Any] = {
            "maxOutputTokens": self._max_output_tokens,
            "temperature": 0.4,
        }
        if json_schema is not None:
            generation["responseMimeType"] = "application/json"
            generation["responseSchema"] = json_schema
        return {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": generation,
        }

    @staticmethod
    def _read_text(body: dict[str, Any]) -> str:
        candidates = body.get("candidates") or []
        if not candidates:
            raise LLMUnavailableError()
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise LLMUnavailableError()
        return text

    async def complete(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        if not self._api_key:
            logger.error("llm_key_missing")
            raise LLMUnavailableError()

        url = f"{BASE_URL}/{self._model}:generateContent"
        payload = self._payload(system, user, json_schema)

        client = _http()
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"x-goog-api-key": self._api_key},
                    timeout=self._timeout,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                logger.warning(
                    "llm_transport_error",
                    extra={"extra_fields": {"attempt": attempt, "error": str(exc)}},
                )
                if attempt == MAX_ATTEMPTS:
                    raise LLMUnavailableError() from exc
                await asyncio.sleep(0.5 * attempt)
                continue

            if response.status_code in RETRY_ON and attempt < MAX_ATTEMPTS:
                logger.warning(
                    "llm_retrying",
                    extra={"extra_fields": {"attempt": attempt, "status": response.status_code}},
                )
                await asyncio.sleep(0.5 * attempt)
                continue

            if response.status_code == QUOTA_EXHAUSTED:
                logger.warning(
                    "llm_quota_exhausted",
                    extra={"extra_fields": {"model": self._model, "body": response.text[:200]}},
                )
                raise LLMUnavailableError()

            if response.status_code >= 400:
                logger.error(
                    "llm_request_failed",
                    extra={
                        "extra_fields": {
                            "status": response.status_code,
                            "body": response.text[:300],
                        }
                    },
                )
                raise LLMUnavailableError()

            return self._read_text(response.json())

        raise LLMUnavailableError()
