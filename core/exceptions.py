from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    def __init__(self, status_code, detail):
        super().__init__(status_code=status_code, detail=detail)

class OrderNotFoundError(BaseAppException):
    def __init__(self, order_id: int, title: str = None):
        if order_id:
            self.detail = f"Order with id: {order_id} not found."
        elif title:
            self.detail = f"Title {title} not found."
        else:
            self.detail = f"Not found."

        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=self.detail)
        self.order_id = order_id
        self.title = title
        
class OrdersNotFound(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Orders not found.")

class ClientNotFoundError(BaseAppException):
    def __init__(self, client_id: int = None, email: str = None):
        if client_id:
            self.detail = f"Client with id: {client_id} not found."
        elif email:
            self.detail = f"Client with email: {email} not found."
        else:
            self.detail = f"Not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=self.detail)
        self.client_id = client_id
        self.email = email

class ClientsNotFoundError(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

class ClientAlreadyError(BaseAppException):
    def __init__(self, email: str = None, client_id: int = None):
        if client_id:
            detail = f"Client with id: {client_id} already registered."
        elif email:
            detail = f"Client with email: {email} already registered."
        else:
            detail = f"Client is already."
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
        self.client_id=client_id
        self.email=email

class ProductAlready(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Product Already.")

class OrderAlready(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Order Already.")

class InsufficientPermissionsError(BaseAppException):
    def __init__(self, required_role: str, client_role: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Error you need role: {required_role} your role: {client_role}"
        )
        self.required_role=required_role
        self.client_role=client_role

class InvalidAmountError(BaseAppException):
    def __init__(self, amount: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid amount {amount} must be positive!"
        )
        self.amount = amount

class ClientUpdateError(BaseAppException):
    def __init__(self, client_id: int, reason = "Error Update"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error update client: {client_id} - {reason}"
        )
        self.client_id=client_id
        self.reason=reason

class OrderUpdateError(BaseAppException):
    def __init__(self, order_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error update order: {order_id}"
        )
        self.order_id = order_id

class OrderDeleteError(BaseAppException):
    def __init__(self, order_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error delete order: {order_id}"
        )
        self.order_id = order_id

class ClientDeleteError(BaseAppException):
    def __init__(self, client_id: int, reason="Error Delete"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error delete client_id: {client_id} - {reason}"
        )
        self.client_id=client_id
        self.reason=reason

class ClientTransactionNotFound(BaseAppException):
    def __init__(self, client_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Has not transactions: {client_id}"
        )
        self.client_id=client_id
                         
class NotEnoughMoneyError(BaseAppException):
    def __init__(self, client_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough money."
        )
        self.client_id = client_id

class TokenExpiredError(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired!")

class TokenInvalidError(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token!!")

class VerifyPasswordError(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed password!")

class TransactionNotFound(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction not found!"
        )

class ProductNotFound(BaseAppException):
    def __init__(self, product_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Product {product_id} not found!"
        )
        self.product_id = product_id