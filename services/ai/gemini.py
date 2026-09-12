from typing import Any

from core.config import settings
from core.exceptions import LLMUnavailableError
from services.ai.transport import post_json
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Thinking is switched off. Every task here is grounded - pick ids out of a
# catalogue we handed the model, or write two sentences from data we handed it -
# so reasoning adds nothing to the answer. It costs plenty: gemini-3.5-flash
# spent ~490 of a 512 token budget thinking and then had nothing left to answer
# with, so search returned JSON cut off mid-array and chat a sentence cut in
# half. Measured with it off: 1.3s instead of 3.6s, and complete answers.
THINKING_BUDGET = 0
TRUNCATED = "MAX_TOKENS"


def _to_gemini_schema(schema: Any) -> Any:
    """Translate ordinary JSON Schema into the dialect Gemini accepts.

    Gemini spells its type names in upper case and nobody else does, so the
    schema in `prompts` stays vendor-neutral and this payload adapts.
    """
    if isinstance(schema, dict):
        return {
            key: value.upper()
            if key == "type" and isinstance(value, str)
            else _to_gemini_schema(value)
            for key, value in schema.items()
        }
    if isinstance(schema, list):
        return [_to_gemini_schema(item) for item in schema]
    return schema


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
            "thinkingConfig": {"thinkingBudget": THINKING_BUDGET},
        }
        if json_schema is not None:
            generation["responseMimeType"] = "application/json"
            generation["responseSchema"] = _to_gemini_schema(json_schema)
        return {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": generation,
        }

    @staticmethod
    def _read_text(body: dict[str, Any]) -> str:
        candidates = body.get("candidates") or []
        if not candidates:
            logger.error("llm_no_candidates")
            raise LLMUnavailableError()

        candidate = candidates[0]

        # A truncated answer is worse than none: prose arrives cut mid-sentence
        # and JSON arrives unparsable, which reads as a mangled reply rather than
        # a failure. Refuse it here so the cause is named in the log.
        if candidate.get("finishReason") == TRUNCATED:
            logger.error(
                "llm_answer_truncated",
                extra={"extra_fields": {"usage": body.get("usageMetadata", {})}},
            )
            raise LLMUnavailableError()

        # A thinking part carries reasoning, not the answer. Joining it in would
        # corrupt a JSON reply and pad a prose one.
        parts = candidate.get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
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
            logger.error("llm_key_missing")
            raise LLMUnavailableError()

        body = await post_json(
            f"{BASE_URL}/{self._model}:generateContent",
            self._payload(system, user, json_schema),
            {"x-goog-api-key": self._api_key},
            self._timeout,
        )
        return self._read_text(body)
