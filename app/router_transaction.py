from fastapi import APIRouter
from schemas.transaction.output_dto import TransactionOutputDTO
from services.transaction_service import TransactionService
from utils.dependencies import CurrentClient


router_transaction = APIRouter(prefix="/transaction")


@router_transaction.get("/me/transactions", response_model=list[TransactionOutputDTO])
async def get_my_transactions(
    current_client: CurrentClient, limit: int = 10, offset: int = 0
) -> list:
    return await TransactionService.get_my_transactions(current_client, limit, offset)

@router_transaction.get("/{transaction_id}", response_model=TransactionOutputDTO)
async def get_transaction(
    transaction_id: int, current_client: CurrentClient
) -> TransactionOutputDTO:
    return await TransactionService.get_transaction(transaction_id, current_client)

@router_transaction.get("/{client_id}/transactions", response_model=list[TransactionOutputDTO])
async def client_all_transactions(
    client_id: int, current_client: CurrentClient, limit: int = 10, offset: int = 0
) -> list:
    return await TransactionService.client_all_transactions(client_id, current_client, limit, offset)
