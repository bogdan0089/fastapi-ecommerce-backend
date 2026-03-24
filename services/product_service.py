from schemas.schemas import ProductsCreate
from models.models import Product, Client
from fastapi import HTTPException, status
from database.unit_of_work import UnitOfWork
from core.exceptions import ProductNotFound

class ProductService:



    @staticmethod
    async def create_product(data: ProductsCreate) -> Product:
        async with UnitOfWork() as uow:
            return await uow.product.create_product(data)

    @staticmethod
    async def get_product(product_id: int) -> Product:
        async with UnitOfWork() as uow:
            products = await uow.product.get_product(product_id)
            if not products:
                raise ProductNotFound(product_id)
            return products
        




