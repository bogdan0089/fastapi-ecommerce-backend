from fastapi import APIRouter
from services.ai_service import AiService
from utils.dependencies import CurrentClient, CurrentAdmin
from schemas.product_schema import ProductGenerateDescription, AiChat
from utils.dependencies import RateLimit


router_ai = APIRouter(prefix="/ai")


@router_ai.get("/recommendations")
async def get_client_recommendations(_: RateLimit, current_client: CurrentClient) -> str:
    return await AiService.get_client_recommendations(current_client.id)

@router_ai.post("/generate-description")
async def product_generate_description(_rate: RateLimit, _admin: CurrentAdmin, data: ProductGenerateDescription) -> str:
    return await AiService.generate_product_description(data.product_name)

@router_ai.post("/chat")
async def chat(_rate: RateLimit, _: CurrentClient, data: AiChat) -> str:
    return await AiService.chat(data.message)

@router_ai.get("/search")
async def ia_search(_rate: RateLimit, query: str, _client: CurrentClient) -> str:
    return await AiService.ai_search(query)