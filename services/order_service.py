import json
from typing import Any
from core.enum import OrderStatus, TransactionType, ProductStatus, Role
from core.exceptions import (
    ClientNotFoundError,
    InsufficientPermissionsError,
    NotEnoughMoneyError,
    OrderAlready,
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    OrderUpdateError,
    OrdersNotFound,
    ProductAlready,
    ProductNotFound,
    ProductNotApprovedError
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client, Order
from schemas.order_schema import OrderCreate
from schemas.transaction_schema import CreateTransaction
from utils.connection_manager import connection


class OrderService:

    @staticmethod
    async def create_order(title: str, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            return await uow.order.create_order(OrderCreate(title=title, client_id=current_client.id))

    @staticmethod
    async def get_orders(limit, offset) -> list[Order] | list[dict]:
        async with UnitOfWork() as uow:
            cached_key = f"orders:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            orders = await uow.order.get_orders(limit=limit, offset=offset)
            if not orders:
                raise OrdersNotFound()
            await redis_client.set(
                cached_key,
                json.dumps([
                    {"id": o.id, "title": o.title, "client_id": o.client_id, "status": o.status.value}
                    for o in orders
                ]),
                ex=60,
            )
            return orders

    @staticmethod
    async def get_order(order_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            return order

    @staticmethod
    async def order_update(order_id: int, current_client: Client, title: str) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderUpdateError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            from schemas.order_schema import OrderUpdateRequest
            return await uow.order.orders_update(order, OrderUpdateRequest(title=title))

    @staticmethod
    async def add_product_to_order(order_id: int, product_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            if product.status != ProductStatus.accept:
                raise ProductNotApprovedError(product.id)
            if product in order.products:
                raise ProductAlready()
            order.products.append(product)
            return order

    @staticmethod
    async def order_client_sum(order_id: int, current_client: Client) -> dict[str, Any]:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order_selectionload(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            total_price = sum(p.price for p in order.products)
            return {"order_id": order.id, "total_price": total_price}

    @staticmethod
    async def update_order_status(order_id: int, status: OrderStatus, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            return await uow.order.update_order_status(order, status)

    @staticmethod
    async def cancel_order(order_id: int, current_client: Client) -> None:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            client = await uow.client.get_client(order.client_id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            if order.status == OrderStatus.cancelled:
                raise OrderCannotBeCancelledError(order_id)
            if order.status == OrderStatus.completed:
                amount = sum(p.price for p in order.products)
                client.balance += amount
                await uow.transaction.create_transaction(CreateTransaction(
                    amount=amount,
                    type=TransactionType.refund,
                    description="Order refund",
                    client_fk=client.id,
                ))
            order.status = OrderStatus.cancelled

    @staticmethod
    async def create_order_client(
        client_id: int, product_id: int, title: str, current_client: Client
    ) -> Order:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            if product.status != ProductStatus.accept:
                raise ProductNotApprovedError(product_id)
            order = await uow.order.create_order(OrderCreate(title=title, client_id=client_id))
            order.products.append(product)
            return order

    @staticmethod
    async def delete_product_from_order(order_id: int, product_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            if product not in order.products:
                raise ProductNotFound(product_id)
            order.products.remove(product)
            return order

    @staticmethod
    async def get_order_with_products(order_id: int, current_client: Client) -> dict[str, Any]:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order_selectionload(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            return {"order_with_products": order}

    @staticmethod
    async def checkout(order_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id and current_client.role != Role.superadmin:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role=current_client.role.value
                )
            if order.status == OrderStatus.completed:
                raise OrderAlready()
            client = await uow.client.get_client(order.client_id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            amount = sum(p.price for p in order.products)
            if client.balance < amount:
                raise NotEnoughMoneyError(order.client_id)
            client.balance -= amount
            await uow.transaction.create_transaction(CreateTransaction(
                amount=amount,
                type=TransactionType.purchase,
                description="Order checkout",
                client_fk=client.id,
            ))
            order.status = OrderStatus.completed
            await connection.broadcast(f"New order {order_id} checked out by client {current_client.id}")
            return order

    @staticmethod
    async def get_my_orders(current_client: Client, limit, offset) -> list[Order]:
        async with UnitOfWork() as uow:
            orders = await uow.order.get_by_client_id(current_client.id, limit, offset)
            if not orders:
                raise OrdersNotFound()
            return orders
