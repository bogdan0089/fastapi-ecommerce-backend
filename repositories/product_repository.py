from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Product
from schemas.product_schema import ProductCreate, ProductUpdate
from core.enum import ProductStatus


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_product(self, data: ProductCreate) -> Product:
        product = Product(
            **data.model_dump()
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_product(self, product_id: int) -> Product | None:
        stmt = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .where(Product.status == ProductStatus.accept)
        )
        return stmt.scalars().first()

    async def get_products(self, limit: int, offset: int) -> Sequence[Product]:
        result = await self.session.execute(
            select(Product)
            .where(Product.status == ProductStatus.accept)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def update_product(self, product: Product, data: ProductUpdate) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product
    
    async def update_product_status(self, product: Product, status: ProductStatus) -> Product:
        product.status = status
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete_product(self, product: Product) -> Product:
        await self.session.delete(product)
        return product

    async def search_by_name(self, name: str, limit: int, offset: int) -> Sequence[Product]:
        stmt = await self.session.execute(
            select(Product)
            .where(Product.name.ilike(f"%{name}%"))
            .where(Product.status == ProductStatus.accept)
            .limit(limit).offset(offset)
        )
        return stmt.scalars().all()

    async def filter_by_price(
        self, limit, offset, min_price: float | None = None, max_price: float | None = None 
    ) -> Sequence[Product]:
        stmt = select(Product).where(Product.status == ProductStatus.accept)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_color(self, product_color: str, limit: int, offset: int) -> Sequence[Product]:
        stmt = await self.session.execute(
            select(Product)
            .where(Product.color == product_color) 
            .where(Product.status == ProductStatus.accept)
            .limit(limit).offset(offset)
        )
        return stmt.scalars().all()
