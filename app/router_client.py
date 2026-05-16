from fastapi import APIRouter
from schemas.client.input_dto import ClientUpdateDTO, ClientBalanceOperationDTO
from schemas.client.output_dto import ClientOutputDTO, ClientOrdersCountDTO
from schemas.order.output_dto import OrderOutputDTO
from services.client_service import ClientService
from services.order_service import OrderService
from utils.dependencies import CurrentClient, CurrentAdmin


router_client = APIRouter(prefix="/client")


@router_client.get("/me", response_model=ClientOutputDTO)
async def get_me(current_client: CurrentClient) -> ClientOutputDTO:
    return current_client

@router_client.get("/me/stats")
async def get_my_stats(current_client: CurrentClient) -> dict:
    return await ClientService.get_client_stats(current_client)

@router_client.get("/me/orders", response_model=list[OrderOutputDTO])
async def get_my_orders(current_client: CurrentClient, limit: int = 10, offset: int = 0) -> list:
    return await OrderService.get_my_orders(current_client, limit, offset)

@router_client.post("/{client_id}/deposit", response_model=ClientOutputDTO)
async def client_deposit(
    client_id: int, deposit: ClientBalanceOperationDTO, current_client: CurrentClient
) -> ClientOutputDTO:
    return await ClientService.client_deposit(client_id, deposit.amount, current_client)

@router_client.post("/{client_id}/withdraw", response_model=ClientOutputDTO)
async def client_withdraw(
    client_id: int, withdraw: ClientBalanceOperationDTO, current_client: CurrentClient
) -> ClientOutputDTO:
    return await ClientService.client_withdraw(client_id, withdraw.amount, current_client)

@router_client.get("/get_clients", response_model=list[ClientOutputDTO])
async def get_clients(_: CurrentAdmin, limit: int = 10, offset: int = 0) -> list:
    return await ClientService.get_all_client(limit, offset)

@router_client.get("/{client_id}", response_model=ClientOutputDTO)
async def get_client(client_id: int, current_client: CurrentClient) -> ClientOutputDTO:
    return await ClientService.get_client(client_id, current_client)

@router_client.put("/{client_id}", response_model=ClientOutputDTO)
async def client_update(
    client_id: int, data: ClientUpdateDTO, current_client: CurrentClient
) -> ClientOutputDTO:
    return await ClientService.client_update(client_id, data, current_client)

@router_client.delete("/{client_id}", response_model=ClientOutputDTO)
async def client_delete(client_id: int, current_client: CurrentClient) -> ClientOutputDTO:
    return await ClientService.client_delete(client_id, current_client)

@router_client.get("/{client_id}/orders/count", response_model=ClientOrdersCountDTO)
async def client_orders_count(client_id: int, current_client: CurrentClient) -> ClientOrdersCountDTO:
    return await ClientService.get_client_order_count(client_id, current_client)
