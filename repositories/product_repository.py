from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Product
from schemas.product_schema import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_product(self, data: ProductCreate) -> Product:
        product = Product(name=data.name, price=data.price)
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_product(self, product_id: int) -> Product | None:
        return await self.session.get(Product, product_id)

    async def get_products(self, limit: int, offset: int) -> Sequence[Product]:
        result = await self.session.execute(select(Product).limit(limit).offset(offset))
        return result.scalars().all()

    async def update_product(self, product: Product, data: ProductUpdate) -> Product:
        if data.name is not None:
            product.name = data.name
        if data.price is not None:
            product.price = data.price
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete_product(self, product: Product) -> Product:
        await self.session.delete(product)
        return product

    async def search_by_name(self, name: str) -> Sequence[Product]:
        result = await self.session.execute(
            select(Product).where(Product.name.ilike(f"%{name}%"))
        )
        return result.scalars().all()

    async def filter_by_price(
        self, min_price: float | None = None, max_price: float | None = None
    ) -> Sequence[Product]:
        stmt = select(Product)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        result = await self.session.execute(stmt)
        return result.scalars().all()
