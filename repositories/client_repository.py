from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.models import Client
from schemas.client_schema import ClientUpdate, ClientCreate
from schemas.auth_schema import ChangeRole


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_client(
            self,
            data: ClientCreate,
            hashed: str
    ) -> Client:
        client = Client(
            **data.model_dump(exclude={"password"}),
            hashed_password=hashed
        )
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def get_all_clients(self, limit: int, offset: int) -> Sequence[Client]:
        result = await self.session.execute(
            select(Client)
            .where(Client.is_active == True)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def get_client(self, client_id: int) -> Client | None:
        result = await self.session.execute(
            select(Client)
            .where(Client.id == client_id)
            .where(Client.is_active == True)
        )
        return result.scalars().first()

    async def get_client_email(self, email: str) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.email == email))
        return result.scalars().first()

    async def client_update(self, client: Client, data: ClientUpdate) -> Client:
        for field, value in data.model_dump().items():
            setattr(client, field, value)
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def client_delete(self, client: Client) -> None:
        client.is_active = False
        self.session.add(client)

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
    
    async def change_role(self, client: Client, role: ChangeRole) -> Client:
        for field, value in role.model_dump().items():
            setattr(client, field, value)
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client
