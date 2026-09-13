from decimal import Decimal
from typing import Any

from pydantic import TypeAdapter

from celery_app import send_new_order_notification, send_order_status_email
from core.config import settings
from core.enum import OrderStatus, ProductStatus, Role, TransactionType
from core.exceptions import (
    ClientNotFoundError,
    InsufficientPermissionsError,
    InvalidAmountError,
    InvalidOrderTransitionError,
    NotEnoughMoneyError,
    OrderAlready,
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    OrderUpdateError,
    OutOfStockError,
    ProductAlready,
    ProductNotApprovedError,
    ProductNotFound,
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client, Order
from schemas.order.input_dto import OrderCreateInternalDTO, OrderUpdateDTO
from schemas.order.output_dto import OrderOutputDTO
from schemas.transaction.input_dto import TransactionCreateDTO
from utils import cache
from utils.connection_manager import connection
from utils.logger import get_logger

logger = get_logger(__name__)

_orders_list_adapter = TypeAdapter(list[OrderOutputDTO])

class OrderService:

    @staticmethod
    def _refund_amount(order: Order) -> Decimal:
        """Sum of what the client actually paid, line by line.

        Orders placed before price_at_purchase existed fall back to the current
        price, which is the old behaviour and can differ from what was charged.
        """
        total = Decimal("0.00")
        for op in order.order_products:
            price = op.price_at_purchase
            if price is None:
                logger.warning(
                    "refund_without_purchase_price",
                    extra={
                        "extra_fields": {
                            "order_id": order.id,
                            "product_id": op.product_id,
                        }
                    },
                )
                price = op.product.price
            total += price * op.quantity
        return total

    @staticmethod
    async def create_order(title: str, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.create_order(OrderCreateInternalDTO(title=title, client_id=current_client.id))
        await cache.invalidate("order")
        logger.info("order_created", extra={"extra_fields": {"order_id": order.id, "client_id": current_client.id}})
        return order

    @staticmethod
    async def get_orders(limit, offset) -> list[OrderOutputDTO]:
        cached_key = await cache.key("order", f"list:limit={limit}:offset={offset}")
        cached = await redis_client.get(cached_key)
        if cached:
            return _orders_list_adapter.validate_json(cached)
        async with UnitOfWork() as uow:
            orders = await uow.order.get_orders(limit=limit, offset=offset)
            if not orders:
                return []
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
                logger.warning("order_not_found", extra={"extra_fields": {"order_id": order_id}})
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
            updated = await uow.order.orders_update(order, OrderUpdateDTO(title=title))
        await cache.invalidate("order")
        logger.info("order_updated", extra={"extra_fields": {"order_id": order_id}})
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
            if quantity < 1:
                raise InvalidAmountError(quantity)
            if product.quantity < quantity:
                raise OutOfStockError(product_id)
            if any(op.product_id == product_id for op in order.order_products):
                raise ProductAlready()
            await uow.order.add_product_to_order(order_id, product_id, quantity)
            logger.info(
                "product_added_to_order",
                extra={"extra_fields": {"order_id": order_id, "product_id": product_id}},
            )
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
            if not client:
                raise ClientNotFoundError(order.client_id)
            recipient = client.email
            updated = await uow.order.update_order_status(order, status)
        send_order_status_email.delay(recipient, order_id, status.value)
        await cache.invalidate("order")
        logger.info("order_status_updated", extra={"extra_fields": {"order_id": order_id, "status": status.value}})
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
                amount = OrderService._refund_amount(order)
                client.balance += amount
                for op in order.order_products:
                    await uow.product.increase_stock(op.product_id, op.quantity)
                await uow.transaction.create_transaction(TransactionCreateDTO(
                    amount=amount,
                    type=TransactionType.refund,
                    description="Order refund",
                    client_fk=client.id,
                ))
            order.status = OrderStatus.cancelled
        await cache.invalidate("order")
        logger.info("order_cancelled", extra={"extra_fields": {"order_id": order_id, "client_id": current_client.id}})
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
            order = await uow.order.create_order(OrderCreateInternalDTO(title=title, client_id=client_id))
            await uow.order.add_product_to_order(order.id, product.id, 1)
        logger.info(
            "order_created_with_product",
            extra={
                "extra_fields": {
                    "order_id": order.id,
                    "client_id": client_id,
                    "product_id": product_id,
                }
            },
        )
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
        logger.info(
            "product_removed_from_order",
            extra={"extra_fields": {"order_id": order_id, "product_id": product_id}},
        )
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
            if client.balance < amount:
                raise NotEnoughMoneyError(order.client_id)
            client.balance -= amount

            for op in sorted(order.order_products, key=lambda line: line.product_id):
                if not await uow.product.decrease_stock(op.product_id, op.quantity):
                    raise OutOfStockError(op.product_id)
                op.price_at_purchase = op.product.price
            await uow.transaction.create_transaction(TransactionCreateDTO(
                amount=amount,
                type=TransactionType.purchase,
                description="Order checkout",
                client_fk=client.id,
            ))
            order.status = OrderStatus.completed

        send_order_status_email.delay(
            to_email=current_client.email,
            order_id=order.id,
            status=OrderStatus.completed.value
        )
        send_new_order_notification.delay(
            admin_email=settings.EMAIL_USER,
            order_id=order.id,
            client_email=current_client.email,
            amount=float(amount)
        )
        await connection.broadcast(
            f"New order {order_id} checked out by client {current_client.id}"
        )
        await cache.invalidate("order")
        logger.info(
            "order_checkout",
            extra={
                "extra_fields": {
                    "order_id": order_id,
                    "client_id": current_client.id,
                    "amount": amount,
                }
            },
        )
        return order

    @staticmethod
    async def get_my_orders(current_client: Client, limit, offset) -> list[Order]:
        async with UnitOfWork() as uow:
            return await uow.order.get_by_client_id(current_client.id, limit, offset)
