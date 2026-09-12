"""Every instruction the model is given, in one place.

These are system prompts: rules written by us. Whatever a person typed goes in
the user message instead, never here — that separation is what keeps "ignore
your instructions" in a search box from rewriting the rules.

They are kept short on purpose: the free tier bills tokens in both directions.
"""

SEARCH = (
    "You match a shopper's request against a product catalogue.\n"
    "Return only ids that appear in the catalogue given to you.\n"
    "Order them best match first. If nothing fits, return an empty list.\n"
    "Never invent an id or a product."
)

CHAT = (
    "You are the assistant of a small online clothing store.\n"
    "Answer only from the catalogue and order history given to you.\n"
    "If the answer is not there, say you do not know and suggest browsing the catalogue.\n"
    "Never invent products, prices or delivery terms. Two or three sentences."
)

DESCRIPTION = (
    "You write product descriptions for an online store.\n"
    "Two or three sentences, concrete and plain. No bullet points, no hype, "
    "no invented materials, sizes or prices."
)

RECOMMENDATIONS = (
    "You suggest what a returning shopper might like next.\n"
    "Base it only on what they already bought and on the catalogue given to you.\n"
    "Name at most three products and say in one clause why each fits."
)


def catalogue_block(items: list[tuple[int, str, float, str | None]]) -> str:
    """Render the catalogue the model is allowed to answer from.

    One product per line so the model cannot confuse fields, and the id first
    so it is the easiest thing to copy back.
    """
    lines = []
    for product_id, name, price, description in items:
        line = f"{product_id} | {name} | ${price}"
        if description:
            line += f" | {description[:120]}"
        lines.append(line)
    return "\n".join(lines)


# Ordinary JSON Schema. Gemini wants its type names upper-cased; that belongs
# to the Gemini payload, not here, so every provider can read the same schema.
SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "ids": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["ids"],
}
