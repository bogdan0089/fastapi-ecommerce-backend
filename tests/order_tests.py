import pytest
from pydantic import ValidationError
from core.enum import OrderStatus
from schemas.order_schema import ClientOrder, OrderCreate, UpdateOrderStatus


def test_create_order(client, auth_headers):
    response = client.post("/order/create_orders", json={
        "title": "My Test Order"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "My Test Order"
    assert "id" in response.json()


def test_create_order_unauthorized(client):
    response = client.post("/order/create_orders", json={"title": "Order"})
    assert response.status_code == 401


def test_get_order(client, auth_headers):
    created = client.post("/order/create_orders", json={
        "title": "Order To Get"
    }, headers=auth_headers)
    order_id = created.json()["id"]
    response = client.get(f"/order/{order_id}/orders", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_update_order_title(client, auth_headers):
    created = client.post("/order/create_orders", json={
        "title": "Old Title"
    }, headers=auth_headers)
    order_id = created.json()["id"]
    response = client.put(f"/order/order_update/{order_id}", json={
        "title": "New Title"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


def test_get_order_not_found(client, auth_headers):
    response = client.get("/order/orders/999999", headers=auth_headers)
    assert response.status_code == 404


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