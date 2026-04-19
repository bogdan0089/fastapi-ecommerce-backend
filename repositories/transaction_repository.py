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
            **data.model_dump()
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
        self, client_id: int, limit, offset
    ) -> Sequence[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.client_fk == client_id)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
