from fastapi import APIRouter

from schemas.review.input_dto import ReviewCreate
from schemas.review.output_dto import ReviewResponse
from services.review_service import ReviewService
from utils.dependencies import CurrentClient

router_review = APIRouter(prefix="/review", tags=["Review"])


@router_review.post("/", response_model=ReviewResponse)
async def create_review(current_client: CurrentClient, data: ReviewCreate) -> ReviewResponse:
    return await ReviewService.create_review(data, current_client.id)

@router_review.get("/product/{product_id}", response_model=list[ReviewResponse])
async def get_review_by_product_id(product_id: int) -> list[ReviewResponse]:
    return await ReviewService.get_reviews_by_product_id(product_id)

@router_review.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int) -> ReviewResponse:
    return await ReviewService.get_review(review_id)

@router_review.delete("/{review_id}", status_code=204)
async def review_delete(review_id: int) -> None:
    await ReviewService.delete_review(review_id)
