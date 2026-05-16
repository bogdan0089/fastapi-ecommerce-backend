from fastapi import APIRouter
from services.category_service import CategoryService
from schemas.category.input_dto import CategoryCreateDTO
from schemas.category.output_dto import CategoryOutputDTO
from utils.dependencies import CurrentAdmin


router_category = APIRouter(prefix="/category")


@router_category.post("/create", response_model=CategoryOutputDTO)
async def create_category(data: CategoryCreateDTO, _: CurrentAdmin):
    return await CategoryService.create_category(data)

@router_category.get("/all", response_model=list[CategoryOutputDTO])
async def get_all_category(limit: int = 15, offset: int = 0) -> list[CategoryOutputDTO]:
    return await CategoryService.get_all_category(limit, offset)

@router_category.delete("/{category_id}", status_code=204)
async def delete_category(_: CurrentAdmin, category_id: int) -> None:
    await CategoryService.delete_category(category_id)



