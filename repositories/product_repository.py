from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Product
from schemas.schemas import ProductsCreate, ProductUpdate
from sqlalchemy import select
from typing import List


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_product(self, data: ProductsCreate) -> Product | None:
        db_products = Product(
            name=data.name
        )
        self.session.add(db_products)
        return db_products

    async def get_product(self, product_id: int) -> Product | None:
        result = await self.session.get(Product, product_id)
        return result
    
    async def get_products(self, limit, offset) -> List[Product] | None:
        result = await self.session.execute(
            select(Product).limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    async def update_product(self, product: Product, data: ProductUpdate) -> Product | None:
        if data.name is not None:
            product.name = data.name
        if data.price is not None:
            product.price = data.price
        self.session.add(product)
        return product


    async def delete_product(self, product: Product) -> Product | None:
        await self.session.delete(product)
        return product

    async def search_by_name(self, name: str) -> List[Product]:
        result = await self.session.execute(
            select(Product).where(Product.name.ilike(f"%{name}%"))
        )
        return result.scalars().all()

    async def filter_by_price(self, min_price: float = None, max_price: float = None) -> List[Product]:
        stmt = select(Product)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        result = await self.session.execute(stmt)
        return result.scalars().all()
