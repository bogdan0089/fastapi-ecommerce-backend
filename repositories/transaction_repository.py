from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Transaction
from schemas.transaction_schema import CreateTransaction


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_transaction(self, data: CreateTransaction) -> Transaction:
        transaction = Transaction(
            amount=data.amount,
            type=data.type,
            description=data.description,
            client_fk=data.client_fk,
        )
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    async def get_transaction(self, transaction_id: int) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalars().first()

    async def get_client_transactions(
        self, client_id: int, limit: int = 10, offset: int = 0
    ) -> Sequence[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.client_fk == client_id)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_all_client_transactions(self, client_id: int) -> Sequence[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.client_fk == client_id)
        )
        return result.scalars().all()
