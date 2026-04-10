from fastapi import APIRouter
from schemas.transaction_schema import CreateTransaction, ResponseTransaction
from services.transaction_service import TransactionService
from utils.dependencies import CurrentClient


router_transaction = APIRouter(prefix="/transaction")


@router_transaction.post("/create_transaction", response_model=ResponseTransaction)
async def create_transaction(transaction: CreateTransaction, _: CurrentClient) -> ResponseTransaction:
    return await TransactionService.create_transaction(data=transaction)

@router_transaction.get("/me/transactions", response_model=list[ResponseTransaction])
async def get_my_transactions(
    current_client: CurrentClient, limit: int = 10, offset: int = 0
) -> list:
    return await TransactionService.get_my_transactions(current_client, limit, offset)

@router_transaction.get("/{transaction_id}", response_model=ResponseTransaction)
async def get_transaction(
    transaction_id: int, current_client: CurrentClient
) -> ResponseTransaction:
    return await TransactionService.get_transaction(transaction_id, current_client)

@router_transaction.get("/{client_id}/transactions", response_model=list[ResponseTransaction])
async def client_all_transactions(
    client_id: int, current_client: CurrentClient
) -> list:
    return await TransactionService.client_all_transactions(client_id, current_client)
