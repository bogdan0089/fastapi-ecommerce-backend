from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Review
from schemas.review.input_dto import ReviewCreate


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_review(self, data: ReviewCreate, client_id: int) -> Review:
        create_review = Review(
            **data.model_dump(),
            client_id=client_id
        )
        self.session.add(create_review)
        await self.session.flush()
        await self.session.refresh(create_review)
        return create_review

    async def get_review(self, review_id: int) -> Review:
        result = await self.session.execute(
            select(Review)
            .where(Review.id == review_id)
        )
        return result.scalars().first()

    async def get_reviews(self, limit, offset):
        result = await self.session.execute(
            select(Review)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    async def get_reviews_by_product_id(self, product_id: int) -> list[Review]:
        result = await self.session.execute(
            select(Review)
            .where(Review.product_id == product_id)
        )
        return result.scalars().all()
    
    async def delete_review(self, review: Review) -> None:
        await self.session.delete(review)



    
