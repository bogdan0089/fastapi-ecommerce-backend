from fastapi import APIRouter
from schemas.order_schema import (
    ClientOrder,
    OrderCreateRequest,
    OrderResponse,
    OrderUpdate,
    OrderUpdateRequest,
    ResponseOrder,
    UpdateOrderStatus,
)
from services.order_service import OrderService
from utils.dependencies import CurrentClient


router_order = APIRouter(prefix="/order")


@router_order.post("/create_orders", response_model=ResponseOrder)
async def create_order(order: OrderCreateRequest, current_client: CurrentClient) -> ResponseOrder:
    return await OrderService.create_order(title=order.title, current_client=current_client)

@router_order.get("/get_orders", response_model=list[ResponseOrder])
async def get_orders(_: CurrentClient, limit: int = 10, offset: int = 0) -> list:
    return await OrderService.get_orders(limit, offset)

@router_order.get("/orders/{order_id}", response_model=ResponseOrder)
async def read_order(order_id: int, current_client: CurrentClient) -> ResponseOrder:
    return await OrderService.get_order(order_id, current_client)

@router_order.post("/{order_id}/products/{products_id}", response_model=ResponseOrder)
async def add_product_to_order(
    order_id: int, products_id: int, current_client: CurrentClient
) -> ResponseOrder:
    return await OrderService.add_product_to_order(order_id, products_id, current_client)

@router_order.put("/order_update/{order_id}", response_model=OrderUpdate)
async def order_update(
    order_id: int, data: OrderUpdateRequest, current_client: CurrentClient
) -> OrderUpdate:
    return await OrderService.order_update(order_id, current_client, title=data.title)

@router_order.get("/order/{order_id}/total_price")
async def order_client_sum(order_id: int, current_client: CurrentClient) -> dict:
    return await OrderService.order_client_sum(order_id, current_client)

@router_order.put("/{order_id}/status", response_model=ResponseOrder)
async def update_order_status(
    order_id: int, data: UpdateOrderStatus, current_client: CurrentClient
) -> ResponseOrder:
    return await OrderService.update_order_status(order_id, data.status, current_client)

@router_order.post("/orders", response_model=OrderResponse)
async def create_order_for_client(
    data: ClientOrder, current_client: CurrentClient
) -> OrderResponse:
    return await OrderService.create_order_client(
        current_client=current_client,
        client_id=data.client_id,
        product_id=data.product_id,
        title=data.title,
    )

@router_order.get("/order_with_products/{order_id}")
async def order_with_products(order_id: int, current_client: CurrentClient) -> dict:
    return await OrderService.get_order_with_products(order_id, current_client)

@router_order.delete("/{order_id}/order/{product_id}/product", response_model=ResponseOrder)
async def delete_product_from_order_id(
    order_id: int, product_id: int, current_client: CurrentClient
) -> ResponseOrder:
    return await OrderService.delete_product_from_order(order_id, product_id, current_client)

@router_order.post("/{order_id}/checkout", response_model=ResponseOrder)
async def checkout(order_id: int, current_client: CurrentClient) -> ResponseOrder:
    return await OrderService.checkout(order_id, current_client)

@router_order.post("/{order_id}/refund", response_model=ResponseOrder)
async def cancelled_order(order_id: int, current_client: CurrentClient) -> ResponseOrder:
    return await OrderService.cancell_order(order_id, current_client)
