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
    ProductNotApprovedError,
    InvalidOrderTransitionError,
    OutOfStockError
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client, Order
from schemas.order_schema import OrderCreate, ResponseOrder, OrderUpdateRequest
from schemas.transaction_schema import CreateTransaction
from utils.connection_manager import connection
from celery_app import send_order_status_email
from pydantic import TypeAdapter


_orders_list_adapter = TypeAdapter(list[ResponseOrder])

class OrderService:

    @staticmethod
    async def create_order(title: str, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.create_order(OrderCreate(title=title, client_id=current_client.id))
        async for key in redis_client.scan_iter("order*"):
            await redis_client.unlink(key)
        return order

    @staticmethod
    async def get_orders(limit, offset) -> list[ResponseOrder]:
        cached_key = f"orders:limit={limit}:offset={offset}"
        cached = await redis_client.get(cached_key)
        if cached:
            return _orders_list_adapter.validate_json(cached)
        async with UnitOfWork() as uow:
            orders = await uow.order.get_orders(limit=limit, offset=offset)
            if not orders:
                raise OrdersNotFound()
            validated = _orders_list_adapter.validate_python(orders)
        await redis_client.set(
            cached_key, _orders_list_adapter.dump_json(validated),
            ex=60,
            )
        return validated 

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
            updated = await uow.order.orders_update(order, OrderUpdateRequest(title=title))
        async for key in redis_client.scan_iter("order*"):
            await redis_client.unlink(key)
        return updated

    @staticmethod
    async def add_product_to_order(order_id: int, product_id: int, quantity: int, current_client: Client) -> Order:
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
            if any(op.product_id == product_id for op in order.order_products):
                raise ProductAlready()
            await uow.order.add_product_to_order(order_id, product_id, quantity)
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
            total_price = sum(op.product.price * op.quantity for op in order.order_products)
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
            allowed_transitions = {
                OrderStatus.create: [OrderStatus.completed, OrderStatus.cancelled],
                OrderStatus.completed: [OrderStatus.cancelled],
                OrderStatus.cancelled: []
            }
            if status not in allowed_transitions[order.status]:
                raise InvalidOrderTransitionError(order.status, status)
            client = await uow.client.get_client(order.client_id)
            send_order_status_email.delay(client.email, order_id, status.value)
            updated = await uow.order.update_order_status(order, status)
        async for key in redis_client.scan_iter("order*"):
            await redis_client.unlink(key)
        return updated

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
            client = await uow.client.get_client_with_lock(order.client_id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            if order.status == OrderStatus.cancelled:
                raise OrderCannotBeCancelledError(order_id)
            if order.status == OrderStatus.completed:
                amount = sum(op.product.price * op.quantity for op in order.order_products)
                client.balance += amount
                await uow.transaction.create_transaction(CreateTransaction(
                    amount=amount,
                    type=TransactionType.refund,
                    description="Order refund",
                    client_fk=client.id,
                ))
            order.status = OrderStatus.cancelled
        async for key in redis_client.scan_iter("order*"):
            await redis_client.unlink(key)
        return order

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
            await uow.order.add_product_to_order(order.id, product.id, 1)
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
            if not any(op.product_id == product_id for op in order.order_products):
                raise ProductNotFound(product_id)
            await uow.order.remove_product_from_order(order_id, product_id)
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
            client = await uow.client.get_client_with_lock(order.client_id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            amount = sum(op.product.price * op.quantity for op in order.order_products)
            for op in order.order_products:
                if op.product.quantity < op.quantity:
                    raise OutOfStockError(op.product_id)
            if client.balance < amount:
                raise NotEnoughMoneyError(order.client_id)
            client.balance -= amount
            for op in order.order_products:
                op.product.quantity -= op.quantity
            await uow.transaction.create_transaction(CreateTransaction(
                amount=amount,
                type=TransactionType.purchase,
                description="Order checkout",
                client_fk=client.id,
            ))
            order.status = OrderStatus.completed
            await connection.broadcast(f"New order {order_id} checked out by client {current_client.id}")
        async for key in redis_client.scan_iter("order*"):
            await redis_client.unlink(key)
        return order

    @staticmethod
    async def get_my_orders(current_client: Client, limit, offset) -> list[Order]:
        async with UnitOfWork() as uow:
            orders = await uow.order.get_by_client_id(current_client.id, limit, offset)
            if not orders:
                return []
            return orders
