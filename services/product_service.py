from core.exceptions import ProductNotFound
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Product
from schemas.product.input_dto import ProductCreateDTO, ProductUpdateDTO
from schemas.product.output_dto import ProductOutputDTO
from core.enum import ProductStatus
from pydantic import TypeAdapter


_product_list_adapter = TypeAdapter(list[ProductOutputDTO])

class ProductService:

    @staticmethod
    async def create_product(data: ProductCreateDTO) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.create_product(data)
        async for key in redis_client.scan_iter("product*"):
            await redis_client.unlink(key)
        return product

    @staticmethod
    async def get_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            return product

    @staticmethod
    async def get_products(limit, offset) -> list[ProductOutputDTO]:
        async with UnitOfWork() as uow:
            cached_key = f"products:limit={limit}:offset={offset}"
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
    async def get_products_any_status(limit: int, offset: int) -> list[ProductOutputDTO]:
        async with UnitOfWork() as uow:
            cached_key = f"products_admin:limit={limit}:offset={offset}"
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
        async for key in redis_client.scan_iter("product*"):
            await redis_client.unlink(key)
        return updated

    @staticmethod
    async def update_product_status(product_id: int, status: ProductStatus) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product_any_status(product_id)
            if not product:
                raise ProductNotFound(product_id)
            updated = await uow.product.update_product_status(product, status)
        async for key in redis_client.scan_iter("product*"):
            await redis_client.unlink(key)
        return updated

    @staticmethod
    async def delete_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product_any_status(product_id)
            if not product:
                raise ProductNotFound(product_id)
            deleted = await uow.product.delete_product(product)
        async for key in redis_client.scan_iter("product*"):
            await redis_client.unlink(key)
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

