from schemas.schemas import CreateTransaction
from database.unit_of_work import UnitOfWork
from models.models import Transaction, Client
from fastapi import HTTPException, status
from typing import List
from core.exceptions import (
    ClientTransactionNotFound,
    ClientAlreadyError,
    ClientNotFoundError,
    TransactionNotFound,
    InsufficientPermissionsError
)


class TransactionService:


    @staticmethod
    async def create_transaction(data: CreateTransaction) -> Transaction:
        async with UnitOfWork() as uow:
            transaction = await uow.transaction.create_transaction(data)
            if not transaction:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
            return transaction

    @staticmethod
    async def get_transaction(transaction_id: int, current_client: Client) -> Transaction:
        async with UnitOfWork() as uow:
            transactions = await uow.transaction.get_transaction(transaction_id)
            if not transactions:
                raise TransactionNotFound()
            if transactions.client_fk != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            return transactions

    @staticmethod
    async def client_all_transactions(client_id: int, current_client: Client) -> List[Transaction]:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if client.id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            if client is None:
                raise ClientNotFoundError(client_id)
            total_transactions_client = client.transactions
            if total_transactions_client is None:
                raise ClientTransactionNotFound(client_id)
            return total_transactions_client
            
            
