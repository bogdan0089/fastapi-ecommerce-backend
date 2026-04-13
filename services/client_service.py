import json
from typing import Any
from core.exceptions import (
    ClientDeleteError,
    ClientNotFoundError,
    ClientsNotFoundError,
    InsufficientPermissionsError,
    InvalidAmountError,
    NotEnoughMoneyError,
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client
from schemas.client_schema import ClientCreate, ClientUpdate
from schemas.order_schema import OrderCreate
from utils.hash import hash_password
from core.enum import Role, OrderStatus


class ClientService:

    @staticmethod
    async def create_client(data: ClientCreate) -> Client:
        async with UnitOfWork() as uow:
            hashed = hash_password(data.password)
            client = await uow.client.create_client(data, hashed)
            order_data = OrderCreate(
                title=f"Order for client {client.id}",
                client_id=client.id,
            )
            await uow.order.create_order(order_data)
        keys = await redis_client.keys("clients:*")
        if keys:
            await redis_client.delete(*keys)
        return client

    @staticmethod
    async def get_all_client(limit: int = 10, offset: int = 0) -> list[Client] | list[dict]:
        async with UnitOfWork() as uow:
            cached_key = f"clients:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            clients = await uow.client.get_all_clients(limit, offset)
            if not clients:
                raise ClientsNotFoundError()
            await redis_client.set(
                cached_key,
                json.dumps([
                    {"email": c.email, "name": c.name, "age": c.age, "balance": c.balance, "id": c.id}
                    for c in clients
                ]),
                ex=60,
            )
            return clients

    @staticmethod
    async def get_client(client_id: int, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            return client

    @staticmethod
    async def client_update(client_id: int, data: ClientUpdate, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            updated = await uow.client.client_update(client, data)
        keys = await redis_client.keys("clients:*")
        if keys:
            await redis_client.delete(*keys)
        return updated

    @staticmethod
    async def client_delete(client_id: int, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            orders = await uow.order.get_by_client_id(client_id)
            if orders:
                raise ClientDeleteError(
                    client_id,
                    reason=f"Client has {len(orders)} active order(s). Remove them first.",
                )
            await uow.client.client_delete(client)
        keys = await redis_client.keys("clients:*")
        if keys:
            await redis_client.delete(*keys)
        return client

    @staticmethod
    async def get_client_order_count(client_id: int, current_client: Client) -> dict[str, Any]:
        async with UnitOfWork() as uow:
            client = await uow.client.client_with_orders(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            return {"client_id": client.id, "orders_count": len(client.orders)}

    @staticmethod
    async def get_client_stats(current_client: Client) -> dict[str, Any]:
        async with UnitOfWork() as uow:
            cached = await redis_client.get(f"client:stats:{current_client.id}")
            if cached:
                return json.loads(cached)
            client = await uow.client.client_with_orders(current_client.id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            total_orders = len(client.orders)
            total_spent = sum(
                sum(p.price for p in order.products)
                for order in client.orders
                if order.status.value == OrderStatus.completed
            )
            stats = {
                "client_id": client.id,
                "total_orders": total_orders,
                "total_spent": total_spent,
                "balance": client.balance,
            }
            await redis_client.set(f"client:stats:{current_client.id}", json.dumps(stats), ex=60)
            return stats

    @staticmethod
    async def client_deposit(client_id: int, amount: float, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            if amount <= 0:
                raise InvalidAmountError(amount)
            return await uow.client.deposit_client(client, amount)

    @staticmethod
    async def client_withdraw(client_id: int, amount: float, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            if amount <= 0:
                raise InvalidAmountError(amount)
            if amount > client.balance:
                raise NotEnoughMoneyError(client_id)
            return await uow.client.withdraw_client(client, amount)
