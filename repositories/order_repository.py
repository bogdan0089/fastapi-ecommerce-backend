from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.enum import OrderStatus
from models.models import Order, OrderProduct
from schemas.order.input_dto import OrderCreateInternalDTO, OrderUpdateDTO


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_order(self, data: OrderCreateInternalDTO) -> Order:
        order = Order(
            **data.model_dump()
        )
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def get_order(self, order_id: int) -> Order | None:
        return await self.session.get(Order, order_id)

    async def get_order_selectionload(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).options(selectinload(Order.products)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_orders(self, limit: int, offset: int) -> Sequence[Order]:
        result = await self.session.execute(select(Order).limit(limit).offset(offset))
        return result.scalars().all()

    async def get_by_client_id(self, client_id: int, limit, offset) -> Sequence[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.client_id == client_id)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def orders_update(self, order: Order, data: OrderUpdateDTO) -> Order:
        for field, value in data.model_dump().items():
            setattr(order, field, value)
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def update_order_status(self, order: Order, status: OrderStatus) -> Order:
        order.status = status
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def add_product_to_order(self, order_id: int, product_id: int, quantity: int) -> None:
        item = OrderProduct(order_id=order_id, product_id=product_id, quantity=quantity)
        self.session.add(item)

    async def remove_product_from_order(self, order_id: int, product_id: int) -> None:
        result = await self.session.execute(
            select(OrderProduct).where(
                OrderProduct.order_id == order_id,
                OrderProduct.product_id == product_id
            )
        )
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)