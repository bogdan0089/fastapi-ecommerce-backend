import json
from core.exceptions import ProductNotFound, ProductsNotFound, ProductNotApprovedError
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Product
from schemas.product_schema import ProductCreate, ProductUpdate
from core.enum import ProductStatus


class ProductService:

    @staticmethod
    async def create_product(data: ProductCreate) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.create_product(data)
        keys = await redis_client.keys("products:*")
        if keys:
            await redis_client.delete(*keys)
        return product

    @staticmethod
    async def get_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            return product

    @staticmethod
    async def get_products(limit: int = 10, offset: int = 0) -> list[Product] | list[dict]:
        async with UnitOfWork() as uow:
            cached_key = f"products:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            products = await uow.product.get_products(limit=limit, offset=offset)
            if not products:
                raise ProductsNotFound()
            await redis_client.set(
                cached_key,
                json.dumps([{"id": p.id, "name": p.name, "price": p.price} for p in products]),
                ex=60,
            )
            return products

    @staticmethod
    async def update_product(product_id: int, data: ProductUpdate) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            updated = await uow.product.update_product(product, data)
        keys = await redis_client.keys("products:*")
        if keys:
            await redis_client.delete(*keys)
        return updated

    @staticmethod
    async def update_product_status(product_id: int, status: ProductStatus) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            updated = await uow.product.update_product_status(product, status)
        keys = await redis_client.keys("products:*")
        if keys:
            await redis_client.delete(*keys)
        return updated

    @staticmethod
    async def delete_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            deleted = await uow.product.delete_product(product)
        keys = await redis_client.keys("products:*")
        if keys:
            await redis_client.delete(*keys)
        return deleted

    @staticmethod
    async def search_products(name: str) -> list[Product]:
        async with UnitOfWork() as uow:
            products = await uow.product.search_by_name(name)
            if not products:
                raise ProductsNotFound()
            return products

    @staticmethod
    async def filter_by_price(
        min_price: float | None = None, max_price: float | None = None
    ) -> list[Product]:
        async with UnitOfWork() as uow:
            products = await uow.product.filter_by_price(min_price, max_price)
            if not products:
                raise ProductsNotFound()
            return products
