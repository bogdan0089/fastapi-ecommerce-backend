from database.unit_of_work import UnitOfWork
from schemas.category_schema import CategoryCreate
from models.models import Category
from core.redis import redis_client
import json


class CategoryService:


    @staticmethod
    async def create_category(data: CategoryCreate) -> Category:
        async with UnitOfWork() as uow:
            category = await uow.category.create_category(data)
            keys = await redis_client.keys("categories*")
            if keys:
                await redis_client.delete(*keys)
            return category


    @staticmethod
    async def get_all_category(limit, offset) -> list[Category]:
        async with UnitOfWork() as uow:
            cached_key = f"categories:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            categories = await uow.category.get_all_category(limit, offset)
            if not categories:
                return []
            await redis_client.set(
                cached_key,
                json.dumps([{
                    "id": c.id,
                    "name": c.name
                } for c in categories]),
                ex=60,
            )
            return categories