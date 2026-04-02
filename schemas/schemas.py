from pydantic import BaseModel
from typing import Optional
from core.enum import OrderStatus


class CreateTransaction(BaseModel):
    amount: float
    type: str
    description: str
    client_fk: int

class ResponseTransaction(CreateTransaction):
    id: int

class ClientCreate(BaseModel):
    password: str
    email: str
    name: str
    age: int
    balance: float

class ResponseClient(BaseModel):
    email: str
    name: str
    age: int
    balance: float
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

class ProductUpdate(BaseModel):
    name: Optional[str]
    price: Optional[float]

class ResponseOrder(OrderCreate):
    id: int

class OrderUpdate(OrderCreate):
    id: int
    
class ProductsCreate(BaseModel):
    name: str

class ResponseProduct(ProductsCreate):
    id: int

class OperationsRequest(BaseModel):
    amount: float

class UpdateOrderStatus(BaseModel):
    status: OrderStatus

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    client_id: int
    email: str
    age: int
    name: str

class TransactionArchive(BaseModel):
    description: str
    type: str

class RefreshResponse(BaseModel):
    access_token: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str


    