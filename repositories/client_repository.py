from sqlalchemy.ext.asyncio import AsyncSession
from models.models  import Client
from schemas.schemas import ClientCreate
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List


class ClientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_client(self, name: str, age: int, balance: float, hashed_password: str, email: str) -> Client:
        db_client = Client(
            name=name,
            age=age,
            balance=balance,
            hashed_password=hashed_password,
            email=email
        )
        self.session.add(db_client)
        await self.session.flush()
        return db_client

    async def get_all_clients(self, limit, offset) -> List[Client]:
        client = await self.session.execute(
            select(Client).limit(limit).offset(offset)
        )
        return client.scalars().all()

    async def get_client(self, client_id: int) -> Client:
        db_client = await self.session.get(Client, client_id,)
        return db_client

    async def client_update(self, client: Client, data: ClientCreate) -> Client: 
        client.name = data.name
        client.age = data.age
        self.session.add(client)
        return client

    async def get_client_email(self, email: str) -> Client:
        client_email = await self.session.execute(
            select(Client)
            .where(Client.email == email)
        )
        return client_email.scalars().first()
    
    async def client_delete(self, client: Client) -> Client:
        delete_client = await self.session.delete(client)
        return delete_client
        
    async def client_with_orders(self, client_id: int) -> Client:
        result = await self.session.execute(
            select(Client)
            .options(joinedload(Client.orders))
            .where(Client.id == client_id)
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






        
        