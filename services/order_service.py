from schemas.schemas import OrderCreate, CreateTransaction
from models.models import Order, Client
from database.unit_of_work import UnitOfWork
from core.enum import OrderStatus, TransactionType
from core.redis import redis_client
import json
from core.exceptions import(
OrderNotFoundError,
ClientNotFoundError, 
NotEnoughMoneyError,
OrderAlready,
OrdersNotFound,
OrderUpdateError,
InsufficientPermissionsError,
ProductAlready,
ProductNotFound
)


class OrderService:

        
    @staticmethod
    async def create_order(data: OrderCreate) -> Order:
        async with UnitOfWork() as uow:
            create_order = await uow.order.create_order(data)
            return create_order

    @staticmethod
    async def get_orders(limit: int = 10, offset: int = 0) -> list[Order]:
        async with UnitOfWork() as uow:
            cached_key = f"orders:limit={limit}:offset={offset}"
            cached = await redis_client.get(cached_key)
            if cached:
                return json.loads(cached)
            order = await uow.order.get_orders(limit=limit, offset=offset)
            if not order:
                raise OrdersNotFound()
            await redis_client.set(
                cached_key, json.dumps([{
                    "id": o.id,
                    "title": o.title,
                    "client_id": o.client_id,
                    "status": o.status.value 
                } for o in order if isinstance(o, Order)]), ex=60
            )
            return order

    @staticmethod
    async def get_order(order_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            return order
    
    @staticmethod
    async def order_update(order_id: int, title: str, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderUpdateError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            order_update = await uow.order.orders_update(order, title=title)
            return order_update
        
    @staticmethod
    async def add_product_to_order(order_id: int, product_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role="client"
                )
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            if product in order.products:
                raise ProductAlready()
            order.products.append(product)
            return order.products

    @staticmethod
    async def order_client_sum(order_id: int, current_client: Client) -> dict:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order_selectionload(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            total_price = sum(products.price for products in order.products)
            return {
                "order_id": order.id,
                "total_price": total_price
            }
        
    @staticmethod
    async def update_order_status(order_id: int, Status: str, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            update_order_status = await uow.order.update_order_status(order, Status)
            return update_order_status
    
    @staticmethod
    async def create_order_client(client_id: int, product_id: int, title: str, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            if client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            order = OrderCreate(
                title=title,
                client_id=client_id
            )
            order = await uow.order.create_order(order)
            order.products.append(product)
            return order
    
    @staticmethod
    async def delete_product_from_order(order_id: int, product_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            product = await uow.product.get_product(product_id)
            if not product:
                raise ProductNotFound(product_id)
            if product not in order.products:
                raise ProductNotFound(product_id)
            order.products.remove(product)
            return order

    @staticmethod
    async def get_order_with_products(order_id: int, current_client: Client) -> dict:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order_selectionload(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            return {"order_with_products": order}

    @staticmethod
    async def checkout(order_id: int, current_client: Client):
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner",
                    client_role="client"
                )
            if order.status == OrderStatus.completed:
                raise OrderAlready()
            client = await uow.client.get_client(current_client.id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            amount = sum(p.price for p in order.products)
            if client.balance >= amount:
                client.balance -= amount
                transaction_data = CreateTransaction(
                    amount=amount,
                    type=TransactionType.purchase,
                    description="Order checkout",
                    client_fk=client.id
                )
                await uow.transaction.create_transaction(transaction_data)
                order.status = OrderStatus.completed
            else:
                raise NotEnoughMoneyError(current_client.id)
            return order

    @staticmethod
    async def get_my_orders(current_client: Client, limit: int = 10, offset: int = 0):
        async with UnitOfWork() as uow:
            orders = await uow.order.get_by_client_id(current_client.id)
            if not orders:
                raise OrdersNotFound()
            return orders[offset:offset + limit]
                









    