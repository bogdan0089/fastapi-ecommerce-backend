from fastapi import APIRouter
from schemas.schemas import ProductsCreate, ProductUpdate, ResponseProduct
from services.product_service import ProductService


router_product = APIRouter(prefix="/product")


@router_product.post("/", response_model=ResponseProduct)
async def create_product(data: ProductsCreate):
    return await ProductService.create_product(data)

@router_product.get("/all")
async def get_all_products(limit: int = 10, offset: int = 0):
    return await ProductService.get_products(limit, offset)

@router_product.get("/search")
async def search_products(name: str):
    return await ProductService.search_products(name)

@router_product.get("/filter")
async def filter_products(min_price: float = None, max_price: float = None):
    return await ProductService.filter_by_price(min_price, max_price)

@router_product.get("/{product_id}", response_model=ResponseProduct)
async def get_product(product_id: int):
    return await ProductService.get_product(product_id)

@router_product.put("/{product_id}", response_model=ResponseProduct)
async def update_product(product_id: int, data: ProductUpdate):
    return await ProductService.update_product(product_id, data)

@router_product.delete("/{product_id}", response_model=ResponseProduct)
async def delete_product(product_id: int):
    return await ProductService.delete_product(product_id)