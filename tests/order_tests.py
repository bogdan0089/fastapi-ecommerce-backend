import uuid

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


def test_refund_uses_the_price_the_client_paid(client, auth_headers):
    """A price change after checkout must not change what the refund pays back."""
    me = client.get("/client/me", headers=auth_headers)
    client_id = me.json()["id"]
    client.post(f"/client/{client_id}/deposit", headers=auth_headers, json={"amount": 1000})

    name = f"price-change-{uuid.uuid4().hex[:8]}"
    product = client.post(
        "/product/",
        json={"name": name, "price": 50.0, "color": "black", "quantity": 10},
        headers=auth_headers,
    )
    product_id = product.json()["id"]
    _db_execute("UPDATE products SET status='accept' WHERE id=%s", (product_id,))

    order = client.post("/order/create_orders", json={"title": name}, headers=auth_headers)
    order_id = order.json()["id"]
    client.post(f"/order/{order_id}/products/{product_id}", headers=auth_headers)
    client.post(f"/order/{order_id}/checkout", headers=auth_headers)

    balance_after_checkout = client.get("/client/me", headers=auth_headers).json()["balance"]
    _db_execute("UPDATE products SET price=500 WHERE id=%s", (product_id,))

    client.post(f"/order/{order_id}/refund", headers=auth_headers)

    balance_after_refund = client.get("/client/me", headers=auth_headers).json()["balance"]
    assert balance_after_refund == balance_after_checkout + 50


def test_refund_already_cancelled(client, auth_headers):
    order = client.post("/order/create_orders", json={"title": "Cancel Order"}, headers=auth_headers)
    order_id = order.json()["id"]
    client.post(f"/order/{order_id}/refund", headers=auth_headers)
    response = client.post(f"/order/{order_id}/refund", headers=auth_headers)
    assert response.status_code == 400

def test_add_product_zero_quantity(client, auth_headers):
    product = client.post("/product/", json={"name": "zero-qty", "price": 10.0, "color": "black", "quantity": 5}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("zero-qty",))
    product_id = product.json()["id"]
    order = client.post("/order/create_orders", json={"title": "Zero Qty"}, headers=auth_headers)
    order_id = order.json()["id"]
    response = client.post(f"/order/{order_id}/products/{product_id}?quantity=0", headers=auth_headers)
    assert response.status_code == 422


def test_add_product_negative_quantity(client, auth_headers):
    product = client.post("/product/", json={"name": "neg-qty", "price": 10.0, "color": "black", "quantity": 5}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("neg-qty",))
    product_id = product.json()["id"]
    order = client.post("/order/create_orders", json={"title": "Neg Qty"}, headers=auth_headers)
    order_id = order.json()["id"]
    response = client.post(f"/order/{order_id}/products/{product_id}?quantity=-5", headers=auth_headers)
    assert response.status_code == 422


def test_add_product_more_than_in_stock(client, auth_headers):
    product = client.post("/product/", json={"name": "low-stock", "price": 10.0, "color": "black", "quantity": 2}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("low-stock",))
    product_id = product.json()["id"]
    order = client.post("/order/create_orders", json={"title": "Too Many"}, headers=auth_headers)
    order_id = order.json()["id"]
    response = client.post(f"/order/{order_id}/products/{product_id}?quantity=3", headers=auth_headers)
    assert response.status_code == 400


def test_refund_restores_product_stock(client, auth_headers):
    me = client.get("/client/me", headers=auth_headers)
    client_id = me.json()["id"]
    client.post(f"/client/{client_id}/deposit", headers=auth_headers, json={"amount": 1000})
    product = client.post("/product/", json={"name": "restock-me", "price": 20.0, "color": "blue", "quantity": 7}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("restock-me",))
    product_id = product.json()["id"]
    order = client.post("/order/create_orders", json={"title": "Restock Order"}, headers=auth_headers)
    order_id = order.json()["id"]
    client.post(f"/order/{order_id}/products/{product_id}?quantity=3", headers=auth_headers)
    client.post(f"/order/{order_id}/checkout", headers=auth_headers)
    assert client.get(f"/product/{product_id}").json()["quantity"] == 4
    client.post(f"/order/{order_id}/refund", headers=auth_headers)
    assert client.get(f"/product/{product_id}").json()["quantity"] == 7


def test_update_order_status_forbidden_for_client(client, auth_headers):
    order = client.post("/order/create_orders", json={"title": "Status Order"}, headers=auth_headers)
    order_id = order.json()["id"]
    response = client.put(f"/order/{order_id}/status", json={"status": "completed"}, headers=auth_headers)
    assert response.status_code == 403
