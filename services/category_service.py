from database.unit_of_work import UnitOfWork
from schemas.category_schema import CategoryCreate, ResponseCategory
from models.models import Category
from core.redis import redis_client
from pydantic import TypeAdapter
from core.exceptions import CategoryNotFoundError


_category_list_adapter = TypeAdapter(list[ResponseCategory])

class CategoryService:


    @staticmethod
    async def create_category(data: CategoryCreate) -> Category:
        async with UnitOfWork() as uow:
            category = await uow.category.create_category(data)
        async for key in redis_client.scan_iter("category*"):
            await redis_client.unlink(key)
        return category


    @staticmethod
    async def get_all_category(limit, offset) -> list[ResponseCategory]:
        cached_key = f"categories:limit={limit}:offset={offset}"
        cached = await redis_client.get(cached_key)
        if cached:
            return _category_list_adapter.validate_json(cached)
        async with UnitOfWork() as uow:
            categories = await uow.category.get_all_category(limit, offset)
            if not categories:
                return []
            validated = _category_list_adapter.validate_python(categories)
        await redis_client.set(
            cached_key, _category_list_adapter.dump_json(validated),
            ex=60
        )
        return validated

    @staticmethod
    async def delete_category(category_id: int) -> None:
        async with UnitOfWork() as uow:
            category = await uow.category.get_category(category_id)
            if not category:
                raise CategoryNotFoundError(category_id)
            await uow.category.delete_category(category)
        async for key in redis_client.scan_iter("category*"):
            await redis_client.unlink(key)