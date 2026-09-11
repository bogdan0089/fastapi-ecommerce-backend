from typing import Any, Protocol


class LLMProvider(Protocol):
    """What the rest of the app is allowed to ask of a language model.

    Business logic depends on this and never on a vendor. Swapping Gemini for
    something else, or for a stub in tests, means providing another class with
    this method — no service is touched.
    """

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
