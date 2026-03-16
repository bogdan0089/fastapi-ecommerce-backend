from fastapi import FastAPI, APIRouter
from schemas.schemas import ResponseTransaction, CreateTransaction
from services.transaction_service import Transaction, TransactionService


router_transaction = APIRouter(prefix="/transaction")


app = FastAPI()




@router_transaction.post("/create_transaction", response_model=ResponseTransaction)
async def create_transaction(transaction: CreateTransaction):
    return await TransactionService.create_transaction(data=transaction)


@router_transaction.get("/{transaction_id}", response_model=ResponseTransaction)
async def get_transaction(transaction_id: int):
    return await TransactionService.get_transaction(transaction_id)
