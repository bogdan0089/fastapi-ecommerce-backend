from collections.abc import Sequence

from sqlalchemy import Row, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from core.enum import ProductStatus
from models.models import Product
from schemas.product.input_dto import ProductCreateDTO, ProductUpdateDTO


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_product(self, data: ProductCreateDTO) -> Product:
        product = Product(
            **data.model_dump()
        )
        self.session.add(product)
        await self.session.flush()
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product.id)
            .options(selectinload(Product.category))
        )
        return result.scalars().first()

    async def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """Take stock only if there is enough, in a single statement.

        Reading the quantity and then writing it lets two concurrent checkouts
        both pass the check and drive stock negative. The WHERE clause makes
        the database do the comparison, so exactly one of them updates a row.
        """
        statement = (
            update(Product)
            .where(Product.id == product_id, Product.quantity >= quantity)
            .values(quantity=Product.quantity - quantity)
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def increase_stock(self, product_id: int, quantity: int) -> None:
        statement = (
            update(Product)
            .where(Product.id == product_id)
            .values(quantity=Product.quantity + quantity)
        )
        await self.session.execute(statement)

    async def get_product(self, product_id: int) -> Product | None:
        stmt = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
            .where(Product.status == ProductStatus.accept)
        )
        return stmt.scalars().first()
    
    async def get_product_any_status(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
        )
        return result.scalars().first()

    async def get_products(self, limit: int, offset: int) -> Sequence[Product]:
        result = await self.session.execute(
            select(Product)
            .where(Product.status == ProductStatus.accept)
            .options(selectinload(Product.category))
            .order_by(Product.id)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    async def get_catalogue(self, limit: int) -> Sequence[Row]:
        """The four columns a prompt needs, as rows rather than ORM objects.

        Nothing here is ever returned to a client, so loading whole products
        and their categories would buy a second query and a hundred identity-map
        entries for text that is thrown away after the request.
        """
        result = await self.session.execute(
            select(Product.id, Product.name, Product.price, Product.description)
            .where(Product.status == ProductStatus.accept)
            .order_by(Product.id)
            .limit(limit)
        )
        return result.all()

    @staticmethod
    def _catalogue_conditions(name: str | None, category_id: int | None) -> list:
        conditions = [Product.status == ProductStatus.accept]
        if name:
            conditions.append(Product.name.ilike(f"%{name}%"))
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        return conditions

    @staticmethod
    def _price_conditions(min_price: float | None, max_price: float | None) -> list:
        conditions = []
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        return conditions

    async def browse(
        self,
        *,
        name: str | None,
        category_id: int | None,
        min_price: float | None,
        max_price: float | None,
        limit: int,
        offset: int,
    ) -> Sequence[Product]:
        """One page of the catalogue, filtered by everything the shop screen offers."""
        conditions = self._catalogue_conditions(name, category_id)
        conditions += self._price_conditions(min_price, max_price)
        result = await self.session.execute(
            select(Product)
            .where(*conditions)
            .options(joinedload(Product.category))
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def browse_summary(
        self,
        *,
        name: str | None,
        category_id: int | None,
        min_price: float | None,
        max_price: float | None,
    ) -> Row:
        """How many products match, and the dearest one the filters allow.

        Both in one trip. The count honours the price filter so paging is right;
        the ceiling ignores it, so dragging the price slider cannot move the end
        of its own track.
        """
        price = self._price_conditions(min_price, max_price)
        total = func.count().filter(*price) if price else func.count()
        result = await self.session.execute(
            select(total, func.max(Product.price)).where(
                *self._catalogue_conditions(name, category_id)
            )
        )
        return result.one()

    async def get_products_any_status(self, limit: int, offset: int) -> list[Product] | None:
        result = await self.session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.id)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def update_product(self, product: Product, data: ProductUpdateDTO) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        self.session.add(product)
        await self.session.flush()
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product.id)
            .options(selectinload(Product.category))
        )
        return result.scalars().first()
    
    async def update_product_status(self, product: Product, status: ProductStatus) -> Product:
        product.status = status
        self.session.add(product)
        await self.session.flush()
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product.id)
            .options(selectinload(Product.category))
        )
        return result.scalars().first()

    async def delete_product(self, product: Product) -> Product:
        await self.session.delete(product)
        return product

    async def search_by_name(self, name: str, limit: int, offset: int) -> Sequence[Product]:
        stmt = await self.session.execute(
            select(Product)
            .where(Product.name.ilike(f"%{name}%"))
            .where(Product.status == ProductStatus.accept)
            .options(selectinload(Product.category))
            .order_by(Product.id)
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
        stmt = stmt.options(selectinload(Product.category)).order_by(Product.id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_color(self, product_color: str, limit: int, offset: int) -> Sequence[Product]:
        stmt = await self.session.execute(
            select(Product)
            .where(Product.color == product_color) 
            .where(Product.status == ProductStatus.accept)
            .options(selectinload(Product.category))
            .order_by(Product.id)
            .limit(limit).offset(offset)
        )
        return stmt.scalars().all()
