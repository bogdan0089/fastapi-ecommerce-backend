from pydantic import BaseModel, ConfigDict
from core.enum import TransactionType


class CreateTransaction(BaseModel):
    amount: float
    type: TransactionType
    description: str
    client_fk: int

class ResponseTransaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: TransactionType
    description: str
    client_fk: int

class TransactionArchive(BaseModel):
    description: str
    type: TransactionType

class RequestPayment(BaseModel):
    amount: float