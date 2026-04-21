from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)

class OrderNotFoundError(BaseAppException):
    def __init__(self, order_id: int | None = None, title: str | None = None) -> None:
        if order_id is not None:
            detail = f"Order with id {order_id} not found."
        elif title:
            detail = f"Order with title '{title}' not found."
        else:
            detail = "Order not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class OrdersNotFound(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found.")

class ClientNotFoundError(BaseAppException):
    def __init__(self, client_id: int | None = None, email: str | None = None) -> None:
        if client_id is not None:
            detail = f"Client with id {client_id} not found."
        elif email:
            detail = f"Client with email '{email}' not found."
        else:
            detail = "Client not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ClientsNotFoundError(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="No clients found.")

class ProductsNotFound(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Not found products.")

class ClientAlreadyError(BaseAppException):
    def __init__(self, email: str | None = None, client_id: int | None = None) -> None:
        if client_id is not None:
            detail = f"Client with id {client_id} is already registered."
        elif email:
            detail = f"Client with email '{email}' is already registered."
        else:
            detail = "Client is already registered."
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class ProductAlready(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="Product is already in the order.")

class ProductNotApprovedError(BaseAppException):
    def __init__(self, product_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product {product_id} is not approved for sale."
        )

class OrderAlready(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="Order is already completed.")

class InsufficientPermissionsError(BaseAppException):
    def __init__(self, required_role: str, client_role: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required: '{required_role}', your role: '{client_role}'.",
        )

class InvalidAmountError(BaseAppException):
    def __init__(self, amount: float) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid amount {amount}. Must be a positive number.",
        )

class ClientUpdateError(BaseAppException):
    def __init__(self, client_id: int, reason: str = "Update failed.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update client {client_id}: {reason}",
        )

class OrderUpdateError(BaseAppException):
    def __init__(self, order_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )

class OrderDeleteError(BaseAppException):
    def __init__(self, order_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete order {order_id}.",
        )

class ClientDeleteError(BaseAppException):
    def __init__(self, client_id: int, reason: str = "Delete failed.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete client {client_id}: {reason}",
        )

class ClientTransactionNotFound(BaseAppException):
    def __init__(self, client_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transactions found for client {client_id}.",
        )

class NotEnoughMoneyError(BaseAppException):
    def __init__(self, client_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance for client {client_id}.",
        )

class TokenExpiredError(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")

class TokenInvalidError(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

class VerifyPasswordError(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")
        
class TransactionNotFound(BaseAppException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

class ProductNotFound(BaseAppException):
    def __init__(self, product_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )

class OrderNotCompletedError(BaseAppException):
    def __init__(self, order_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order {order_id} is not in 'completed' status.",
        )

class EmailNotVerifiedError(BaseAppException):
    def __init__(self, client_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not verify client_id: {client_id}"
        )

class OrderCannotBeCancelledError(BaseAppException):
    def __init__(self, order_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cancelled {order_id}"
        )

class InvalidOrderTransitionError(BaseAppException):
    def __init__(self, from_status, to_status) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition order from {from_status} to {to_status}"
        )

class TooManyRequests(BaseAppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again later."
        )