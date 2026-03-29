from fastapi import APIRouter, Depends
from schemas.schemas import OrderCreate, ResponseOrder, OrderUpdate, ClientOrder, OrderResponse
from services.order_service import OrderService
from utils.dependencies import get_current_client


router_order = APIRouter(prefix="/order")


@router_order.post("/create_orders", response_model=ResponseOrder)
async def create_orders(order: OrderCreate):
        result = await OrderService.create_order(
            data=order
        )
        return result

@router_order.get("/get_orders")
async def get_orders(limit: int = 10, offset: int = 0):
        result = await OrderService.get_orders(limit, offset)
        return result

@router_order.get("/orders/{order_id}", response_model=ResponseOrder)
async def read_order(order_id: int, current_client=Depends(get_current_client)):
        result = await OrderService.get_order(
            order_id,
            current_client
        )
        return result

@router_order.post("/{order_id}/products/{products_id}", response_model=ResponseOrder)
async def add_product_to_order(order_id: int, products_id: int, current_client=Depends(get_current_client)):
        result = await OrderService.add_product_to_order(
            order_id,
            products_id,
            current_client
        )
        return result

@router_order.put("/order_update/{order_id}", response_model=OrderUpdate)
async def order_update(order_id: int, title: str, current_client=Depends(get_current_client)):
    result = await OrderService.order_update(
        order_id,
        current_client,
        title=title
    ) 
    return result

@router_order.get("/order/{order_id}/total_price")
async def order_client_sum(order_id: int, current_client=Depends(get_current_client)):
    result = await OrderService.order_client_sum(
        order_id,
        current_client
    )
    return result

@router_order.put("/{order_id}/status")
async def update_order_status(order_id: int, status: str, current_client=Depends(get_current_client)):
    result = await OrderService.update_order_status(
        order_id,
        status,
        current_client
    )
    return result
     
@router_order.post("/orders", response_model=OrderResponse)
async def create_order_for_client(data: ClientOrder, current_client=Depends(get_current_client)):
    result = await OrderService.create_order_client(
        current_client=current_client,
        client_id=data.client_id,
        product_id=data.product_id,
        title=data.title
    )
    return result 

@router_order.get("/order_with_products/{order_id}")
async def order_with_products(order_id: int, current_client=Depends(get_current_client)):
      result = await OrderService.get_order_with_products(order_id, current_client)
      return result

@router_order.delete("/{order_id}/order/{product_id}/product")
async def delete_product_from_order_id(order_id: int, product_id: int, current_client=Depends(get_current_client)):
    result = await OrderService.delete_product_from_order(order_id, product_id, current_client)
    return result

@router_order.post("/{order_id}/checkout", response_model=ResponseOrder)
async def checkout(order_id: int, current_client=Depends(get_current_client)):
    result = await OrderService.checkout(order_id, current_client)
    return result