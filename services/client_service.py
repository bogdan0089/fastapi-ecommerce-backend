from schemas.schemas import ClientCreate, ClientUpdate, OrderCreate
from models.models import Client
from typing import List
from database.unit_of_work import UnitOfWork
from core.exceptions import (
    ClientAlreadyError,
    ClientDeleteError,
    ClientTransactionNotFound,
    ClientNotFoundError,
    ClientsNotFoundError,
    ClientUpdateError,
    InsufficientPermissionsError,
    InvalidAmountError,
    NotEnoughMoneyError
)
from utils.hash import hash_password


class ClientService:


    @staticmethod
    async def create_client(data: ClientCreate) -> Client:
        async with UnitOfWork() as uow:

            hashed = hash_password(data.password)
            client = await uow.client.create_client(
                name=data.name,
                age=data.age,
                balance=data.balance,
                hashed_password=hashed,
                email=data.email
            )
            order_data = OrderCreate(
                title=f" Order for -> {client.id}",
                client_id=client.id
            )
            await uow.order.create_order(order_data)
            return client
    
    @staticmethod
    async def get_all_client() -> List[Client]:
        async with UnitOfWork() as uow:
            client = await uow.client.get_all_clients()
            if not client:
                raise ClientsNotFoundError()
            return client

    @staticmethod
    async def get_client(client_id: int, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client.id:
                raise InsufficientPermissionsError(
                    required_role="Owner",
                    client_role="client"
                )
            return client
    
    @staticmethod
    async def client_update(client_id: int, data: ClientUpdate, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id:
                raise InsufficientPermissionsError(
                    required_role="Owner",
                    client_role="client"
                )
            client_update = await uow.client.client_update(client, data)
            return client_update

    @staticmethod
    async def client_delete(client_id: int, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            orders = await uow.order.get_by_client_id(client_id)
            if orders:
                return {
                    "massage": "You can not delete client with active order!",
                    "count_order": len(orders)
                }
            if current_client.id != client_id:
                raise InsufficientPermissionsError(
                    required_role="Owner",
                    client_role="client"
                )
            if not orders:
                await uow.client.client_delete(client)
                return client

    @staticmethod
    async def get_client_order_count(client_id: int, current_client: Client) -> dict:
        async with UnitOfWork() as uow:
            client = await uow.client.client_with_orders(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if current_client.id != client_id:
                raise InsufficientPermissionsError(
                    required_role="Owner or admin!",
                    client_role="client"
                )
            total_order = len(client.orders)
            return {
                "client_id": client.id,
                "orders_count": total_order
            }
        
    @staticmethod
    async def get_client_stats(current_client: Client) -> dict:
        async with UnitOfWork() as uow:
            client = await uow.client.client_with_orders(current_client.id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            total_orders = len(client.orders)
            total_spent = sum(
                sum(p.price for p in order.products)
                for order in client.orders
                if order.status.value == "completed"
            )
            return {
                "client_id": client.id,
                "total_orders": total_orders,
                "total_spent": total_spent,
                "balance": client.balance
            }

    @staticmethod
    async def client_deposit(client_id: int, amount: float, current_client: Client) -> Client:
        async with UnitOfWork() as uow:
                client = await uow.client.get_client(client_id)
                if not client:
                    raise ClientNotFoundError(client_id)
                if amount <= 0:
                    raise InvalidAmountError(amount)
                if current_client.id != client_id:
                    raise InsufficientPermissionsError(
                        required_role="Only owner",
                        client_role="client"
                    )
                client_deposit = await uow.client.deposit_client(client, amount)
                return client_deposit
    
    @staticmethod
    async def client_withdraw(client_id: int, amount: float, current_client: Client) -> Client:
        async with UnitOfWork() as uow:        
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            if amount > client.balance:
                raise NotEnoughMoneyError(client_id)
            if amount <= 0:
                raise InvalidAmountError(amount)
            if current_client.id != client_id:
                raise InsufficientPermissionsError(
                    required_role="Owner",
                    client_role="client"
                )
            client_withdraw = await uow.client.withdraw_client(client, amount)
            return client_withdraw
        

        




    

