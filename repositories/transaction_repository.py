from models.models import Transaction
from schemas.schemas import CreateTransaction
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    
    async def create_transaction(self, data: CreateTransaction) -> Transaction:
        transaction = Transaction(
            amount=data.amount,
            type=data.type,
            description=data.description,
            client_fk=data.client_fk
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction
    
    async def get_transaction(self, transaction_id: int) -> Transaction:
        stmt = await self.session.execute(
            select(Transaction)
            .where(Transaction.id == transaction_id)
        )
        return stmt.scalars().first()

    async def get_client_transactions(self, client_id: int, limit: int = 10, offset: int = 0):
        stmt = await self.session.execute(
            select(Transaction)
            .where(Transaction.client_fk == client_id)
            .limit(limit)
            .offset(offset)
        )
        return stmt.scalars().all()
    
    

    

    


    
        