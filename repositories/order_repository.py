from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Order, OrderStatus
from schemas.schemas import OrderCreate
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List



class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_order(self, data: OrderCreate) -> Order:
        db_order = Order(
            title=data.title,
            client_id=data.client_id
        )
        self.session.add(db_order)
        await self.session.flush()
        await self.session.refresh(db_order)
        return db_order
    
    async def get_order_selectionload(self, order_id: int) -> Order:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.products))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_order(self, order_id: int) -> Order:
        return await self.session.get(Order, order_id)
    
    async def orders_update(self, order: Order, title: str) -> Order:
        order.title = title
        self.session.add(order)
        return order

    async def get_orders(self, limit, offset) -> Order:
        db_order = await self.session.execute(
            select(Order).limit(limit).offset(offset)
        )
        return db_order.scalars().all()
    
    async def update_order_status(self, order, status: str) -> Order:
        order.status = OrderStatus(status)
        self.session.add(order)
        await self.session.refresh(order)
        return order

    async def create_order_for_client_id(self, client_id: int, title: str) -> Order:
        order = Order(
            client_id=client_id,
            title=title,
            status=OrderStatus.create
        )
        self.session.add(order)
        await self.session.flush()
        return order
    
    async def get_by_client_id(self, client_id: int) -> List[Order]:
        result = await self.session.execute(select(Order).where(Order.client_id == client_id))
        return result.scalars().all()
    
