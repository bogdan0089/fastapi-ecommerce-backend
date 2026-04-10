from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.models import Client
from schemas.client_schema import ClientUpdate


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_client(
        self,
        name: str,
        age: int,
        balance: float,
        hashed_password: str,
        email: str,
    ) -> Client:
        client = Client(name=name, age=age, balance=balance, hashed_password=hashed_password, email=email)
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def get_all_clients(self, limit: int, offset: int) -> Sequence[Client]:
        result = await self.session.execute(select(Client).limit(limit).offset(offset))
        return result.scalars().all()

    async def get_client(self, client_id: int) -> Client | None:
        return await self.session.get(Client, client_id)

    async def get_client_email(self, email: str) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.email == email))
        return result.scalars().first()

    async def client_update(self, client: Client, data: ClientUpdate) -> Client:
        client.name = data.name
        client.age = data.age
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def client_delete(self, client: Client) -> None:
        await self.session.delete(client)

    async def client_with_orders(self, client_id: int) -> Client | None:
        result = await self.session.execute(
            select(Client).options(joinedload(Client.orders)).where(Client.id == client_id)
        )
        return result.scalars().first()

    async def deposit_client(self, client: Client, amount: float) -> Client:
        client.balance += amount
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def withdraw_client(self, client: Client, amount: float) -> Client:
        client.balance -= amount
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client
