import json
from decimal import Decimal
from typing import Any

from pydantic import TypeAdapter

from core.enum import OrderStatus, Role, TransactionType
from core.exceptions import (
    ClientNotFoundError,
    ClientsNotFoundError,
    InsufficientPermissionsError,
    InvalidAmountError,
    NotEnoughMoneyError,
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client
from schemas.client.input_dto import ClientUpdateDTO
from schemas.client.output_dto import ClientOutputDTO
from schemas.transaction.input_dto import TransactionCreateDTO
from utils import cache
from utils.logger import get_logger

logger = get_logger(__name__)

_client_list_adapter = TypeAdapter(list[ClientOutputDTO])

class ClientService:

    @staticmethod
    async def get_all_client(limit, offset) -> list[ClientOutputDTO]:
        cached_key = await cache.key("client", f"list:limit={limit}:offset={offset}")
        cached = await redis_client.get(cached_key)
        if cached:
            return _client_list_adapter.validate_json(cached)
        async with UnitOfWork() as uow:
            clients = await uow.client.get_all_clients(limit, offset)
            if not clients:
                raise ClientsNotFoundError()
            validated = _client_list_adapter.validate_python(clients)
        await redis_client.set(
            cached_key, _client_list_adapter.dump_json(validated),
            ex=60
        )
        return validated

    @staticmethod
    async def get_client(client_id: int, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                logger.warning("client_not_found", extra={"extra_fields": {"client_id": client_id}})
                raise ClientNotFoundError(client_id)
            if current_client.id != client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            return client

    @staticmethod
    async def client_update(client_id: int, data: ClientUpdateDTO, current_client: Client) -> Client:
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
        await cache.invalidate("client")
        logger.info("client_updated", extra={"extra_fields": {"client_id": client_id}})
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
            await uow.client.client_delete(client)
        await cache.invalidate("client")
        logger.info("client_deleted", extra={"extra_fields": {"client_id": client_id}})
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
        stats_key = await cache.key("client", f"stats:{current_client.id}")
        cached = await redis_client.get(stats_key)
        if cached:
            return json.loads(cached)
        async with UnitOfWork() as uow:
            client = await uow.client.client_with_orders(current_client.id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            total_orders = len(client.orders)
            total_spent = sum(
                sum(op.product.price * op.quantity for op in order.order_products)
                for order in client.orders
                if order.status == OrderStatus.completed
            )
            stats = {
                "client_id": client.id,
                "total_orders": total_orders,
                "total_spent": float(total_spent),
                "balance": float(client.balance),
            }
        await redis_client.set(stats_key, json.dumps(stats), ex=60)
        return stats

    @staticmethod
    async def client_deposit(client_id: int, amount: Decimal, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_with_lock(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            if amount <= 0:
                raise InvalidAmountError(amount)
            await uow.transaction.create_transaction(TransactionCreateDTO(
                amount=amount,
                type=TransactionType.deposit,
                description="deposit",
                client_fk=client.id
            ))
            result = await uow.client.deposit_client(client, amount)
        logger.info("client_deposit", extra={"extra_fields": {"client_id": client_id, "amount": amount}})
        return result

    @staticmethod
    async def client_withdraw(client_id: int, amount: Decimal, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_with_lock(client_id)
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
            await uow.transaction.create_transaction(TransactionCreateDTO(
                amount=amount,
                type=TransactionType.withdraw,
                description="withdraw",
                client_fk=client.id
            ))
            result = await uow.client.withdraw_client(client, amount)
        logger.info("client_withdraw", extra={"extra_fields": {"client_id": client_id, "amount": amount}})
        return result
