from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    name: str
    email: str
    password: str
    age: int
    balance: float = 0.0


class ClientUpdate(BaseModel):
    name: str
    age: int


class ResponseClient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    age: int
    balance: float


class ClientOrdersCount(BaseModel):
    client_id: int
    orders_count: int


class OperationsRequest(BaseModel):
    amount: float
