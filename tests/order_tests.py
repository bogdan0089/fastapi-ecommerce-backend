import pytest
from pydantic import ValidationError
from core.enum import OrderStatus
from schemas.order_schema import ClientOrder, OrderCreate, UpdateOrderStatus


def test_order_create_valid():
    order = OrderCreate(title="My Order", client_id=1)
    assert order.title == "My Order"
    assert order.client_id == 1


def test_order_create_missing_client_id():
    with pytest.raises(ValidationError):
        OrderCreate(title="My Order")


def test_order_create_missing_title():
    with pytest.raises(ValidationError):
        OrderCreate(client_id=1)


def test_client_order_valid():
    order = ClientOrder(client_id=1, product_id=5, title="My Order")
    assert order.product_id == 5


def test_update_order_status_valid():
    data = UpdateOrderStatus(status=OrderStatus.completed)
    assert data.status == OrderStatus.completed


def test_update_order_status_invalid():
    with pytest.raises(ValidationError):
        UpdateOrderStatus(status="flying")
