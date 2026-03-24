from enum import Enum as PyEnum
from sqlalchemy import Enum as SAEnum


class OrderStatus(PyEnum):
    create = "create"
    completed = "completed"
    cancelled = "cancelled"

class TransactionType(PyEnum):
    deposit = "deposit"
    withdraw = "withdraw"
    refund = "refund"
    purchase = "purchase"
