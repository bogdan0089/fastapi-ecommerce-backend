from core.exceptions import (
    ClientAlreadyError,
    ClientNotFoundError,
    InsufficientPermissionsError,
    InvalidAmountError,
    NotEnoughMoneyError,
    OrderNotFoundError,
    ProductNotFound,
    TokenExpiredError,
    VerifyPasswordError,
)


def test_client_not_found_by_id():
    exc = ClientNotFoundError(client_id=5)
    assert exc.status_code == 404
    assert "5" in exc.detail


def test_client_not_found_by_email():
    exc = ClientNotFoundError(email="test@example.com")
    assert exc.status_code == 404
    assert "test@example.com" in exc.detail


def test_client_already_registered():
    exc = ClientAlreadyError(email="test@example.com")
    assert exc.status_code == 409
    assert "test@example.com" in exc.detail


def test_product_not_found():
    exc = ProductNotFound(product_id=10)
    assert exc.status_code == 404
    assert "10" in exc.detail


def test_order_not_found():
    exc = OrderNotFoundError(order_id=3)
    assert exc.status_code == 404
    assert "3" in exc.detail


def test_verify_password_error():
    exc = VerifyPasswordError()
    assert exc.status_code == 401


def test_token_expired():
    exc = TokenExpiredError()
    assert exc.status_code == 401


def test_insufficient_permissions():
    exc = InsufficientPermissionsError(required_role="owner", client_role="client")
    assert exc.status_code == 403
    assert "owner" in exc.detail


def test_invalid_amount():
    exc = InvalidAmountError(amount=-50.0)
    assert exc.status_code == 400
    assert "-50.0" in exc.detail


def test_not_enough_money():
    exc = NotEnoughMoneyError(client_id=1)
    assert exc.status_code == 400
