from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.models import Client, Order, OrderProduct, Product
from schemas.auth.input_dto import ChangeRoleDTO
from schemas.client.input_dto import ClientCreateDTO, ClientUpdateDTO


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_client(
            self,
            data: ClientCreateDTO,
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
            .where(Client.is_active.is_(True))
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def get_client(self, client_id: int) -> Client | None:
        result = await self.session.execute(
            select(Client)
            .where(Client.id == client_id)
            .where(Client.is_active.is_(True))
        )
        return result.scalars().first()
    
    async def get_client_with_lock(self, client_id: int) -> Client | None:
        result = await self.session.execute(
            select(Client)
            .where(Client.id == client_id)
            .where(Client.is_active.is_(True))
            .with_for_update()
        )
        return result.scalars().first()

    async def get_client_email(self, email: str) -> Client | None:
        result = await self.session.execute(
            select(Client)
            .where(Client.email == email.lower())
            .where(Client.is_active.is_(True))
        )
        return result.scalars().first()
    
    async def client_update(self, client: Client, data: ClientUpdateDTO) -> Client:
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

    async def purchased_product_names(self, client_id: int) -> list[str]:
        """Distinct names this client has bought, in one query.

        Walking client -> orders -> order_products -> product loads the whole
        purchase history into memory to end up with a handful of names, and it
        grows with every order the client ever placed.

        Ordered by name so the same history always renders the same prompt, and
        therefore lands on the same cache key.
        """
        result = await self.session.execute(
            select(Product.name)
            .join(OrderProduct, OrderProduct.product_id == Product.id)
            .join(Order, Order.id == OrderProduct.order_id)
            .where(Order.client_id == client_id)
            .distinct()
            .order_by(Product.name)
        )
        return list(result.scalars().all())

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
    
    async def change_role(self, client: Client, role: ChangeRoleDTO) -> Client:
        for field, value in role.model_dump().items():
            setattr(client, field, value)
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client
