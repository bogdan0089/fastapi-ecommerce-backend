from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.enum import OrderStatus
from models.models import Order
from schemas.order_schema import OrderCreate


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def create_order(self, data: OrderCreate) -> Order:
        order = Order(title=data.title, client_id=data.client_id)
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

    async def get_by_client_id(self, client_id: int) -> Sequence[Order]:
        result = await self.session.execute(select(Order).where(Order.client_id == client_id))
        return result.scalars().all()

    async def orders_update(self, order: Order, title: str) -> Order:
        order.title = title
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
