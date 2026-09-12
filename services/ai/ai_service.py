import hashlib
import json

from core.config import settings
from core.exceptions import LLMUnavailableError
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Product
from services.ai import prompts
from services.ai.provider import LLMProvider, build_provider
from utils import cache
from utils.logger import get_logger

logger = get_logger(__name__)

CATALOGUE_LIMIT = 100
NAMESPACE = "ai"


def _default_provider() -> LLMProvider:
    return build_provider()


async def _cached(suffix: str, produce) -> str:
    """Answer from Redis when we can; the free tier is 20 requests per model."""
    redis_key = await cache.key(NAMESPACE, suffix)
    hit = await redis_client.get(redis_key)
    if hit:
        return hit if isinstance(hit, str) else hit.decode()
    value = await produce()
    await redis_client.set(redis_key, value, ex=settings.LLM_CACHE_TTL_SECONDS)
    return value


def _digest(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]


def _block(products) -> str:
    """Render the prompt's catalogue from products or from plain rows."""
    return prompts.catalogue_block(
        [(p.id, p.name, float(p.price), p.description) for p in products]
    )


def _parse_ids(raw: str) -> list[int]:
    """Read the id list out of a search answer, or refuse the answer."""
    try:
        ids = json.loads(raw).get("ids", [])
    except (json.JSONDecodeError, AttributeError):
        logger.error("llm_search_unparsable", extra={"extra_fields": {"raw": raw[:200]}})
        raise LLMUnavailableError() from None
    return [i for i in ids if isinstance(i, int)]


class AiService:

    @staticmethod
    async def _catalogue() -> list[Product]:
        async with UnitOfWork() as uow:
            products = await uow.product.get_products(limit=CATALOGUE_LIMIT, offset=0)
            return list(products)

    @staticmethod
    async def search(query: str, provider: LLMProvider | None = None) -> list[Product]:
        """Return the products a shopper meant, not a sentence about them."""
        provider = provider or _default_provider()
        products = await AiService._catalogue()
        if not products:
            return []

        catalogue = _block(products)

        # Parsing inside ask() keeps a malformed answer out of the cache: it
        # raises before _cached stores anything, so one bad reply costs a
        # retry rather than an hour of the same error.
        async def ask() -> str:
            raw = await provider.complete(
                system=prompts.SEARCH,
                user=f"Catalogue:\n{catalogue}\n\nRequest: {query}",
                json_schema=prompts.SEARCH_SCHEMA,
            )
            return json.dumps({"ids": _parse_ids(raw)})

        # Stamped with the catalogue's version: adding or editing a product
        # bumps it, so a new arrival is searchable at once instead of after the
        # hour it would otherwise spend behind a cached answer.
        answer = await _cached(f"search:{provider.name}:c{await cache.version('product')}:{_digest(query)}", ask)
        ids = json.loads(answer)["ids"]

        # Only ids that exist are kept, so a hallucinated id cannot reach a shopper.
        by_id = {p.id: p for p in products}
        return [by_id[i] for i in ids if i in by_id]

    @staticmethod
    async def chat(message: str, client_id: int, provider: LLMProvider | None = None) -> str:
        """Answer about this store, using this catalogue and this client's orders."""
        provider = provider or _default_provider()

        async with UnitOfWork() as uow:
            rows = await uow.product.get_catalogue(limit=CATALOGUE_LIMIT)
            bought = await uow.client.purchased_product_names(client_id)

        history = ", ".join(bought) or "nothing yet"
        return await provider.complete(
            system=prompts.CHAT,
            user=(
                f"Catalogue:\n{_block(rows)}\n\n"
                f"This shopper has bought: {history}\n\nQuestion: {message}"
            ),
        )

    @staticmethod
    async def describe(product_name: str, provider: LLMProvider | None = None) -> str:
        provider = provider or _default_provider()

        async def ask() -> str:
            return await provider.complete(
                system=prompts.DESCRIPTION,
                user=f"Product: {product_name}",
            )

        return await _cached(f"describe:{provider.name}:{_digest(product_name)}", ask)

    @staticmethod
    async def recommendations(client_id: int, provider: LLMProvider | None = None) -> str:
        provider = provider or _default_provider()

        # The client is already proven to exist: get_current_client loaded them
        # and raised before the router ever reached this service.
        async with UnitOfWork() as uow:
            bought = await uow.client.purchased_product_names(client_id)
            if not bought:
                return "No purchase history yet. Buy something and recommendations will appear here."
            rows = await uow.product.get_catalogue(limit=CATALOGUE_LIMIT)

        catalogue = _block(rows)
        history = ", ".join(bought)

        async def ask() -> str:
            return await provider.complete(
                system=prompts.RECOMMENDATIONS,
                user=f"Catalogue:\n{catalogue}\n\nAlready bought: {history}",
            )

        return await _cached(
            f"recs:{provider.name}:c{await cache.version('product')}:{client_id}:{_digest(history)}", ask
        )
