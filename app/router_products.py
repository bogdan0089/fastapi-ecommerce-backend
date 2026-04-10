from fastapi import APIRouter
from schemas.product_schema import ProductCreate, ProductUpdate, ResponseProduct
from services.product_service import ProductService
from utils.dependencies import CurrentClient


router_product = APIRouter(prefix="/product")


@router_product.post("/", response_model=ResponseProduct)
async def create_product(data: ProductCreate, _: CurrentClient) -> ResponseProduct:
    return await ProductService.create_product(data)

@router_product.get("/all", response_model=list[ResponseProduct])
async def get_all_products(limit: int = 10, offset: int = 0) -> list:
    return await ProductService.get_products(limit, offset)

@router_product.get("/search", response_model=list[ResponseProduct])
async def search_products(name: str) -> list:
    return await ProductService.search_products(name)

@router_product.get("/filter", response_model=list[ResponseProduct])
async def filter_products(
    min_price: float | None = None, max_price: float | None = None
) -> list:
    return await ProductService.filter_by_price(min_price, max_price)

@router_product.get("/{product_id}", response_model=ResponseProduct)
async def get_product(product_id: int) -> ResponseProduct:
    return await ProductService.get_product(product_id)

@router_product.put("/{product_id}", response_model=ResponseProduct)
async def update_product(
    product_id: int, data: ProductUpdate, _: CurrentClient
) -> ResponseProduct:
    return await ProductService.update_product(product_id, data)

@router_product.delete("/{product_id}", response_model=ResponseProduct)
async def delete_product(product_id: int, _: CurrentClient) -> ResponseProduct:
    return await ProductService.delete_product(product_id)
