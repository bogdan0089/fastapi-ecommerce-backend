from sqlalchemy.ext.asyncio import AsyncSession
from database.database import async_session_maker
from repositories.client_repository import ClientRepository
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from repositories.transaction_repository import TransactionRepository


class UnitOfWork:
    def __init__(self) -> None:
        self.session: AsyncSession | None = None
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()
        self.client = ClientRepository(self.session)
        self.order = OrderRepository(self.session)
        self.product = ProductRepository(self.session)
        self.transaction = TransactionRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
