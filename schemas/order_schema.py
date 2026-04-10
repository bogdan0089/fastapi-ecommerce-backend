from pydantic import BaseModel, ConfigDict
from core.enum import OrderStatus


class OrderCreate(BaseModel):
    title: str
    client_id: int


class OrderCreateRequest(BaseModel):
    title: str


class OrderUpdateRequest(BaseModel):
    title: str


class ResponseOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    client_id: int
    status: OrderStatus


class OrderUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    client_id: int


class ClientOrder(BaseModel):
    client_id: int
    product_id: int
    title: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    title: str


class UpdateOrderStatus(BaseModel):
    status: OrderStatus
