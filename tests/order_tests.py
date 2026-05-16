import pytest
from pydantic import ValidationError
from core.enum import OrderStatus
from schemas.order.input_dto import OrderClientCreateDTO, OrderCreateInternalDTO, OrderStatusUpdateDTO
from tests.conftest import _db_execute


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
    response = client.get("/order/999999/orders", headers=auth_headers)
    assert response.status_code == 404


def test_order_create_valid():
    order = OrderCreateInternalDTO(title="My Order", client_id=1)
    assert order.title == "My Order"
    assert order.client_id == 1


def test_order_create_missing_client_id():
    with pytest.raises(ValidationError):
        OrderCreateInternalDTO(title="My Order")


def test_order_create_missing_title():
    with pytest.raises(ValidationError):
        OrderCreateInternalDTO(client_id=1)


def test_client_order_valid():
    order = OrderClientCreateDTO(client_id=1, product_id=5, title="My Order")
    assert order.product_id == 5


def test_update_order_status_valid():
    data = OrderStatusUpdateDTO(status=OrderStatus.completed)
    assert data.status == OrderStatus.completed


def test_update_order_status_invalid():
    with pytest.raises(ValidationError):
        OrderStatusUpdateDTO(status="flying")


def test_checkout(client, auth_headers):
    me = client.get("/client/me", headers=auth_headers)
    client_id = me.json()["id"]
    client.post(f"/client/{client_id}/deposit", headers=auth_headers, json={"amount": 1000})
    product = client.post("/product/", json={"name": "samsung", "price": 50.0, "color": "black", "quantity": 10}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("samsung",))
    product_id = product.json()["id"]
    order = client.post("/order/create_orders", json={"title": "samsung"}, headers=auth_headers)
    order_id = order.json()["id"]
    client.post(f"/order/{order_id}/products/{product_id}", headers=auth_headers)
    response = client.post(f"/order/{order_id}/checkout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_refund_completed_order(client, auth_headers):
    me = client.get("/client/me", headers=auth_headers)
    client_id = me.json()["id"]
    client.post(f"/client/{client_id}/deposit", headers=auth_headers, json={"amount": 1000})
    product = client.post("/product/", json={"name": "macbook", "price": 50.0, "color": "white", "quantity": 10}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("macbook",))
    product_id = product.json()["id"]
    order = client.post("/order/create_orders", json={"title": "Refund Order"}, headers=auth_headers)
    order_id = order.json()["id"]
    client.post(f"/order/{order_id}/products/{product_id}", headers=auth_headers)
    client.post(f"/order/{order_id}/checkout", headers=auth_headers)
    response = client.post(f"/order/{order_id}/refund", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Order cancelled successfully"


def test_refund_already_cancelled(client, auth_headers):
    order = client.post("/order/create_orders", json={"title": "Cancel Order"}, headers=auth_headers)
    order_id = order.json()["id"]
    client.post(f"/order/{order_id}/refund", headers=auth_headers)
    response = client.post(f"/order/{order_id}/refund", headers=auth_headers)
    assert response.status_code == 400