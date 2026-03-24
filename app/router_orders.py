from fastapi import APIRouter, Depends
from schemas.schemas import OrderCreate, ResponseOrder, OrderUpdate, ProductsRead, ClientOrder, OrderResponse
from services.order_service import OrderService
from utils.dependencies import get_current_client

router_order = APIRouter(prefix="/order")


@router_order.post("/create_orders", response_model=ResponseOrder)
async def create_orders(order: OrderCreate):
        return await OrderService.create_order(
            data=order
        )

@router_order.get("/get_orders")
async def get_orders(limit: int = 10, offset: int = 0):
        return await OrderService.get_orders(limit, offset)

@router_order.get("/orders/{order_id}", response_model=ResponseOrder)
async def read_order(order_id: int, current_client=Depends(get_current_client)):
        return await OrderService.get_order(
            order_id,
            current_client
        )

@router_order.post("/{order_id}/products/{products_id}", response_model=ResponseOrder)
async def add_product_to_order(order_id: int, products_id: int, current_client=Depends(get_current_client)):
        return await OrderService.add_product_to_order(
            order_id,
            products_id,
            current_client
        )

@router_order.put("/order_update/{order_id}", response_model=OrderUpdate)
async def order_update(order_id: int, title: str, current_client=Depends(get_current_client)):
    return await OrderService.order_update(
        order_id,
        current_client,
        title=title
    ) 

@router_order.get("/order/{order_id}/total_price")
async def order_client_sum(order_id: int, current_client=Depends(get_current_client)):
    return await OrderService.order_client_sum(
        order_id,
        current_client
    )

@router_order.put("/client/{client_id}/order")
async def update_order_status(order_id: int, status: str, current_client=Depends(get_current_client)):
     return await OrderService.update_order_status(
        order_id,
        status,
        current_client
    )
     
@router_order.post("/orders", response_model=OrderResponse)
async def create_order_for_client(data: ClientOrder, current_client=Depends(get_current_client)):
    order =  await OrderService.create_order_client(
        current_client=current_client,
        client_id=data.client_id,
        product_id=data.product_id,
        title=data.title
    )
    return order

@router_order.get("/order_with_products/{order_id}")
async def order_with_products(order_id: int, current_client=Depends(get_current_client)):
      order_with_products = await OrderService.get_order_with_products(order_id, current_client)
      return order_with_products
