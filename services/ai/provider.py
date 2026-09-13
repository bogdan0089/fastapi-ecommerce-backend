from typing import Any, Protocol

from core.config import settings
from core.exceptions import LLMUnavailableError
from services.ai.gemini import GeminiProvider
from services.ai.groq import GroqProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Protocol):
    """What the rest of the app is allowed to ask of a language model.

    Business logic depends on this and never on a vendor. Swapping one vendor
    for another, or for a stub in tests, means providing another class with
    this method — no service is touched.
    """

    @property
    def name(self) -> str:
        """Vendor and model, e.g. `groq:openai/gpt-oss-120b`.

        Cache keys carry it, so switching vendor or model stops serving the
        previous one's answers for the rest of their hour.
        """
        ...

    async def complete(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        """Answer `user` under the rules in `system`.

        `system` carries the instructions the developer wrote; `user` carries
        whatever a person typed. Keeping them apart is what stops "ignore your
        instructions" in user input from rewriting the rules.

        When `json_schema` is given the answer is valid JSON matching it, so the
        caller can parse instead of guessing at prose.
        """
        ...


PROVIDERS: dict[str, type] = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
}


def build_provider(name: str | None = None) -> LLMProvider:
    """The provider named by `LLM_PROVIDER`, or the one asked for.

    Adding a vendor means writing one class with `complete()` and listing it
    above. `LLM_MODEL` is left empty by default so each provider falls back to
    a model it is known to work with; set it only to override that.
    """
    chosen = (name or settings.LLM_PROVIDER or "").strip().lower()
    provider = PROVIDERS.get(chosen)
    if provider is None:
        logger.error(
            "llm_provider_unknown",
            extra={"extra_fields": {"asked": chosen, "known": sorted(PROVIDERS)}},
        )
        raise LLMUnavailableError()
    return provider()
