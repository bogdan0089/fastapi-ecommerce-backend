from fastapi import FastAPI, APIRouter
from schemas.schemas import ProductsCreate, ProductsRead
from services.product_service import ProductService


app = FastAPI()

router_product = APIRouter(prefix="/product")


@router_product.post("/create_product", response_model=ProductsRead)
async def create_product(data: ProductsCreate):
    return await ProductService.create_product(data)


@router_product.get("/products/{product_id}")
async def get_products(product_id: int):
    return await ProductService.get_product(product_id)

@router_product.get("/products/{product_id}/orders")
async def get_product_orders(product_id: int):
    return await ProductService.get_product(product_id)





