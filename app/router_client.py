from fastapi import APIRouter, Depends
from schemas.schemas import (
ClientCreate,
ResponseClient,
OperationsRequest,
ClientOrderdsCount,
)
from services.client_service import ClientService
from utils.dependencies import get_current_client


router_client = APIRouter(prefix="/client")


@router_client.get("/me", response_model=ResponseClient)
async def get_me(current_client=Depends(get_current_client)):
    return current_client

@router_client.get("/me/stats")
async def get_my_stats(current_client=Depends(get_current_client)):
    return await ClientService.get_client_stats(current_client)

@router_client.get("/me/orders")
async def get_my_orders(current_client=Depends(get_current_client)):
    from services.order_service import OrderService
    return await OrderService.get_my_orders(current_client)

@router_client.post("/{client_id}/deposit")
async def client_deposit(client_id: int, deposit: OperationsRequest, current_client=Depends(get_current_client)):
    result = await ClientService.client_deposit(
            client_id,
            deposit.amount,
            current_client
        )
    return result
          
@router_client.post("/{client_id}/withdraw")
async def client_withdraw(client_id: int, withdraw: OperationsRequest, current_client=Depends(get_current_client)):
    result = await ClientService.client_withdraw(
            client_id,
            withdraw.amount,
            current_client

        )
    return result

@router_client.post("/create_client", response_model=ResponseClient)
async def create_client(client: ClientCreate):
    result = await ClientService.create_client(data=client)
    return result

@router_client.get("/all_clients", response_model=list[ResponseClient])
async def get_clients(limit: int = 10, offset: int = 0):
    result = await ClientService.get_all_client(limit, offset)
    return result

@router_client.get("/{client_id}", response_model=ResponseClient,)
async def get_client(client_id: int, current_client=Depends(get_current_client)):
    result = await ClientService.get_client(client_id, current_client)
    return result

@router_client.put("/{client_id}", response_model=ResponseClient)
async def client_update(client_id: int, data: ClientCreate, current_client=Depends(get_current_client)):
    result = await ClientService.client_update(client_id, data, current_client)
    return result

@router_client.delete("/{client_id}", response_model=ResponseClient)
async def client_delete(client_id: int, current_client=Depends(get_current_client)):
    result = await ClientService.client_delete(client_id, current_client)
    return result

@router_client.get("/{client_id}/orders/count", response_model=ClientOrderdsCount)
async def client_orders_count(client_id: int, current_client=Depends(get_current_client)):
    result = await ClientService.get_client_order_count(client_id, current_client)
    return result

