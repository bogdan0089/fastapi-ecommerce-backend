from fastapi import APIRouter
from schemas.client_schema import (
    ClientCreate,
    ClientOrdersCount,
    ClientUpdate,
    OperationsRequest,
    ResponseClient,
)
from services.client_service import ClientService
from services.order_service import OrderService
from utils.dependencies import CurrentClient, CurrentAdmin


router_client = APIRouter(prefix="/client")


@router_client.get("/me", response_model=ResponseClient)
async def get_me(current_client: CurrentClient) -> ResponseClient:
    return current_client

@router_client.get("/me/stats")
async def get_my_stats(current_client: CurrentClient) -> dict:
    return await ClientService.get_client_stats(current_client)

@router_client.get("/me/orders")
async def get_my_orders(current_client: CurrentClient) -> list:
    return await OrderService.get_my_orders(current_client)

@router_client.post("/{client_id}/deposit", response_model=ResponseClient)
async def client_deposit(
    client_id: int, deposit: OperationsRequest, current_client: CurrentClient
) -> ResponseClient:
    return await ClientService.client_deposit(client_id, deposit.amount, current_client)

@router_client.post("/{client_id}/withdraw", response_model=ResponseClient)
async def client_withdraw(
    client_id: int, withdraw: OperationsRequest, current_client: CurrentClient
) -> ResponseClient:
    return await ClientService.client_withdraw(client_id, withdraw.amount, current_client)

@router_client.post("/create_client", response_model=ResponseClient)
async def create_client(client: ClientCreate) -> ResponseClient:
    return await ClientService.create_client(data=client)

@router_client.get("/get_clients", response_model=list[ResponseClient])
async def get_clients(_: CurrentAdmin, limit: int = 10, offset: int = 0) -> list:
    return await ClientService.get_all_client(limit, offset)

@router_client.get("/{client_id}", response_model=ResponseClient)
async def get_client(client_id: int, current_client: CurrentClient) -> ResponseClient:
    return await ClientService.get_client(client_id, current_client)

@router_client.put("/{client_id}", response_model=ResponseClient)
async def client_update(
    client_id: int, data: ClientUpdate, current_client: CurrentClient
) -> ResponseClient:
    return await ClientService.client_update(client_id, data, current_client)

@router_client.delete("/{client_id}", response_model=ResponseClient)
async def client_delete(client_id: int, current_client: CurrentClient) -> ResponseClient:
    return await ClientService.client_delete(client_id, current_client)

@router_client.get("/{client_id}/orders/count", response_model=ClientOrdersCount)
async def client_orders_count(client_id: int, current_client: CurrentClient) -> ClientOrdersCount:
    return await ClientService.get_client_order_count(client_id, current_client)
