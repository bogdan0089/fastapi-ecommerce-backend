from fastapi import APIRouter
from schemas.product.input_dto import ProductCreateDTO, ProductUpdateDTO, ProductStatusUpdateDTO
from schemas.product.output_dto import ProductOutputDTO
from services.product_service import ProductService
from utils.dependencies import CurrentClient, CurrentAdmin, CurrentModerator


router_product = APIRouter(prefix="/product")


@router_product.post("/", response_model=ProductOutputDTO)
async def create_product(data: ProductCreateDTO, _: CurrentClient) -> ProductOutputDTO:
    return await ProductService.create_product(data)

@router_product.get("/all", response_model=list[ProductOutputDTO])
async def get_all_products(limit: int = 10, offset: int = 0) -> list:
    return await ProductService.get_products(limit, offset)

@router_product.get("/search", response_model=list[ProductOutputDTO])
async def search_products(name: str, limit: int = 25, offset: int = 0) -> list:
    return await ProductService.search_products(name, limit, offset)

@router_product.get("/filter", response_model=list[ProductOutputDTO])
async def filter_products(
    min_price: float | None = None, max_price: float | None = None,
    limit: int = 15, offset: int = 0
) -> list:
    return await ProductService.filter_by_price(min_price, max_price, limit, offset)

@router_product.get("/{product_id}", response_model=ProductOutputDTO)
async def get_product(product_id: int) -> ProductOutputDTO:
    return await ProductService.get_product(product_id)

@router_product.put("/{product_id}", response_model=ProductOutputDTO)
async def update_product(
    product_id: int, data: ProductUpdateDTO, _: CurrentAdmin
) -> ProductOutputDTO:
    return await ProductService.update_product(product_id, data)

@router_product.delete("/{product_id}", response_model=ProductOutputDTO)
async def delete_product(product_id: int, _: CurrentAdmin) -> ProductOutputDTO:
    return await ProductService.delete_product(product_id)

@router_product.patch("/{product_id}/moderate", response_model=ProductOutputDTO)
async def update_product_status(product_id: int, data: ProductStatusUpdateDTO, _: CurrentModerator) -> ProductOutputDTO:
    return await ProductService.update_product_status(product_id, data.status)

@router_product.get("/color/{product_color}", response_model=list[ProductOutputDTO])
async def find_by_color(product_color: str, limit: int = 10, offset: int = 0) -> list[ProductOutputDTO]:
    return await ProductService.find_by_color(product_color, limit, offset)

@router_product.get("/admin/all", response_model=list[ProductOutputDTO])
async def get_products_admin(_: CurrentAdmin, limit: int = 100, offset: int = 0):
    return await ProductService.get_products_any_status(limit, offset)
