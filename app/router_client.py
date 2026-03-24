from fastapi import APIRouter, Depends
from schemas.schemas import ClientCreate, ResponseClient, OperationsRequest, ClientUpdate, ClientOrderdsCount
from services.client_service import ClientService
from utils.dependencies import get_current_client


router_client = APIRouter(prefix="/client")


@router_client.post("/{client_id}/deposit")
async def client_deposit(client_id: int, deposit: OperationsRequest, current_client=Depends(get_current_client)):
     return await ClientService.client_deposit(
            client_id,
            deposit.amount,
            current_client
        )
          
@router_client.post("/{client_id}/withdraw")
async def client_withdraw(client_id: int, withdraw: OperationsRequest, current_client=Depends(get_current_client)):
     return await ClientService.client_withdraw(
            client_id,
            withdraw.amount,
            current_client
        )

@router_client.post("/create_client", response_model=ResponseClient)
async def create_client(client: ClientCreate):
    return await ClientService.create_client(data=client)

@router_client.get("/all_clients", response_model=list[ResponseClient])
async def get_clients():
    return await ClientService.get_all_client()

@router_client.get("/{client_id}", response_model=ResponseClient,)
async def get_client(client_id: int, current_client=Depends(get_current_client)):
        return await ClientService.get_client(client_id, current_client)

@router_client.put("/{client_id}", response_model=ResponseClient)
async def client_update(client_id: int, data: ClientCreate, current_client=Depends(get_current_client)):
    return await ClientService.client_update(client_id, data, current_client)

@router_client.delete("/{client_id}", response_model=ResponseClient)
async def client_delete(client_id: int, current_client=Depends(get_current_client)):
    return await ClientService.client_delete(client_id, current_client)

@router_client.get("/{client_id}/orders/count", response_model=ClientOrderdsCount)
async def client_orders_count(client_id: int, current_client=Depends(get_current_client)):
     return await ClientService.get_client_order_count(client_id, current_client)

