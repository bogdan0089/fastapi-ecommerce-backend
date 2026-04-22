import json
from core.exceptions import ProductNotFound
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
    async def get_products(limit, offset) -> list[Product] | list[dict]:
        async with UnitOfWork() as uow:
            cached_key = f"products:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            products = await uow.product.get_products(limit, offset)
            if not products:
                return []
            await redis_client.set(
                cached_key,
                json.dumps([{
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "color": p.color,
                    "status": p.status.value,
                    "image_url": p.image_url
                } for p in products]),
                ex=60,
            )
            return products

    @staticmethod
    async def get_products_any_status(limit: int, offset: int) -> list[Product] | None:
        async with UnitOfWork() as uow:
            cached_key = f"products_admin:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            products = await uow.product.get_products_any_status(limit, offset)
            if not products:
                return []
            await redis_client.set(
                cached_key,
                json.dumps([{
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "color": p.color,
                    "status": p.status.value,
                    "image_url": p.image_url
                } for p in products]),
                ex=60
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
            product = await uow.product.get_product_any_status(product_id)
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
            product = await uow.product.get_product_any_status(product_id)
            if not product:
                raise ProductNotFound(product_id)
            deleted = await uow.product.delete_product(product)
        keys = await redis_client.keys("products:*")
        if keys:
            await redis_client.delete(*keys)
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

