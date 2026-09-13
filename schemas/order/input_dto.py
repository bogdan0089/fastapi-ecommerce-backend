from pydantic import BaseModel, Field

from core.enum import OrderStatus


class OrderCreateDTO(BaseModel):
    title: str = Field(..., min_length=1)


class OrderCreateInternalDTO(BaseModel):
    title: str
    client_id: int


class OrderUpdateDTO(BaseModel):
    title: str | None = Field(None, min_length=1)


class OrderStatusUpdateDTO(BaseModel):
    status: OrderStatus


class OrderClientCreateDTO(BaseModel):
    client_id: int
    product_id: int
    title: str = Field(..., min_length=1)
