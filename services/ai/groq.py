from typing import Any

from core.config import settings
from core.exceptions import LLMUnavailableError
from services.ai.transport import post_json
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

# gpt-oss-120b is on the free plan and is one of the models that honours a JSON
# schema with strict decoding, which the search endpoint depends on. Models
# without it can only promise valid JSON, not JSON of the right shape.
DEFAULT_MODEL = "openai/gpt-oss-120b"

# The same argument as Gemini's thinking budget: these tasks are grounded, and
# reasoning tokens come out of the same allowance as the answer.
REASONING_EFFORT = "low"
TRUNCATED = "length"


class GroqProvider:
    """Talks to Groq's OpenAI-compatible chat completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.GROQ_API_KEY
        self._model = model or settings.LLM_MODEL or DEFAULT_MODEL
        self._timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self._max_output_tokens = max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS

    @property
    def name(self) -> str:
        return f"groq:{self._model}"

    def _payload(self, system: str, user: str, json_schema: dict[str, Any] | None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
            "max_completion_tokens": self._max_output_tokens,
            "reasoning_effort": REASONING_EFFORT,
        }
        if json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "answer", "strict": True, "schema": json_schema},
            }
        return payload

    @staticmethod
    def _read_text(body: dict[str, Any]) -> str:
        choices = body.get("choices") or []
        if not choices:
            logger.error("llm_no_candidates")
            raise LLMUnavailableError()

        choice = choices[0]
        if choice.get("finish_reason") == TRUNCATED:
            logger.error(
                "llm_answer_truncated",
                extra={"extra_fields": {"usage": body.get("usage", {})}},
            )
            raise LLMUnavailableError()

        text = (choice.get("message", {}).get("content") or "").strip()
        if not text:
            logger.error("llm_empty_answer")
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
            logger.error("llm_key_missing", extra={"extra_fields": {"provider": "groq"}})
            raise LLMUnavailableError()

        body = await post_json(
            BASE_URL,
            self._payload(system, user, json_schema),
            {"Authorization": f"Bearer {self._api_key}"},
            self._timeout,
        )
        return self._read_text(body)
