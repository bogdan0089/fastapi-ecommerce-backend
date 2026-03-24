from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Product
from schemas.schemas import ProductsCreate



class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_product(self, data: ProductsCreate) -> Product:
        db_products = Product(
            name=data.name
        )
        self.session.add(db_products)
        return db_products

    async def get_product(self, product_id: int) -> Product:
        return await self.session.get(Product, product_id)
    

