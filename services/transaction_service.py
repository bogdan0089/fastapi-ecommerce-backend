from core.exceptions import (
    ClientNotFoundError,
    InsufficientPermissionsError,
    TransactionNotFound,
)
from database.unit_of_work import UnitOfWork
from models.models import Client, Transaction
from schemas.transaction_schema import CreateTransaction


class TransactionService:


    @staticmethod
    async def create_transaction(data: CreateTransaction) -> Transaction:
        async with UnitOfWork() as uow:
            return await uow.transaction.create_transaction(data)

    @staticmethod
    async def get_transaction(transaction_id: int, current_client: Client) -> Transaction:
        async with UnitOfWork() as uow:
            transaction = await uow.transaction.get_transaction(transaction_id)
            if not transaction:
                raise TransactionNotFound()
            if transaction.client_fk != current_client.id:
                raise InsufficientPermissionsError(required_role="owner", client_role="client")
            return transaction

    @staticmethod
    async def client_all_transactions(client_id: int, current_client: Client) -> list[Transaction]:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if client is None:
                raise ClientNotFoundError(client_id)
            if client.id != current_client.id:
                raise InsufficientPermissionsError(required_role="owner", client_role="client")
            return await uow.transaction.get_all_client_transactions(client_id)

    @staticmethod
    async def get_my_transactions(
        current_client: Client, limit: int = 10, offset: int = 0
    ) -> list[Transaction]:
        async with UnitOfWork() as uow:
            return await uow.transaction.get_client_transactions(current_client.id, limit, offset)
