from fastapi import APIRouter
from services.category_service import CategoryService
from schemas.category_schema import CategoryCreate, ResponseCategory
from utils.dependencies import CurrentAdmin


router_category = APIRouter(prefix="/category")


@router_category.post("/create", response_model=ResponseCategory)
async def create_category(data: CategoryCreate, _: CurrentAdmin):
    return await CategoryService.create_category(data)


@router_category.get("/admin", response_model=list[ResponseCategory])
async def get_all_category(limit: int = 15, offset: int = 0):
    return await CategoryService.get_all_category(limit, offset)


