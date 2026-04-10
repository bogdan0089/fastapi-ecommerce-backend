from enum import Enum


class OrderStatus(Enum):
    create = "create"
    completed = "completed"
    cancelled = "cancelled"

class TransactionType(Enum):
    deposit = "deposit"
    withdraw = "withdraw"
    refund = "refund"
    purchase = "purchase"
