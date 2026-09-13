"""The HTTP half of talking to a language model, shared by every provider.

Retries, timeouts and the connection pool are the same whoever we are calling,
so they live here and a provider file only has to know its vendor's payload.
"""

import asyncio
from typing import Any

import httpx

from core.exceptions import LLMUnavailableError
from utils.logger import get_logger

logger = get_logger(__name__)

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
    for a fresh TCP connection and TLS handshake. The timeout is passed per
    request instead, because each caller may set its own.
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


async def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    """POST and return the decoded body, or raise `LLMUnavailableError`."""
    client = _http()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)
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
                extra={"extra_fields": {"body": response.text[:200]}},
            )
            raise LLMUnavailableError()

        if response.status_code >= 400:
            logger.error(
                "llm_request_failed",
                extra={"extra_fields": {"status": response.status_code, "body": response.text[:300]}},
            )
            raise LLMUnavailableError()

        return response.json()

    raise LLMUnavailableError()
