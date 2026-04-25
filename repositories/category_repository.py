from schemas.category_schema import CategoryCreate, ResponseCategory
from models.models import Category
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_category(
            self,
            data:CategoryCreate
    ) -> Category:
        category = Category(
            **data.model_dump()
        )
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category


    async def get_all_category(self, limit, offset) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()