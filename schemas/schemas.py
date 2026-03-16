from pydantic import BaseModel
from typing import Optional
from models.models import OrderStatus


class CreateTransaction(BaseModel):
    amount: float
    type: str
    description: str
    client_fk: int

class ResponseTransaction(CreateTransaction):
    id: int


class ClientCreate(BaseModel):
    name: str
    age: int

class ResponseClient(ClientCreate):
    id: int


class ClientOrderdsCount(BaseModel):
    client_id: int
    orders_count: int

class ClientUpdate(BaseModel):
    name: str
    age: int

class OrderCreate(BaseModel):
    title: str
    client_id: int

class ClientOrder(BaseModel):
    client_id: int
    product_id: int
    title: str

class OrderResponse(BaseModel):
    id: int
    client_id: int
    title: str

    class Config:
        from_attributes = True


class ResponseOrder(OrderCreate):
    id: int


class OrderUpdate(OrderCreate):
    id: int
    

class ProductsCreate(BaseModel):
    name: str


class ProductsRead(ProductsCreate):
    id: int


class OperationsRequest(BaseModel):
    amount: float


class UpdateOrderStatus(BaseModel):
    status: OrderStatus