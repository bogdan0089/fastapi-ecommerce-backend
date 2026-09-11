from pydantic import TypeAdapter

from core.enum import ProductStatus
from core.exceptions import ProductNotFound
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Product
from schemas.product.input_dto import ProductCreateDTO, ProductUpdateDTO
from schemas.product.output_dto import ProductOutputDTO, ProductPageDTO
from utils import cache
from utils.logger import get_logger

logger = get_logger(__name__)

_product_list_adapter = TypeAdapter(list[ProductOutputDTO])

class ProductService:

    @staticmethod
    async def create_product(data: ProductCreateDTO) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.create_product(data)
        await cache.invalidate("product")
        logger.info("product_created", extra={"extra_fields": {"product_id": product.id}})
        return product

    @staticmethod
    async def get_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                logger.warning("product_not_found", extra={"extra_fields": {"product_id": product_id}})
                raise ProductNotFound(product_id)
            return product

    @staticmethod
    async def get_products(limit, offset) -> list[ProductOutputDTO]:
        async with UnitOfWork() as uow:
            cached_key = await cache.key("product", f"list:limit={limit}:offset={offset}")
            cached = await redis_client.get(cached_key)
            if cached:
                return _product_list_adapter.validate_json(cached)
            products = await uow.product.get_products(limit, offset)
            if not products:
                return []
            validated = _product_list_adapter.validate_python(products)
            await redis_client.set(
                cached_key, _product_list_adapter.dump_json(validated),
                ex=60
            )
            return validated

    @staticmethod
    async def browse(
        name: str | None,
        category_id: int | None,
        min_price: float | None,
        max_price: float | None,
        limit: int,
        offset: int,
    ) -> ProductPageDTO:
        """One filtered page of the catalogue, with its total and price ceiling."""
        suffix = (
            f"browse:name={name or ''}:cat={category_id or ''}"
            f":min={min_price or ''}:max={max_price or ''}:limit={limit}:offset={offset}"
        )
        cached_key = await cache.key("product", suffix)
        cached = await redis_client.get(cached_key)
        if cached:
            return ProductPageDTO.model_validate_json(cached)

        async with UnitOfWork() as uow:
            products = await uow.product.browse(
                name=name,
                category_id=category_id,
                min_price=min_price,
                max_price=max_price,
                limit=limit,
                offset=offset,
            )
            total, ceiling = await uow.product.browse_summary(
                name=name, category_id=category_id,
                min_price=min_price, max_price=max_price,
            )

        page = ProductPageDTO(
            items=_product_list_adapter.validate_python(products),
            total=total,
            price_ceiling=float(ceiling) if ceiling is not None else 0.0,
        )
        await redis_client.set(cached_key, page.model_dump_json(), ex=60)
        return page

    @staticmethod
    async def get_products_any_status(limit: int, offset: int) -> list[ProductOutputDTO]:
        async with UnitOfWork() as uow:
            cached_key = await cache.key("product", f"admin:limit={limit}:offset={offset}")
            cached = await redis_client.get(cached_key)
            if cached:
                return _product_list_adapter.validate_json(cached)
            products = await uow.product.get_products_any_status(limit, offset)
            if not products:
                return []
            validated = _product_list_adapter.validate_python(products)
            await redis_client.set(
                cached_key, _product_list_adapter.dump_json(validated),
                ex=60
            )
            return validated

    @staticmethod
    async def update_product(product_id: int, data: ProductUpdateDTO) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            updated = await uow.product.update_product(product, data)
        await cache.invalidate("product")
        logger.info("product_updated", extra={"extra_fields": {"product_id": product_id}})
        return updated

    @staticmethod
    async def update_product_status(product_id: int, status: ProductStatus) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product_any_status(product_id)
            if not product:
                raise ProductNotFound(product_id)
            updated = await uow.product.update_product_status(product, status)
        await cache.invalidate("product")
        logger.info(
            "product_status_updated",
            extra={"extra_fields": {"product_id": product_id, "status": status.value}},
        )
        return updated

    @staticmethod
    async def delete_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product_any_status(product_id)
            if not product:
                raise ProductNotFound(product_id)
            deleted = await uow.product.delete_product(product)
        await cache.invalidate("product")
        logger.info("product_deleted", extra={"extra_fields": {"product_id": product_id}})
        return deleted

    @staticmethod
    async def search_products(name: str, limit, offset) -> list[Product]:
        async with UnitOfWork() as uow:
            products = await uow.product.search_by_name(name, limit, offset)
            return products or []

    @staticmethod
    async def filter_by_price(
        limit, offset, min_price: float | None = None, max_price: float | None = None
    ) -> list[Product]:
        async with UnitOfWork() as uow:
            products = await uow.product.filter_by_price(min_price, max_price, limit, offset)
            return products or []

    @staticmethod
    async def find_by_color(product_color: str, limit, offset) -> list[Product]:
        async with UnitOfWork() as uow:
            products = await uow.product.find_by_color(product_color, limit, offset)
            return products or []

