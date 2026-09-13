from pydantic import TypeAdapter
from sqlalchemy.exc import IntegrityError

from core.exceptions import CategoryAlreadyExistsError, CategoryNotFoundError
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Category
from schemas.category.input_dto import CategoryCreateDTO
from schemas.category.output_dto import CategoryOutputDTO
from utils import cache
from utils.logger import get_logger

logger = get_logger(__name__)

_category_list_adapter = TypeAdapter(list[CategoryOutputDTO])

class CategoryService:

    @staticmethod
    async def create_category(data: CategoryCreateDTO) -> Category:
        try:
            async with UnitOfWork() as uow:
                category = await uow.category.create_category(data)
        except IntegrityError as exc:
            raise CategoryAlreadyExistsError(data.name) from exc
        await cache.invalidate("category")
        logger.info("category_created", extra={"extra_fields": {"category_id": category.id, "name": data.name}})
        return category

    @staticmethod
    async def get_all_category(limit, offset) -> list[CategoryOutputDTO]:
        cached_key = await cache.key("category", f"list:limit={limit}:offset={offset}")
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
                logger.warning("category_not_found", extra={"extra_fields": {"category_id": category_id}})
                raise CategoryNotFoundError(category_id)
            await uow.category.delete_category(category)
        await cache.invalidate("category")
        logger.info("category_deleted", extra={"extra_fields": {"category_id": category_id}})

