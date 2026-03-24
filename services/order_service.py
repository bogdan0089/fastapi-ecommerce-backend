from schemas.schemas import OrderCreate
from models.models import Order, Client
from database.unit_of_work import UnitOfWork
from core.exceptions import(
OrderNotFoundError,
ClientNotFoundError, 
OrderDeleteError,
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
    async def get_orders(limit: int = 10, offset: int = 0) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_orders(limit=limit, offset=offset)
            if not order:
                raise OrdersNotFound()
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
        
    async def add_product_to_order(self, order_id: int, product_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            product = await uow.product.get_product(product_id)
            if not product or not order:
                raise OrdersNotFound()
            if product in order.products:
                raise ProductAlready()
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or Admin",
                    client_role="client"
                )
            order.products.append(product)
            return order.products

    async def compeleted_order(self, order_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            if order is None:
                raise OrderNotFoundError(order_id)
            if order.status == "compeleted":
                raise OrderAlready()
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            order.status = "compeleted"
            return order
            
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
            # print(f"{order.products} p1")
            order.products.append(product)
            return order
    
    async def delete_product_from_order(self, order_id: int, product_id: int, current_client: Client) -> Order:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order(order_id)
            product = await uow.product.get_product(product_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if not product:
                raise ProductNotFound(product_id)
            if product not in order.products:
                raise ProductNotFound(product_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            order.products.remove(product)
            return order
            
    async def get_order_with_products(self, order_id: int, current_client: Client) -> dict:
        async with UnitOfWork() as uow:
            order = await uow.order.get_order_selectionload(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            if order.client_id != current_client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin",
                    client_role="client"
                )
            return {
                "order_with_products": order
            }
        
                






    