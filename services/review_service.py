from pydantic import TypeAdapter
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    ProductNotFound,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
    ReviewsNotFoundError,
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from schemas.review.input_dto import ReviewCreate
from schemas.review.output_dto import ReviewResponse
from utils import cache
from utils.logger import get_logger

logger = get_logger(__name__)

_review_list_adapter = TypeAdapter(list[ReviewResponse])

class ReviewService:

    @staticmethod
    async def create_review(data: ReviewCreate, client_id: int) -> ReviewResponse:
        try:
            async with UnitOfWork() as uow:
                product = await uow.product.get_product(data.product_id)
                if not product:
                    raise ProductNotFound(data.product_id)
                review = await uow.review.create_review(data, client_id)
                validated = ReviewResponse.model_validate(review)
        except IntegrityError:
            raise ReviewAlreadyExistsError(data.product_id) from None
        await cache.invalidate("review")
        logger.info("review_created", extra={"extra_fields": {"review_id": validated.id, "client_id": client_id}})
        return validated

    @staticmethod
    async def get_review(review_id: int) -> ReviewResponse:
        async with UnitOfWork() as uow:
            review = await uow.review.get_review(review_id)
            if not review:
                logger.warning("review_not_found", extra={"extra_fields": {"review_id": review_id}})
                raise ReviewNotFoundError(review_id)
            return ReviewResponse.model_validate(review)

    @staticmethod
    async def get_reviews(limit: int, offset: int) -> list[ReviewResponse]:
        cached_key = await cache.key("review", f"list:limit={limit}:offset={offset}")
        cached = await redis_client.get(cached_key)
        if cached:
            return _review_list_adapter.validate_json(cached)
        async with UnitOfWork() as uow:
            reviews = await uow.review.get_reviews(limit, offset)
            if not reviews:
                raise ReviewsNotFoundError()
            validate = _review_list_adapter.validate_python(reviews)
        await redis_client.set(
            cached_key, _review_list_adapter.dump_json(validate),
            ex=60
        )
        return validate

    @staticmethod
    async def get_reviews_by_product_id(product_id: int) -> list[ReviewResponse]:
        cached_key = await cache.key("review", f"product:{product_id}")
        cached = await redis_client.get(cached_key)
        if cached:
            return _review_list_adapter.validate_json(cached)
        async with UnitOfWork() as uow:
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            reviews_by_product = await uow.review.get_reviews_by_product_id(product.id)
            if not reviews_by_product:
                raise ReviewsNotFoundError()
            validate = _review_list_adapter.validate_python(reviews_by_product)
        await redis_client.set(
            cached_key, _review_list_adapter.dump_json(validate),
            ex=60
        )
        return validate

    @staticmethod
    async def delete_review(review_id: int) -> None:
        async with UnitOfWork() as uow:
            review = await uow.review.get_review(review_id)
            if not review:
                raise ReviewNotFoundError(review_id)
            await uow.review.delete_review(review)
        await cache.invalidate("review")
        logger.info("review_deleted", extra={"extra_fields": {"review_id": review_id}})
