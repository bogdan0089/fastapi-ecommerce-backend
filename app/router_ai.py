from fastapi import APIRouter, Query

from schemas.product.input_dto import AiChatDTO, ProductGenerateDescriptionDTO
from schemas.product.output_dto import ProductOutputDTO
from services.ai.ai_service import AiService
from utils.dependencies import CurrentAdmin, CurrentClient, RateLimit

router_ai = APIRouter(prefix="/ai", tags=["AI"])


@router_ai.get("/search", response_model=list[ProductOutputDTO])
async def ai_search(
    _rate: RateLimit,
    _client: CurrentClient,
    query: str = Query(min_length=2, max_length=200),
) -> list:
    return await AiService.search(query)

@router_ai.get("/recommendations")
async def get_client_recommendations(_: RateLimit, current_client: CurrentClient) -> str:
    return await AiService.recommendations(current_client.id)

@router_ai.post("/chat")
async def chat(_rate: RateLimit, current_client: CurrentClient, data: AiChatDTO) -> str:
    return await AiService.chat(data.message, current_client.id)

@router_ai.post("/generate-description")
async def product_generate_description(
    _rate: RateLimit, _admin: CurrentAdmin, data: ProductGenerateDescriptionDTO
) -> str:
    return await AiService.describe(data.product_name)
