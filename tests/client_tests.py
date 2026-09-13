import uuid

import pytest
from pydantic import ValidationError

from schemas.client.input_dto import ClientBalanceOperationDTO, ClientCreateDTO, ClientUpdateDTO


def test_register(client):
    email = f"user_{uuid.uuid4().hex[:8]}@gmail.com"
    response = client.post("/auth/register", json={
        "name": "Bohdan",
        "email": email,
        "password": "password111",
        "age": 19
    })
    assert response.status_code == 200


def test_login(client, new_client):
    response  = client.post("/auth/client_login", data={
        "username": new_client["email"],
        "password": new_client["password"]
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_short_password(client):
    response = client.post("/auth/register", json={
        "name": "Bohdan",
        "email": "test19@gmail.com",
        "password": "1234567",
        "age": 19
    })
    assert response.status_code == 422

def test_get_me(client, auth_headers, new_client):
    response = client.get("/client/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == new_client["email"]


def test_get_me_unauthorized(client):
    response = client.get("/client/me")
    assert response.status_code == 401
   

def test_register_duplicated_email(client, new_client):
    response = client.post("/auth/register", json={
        "name": new_client["name"],
        "email": new_client["email"],
        "password": new_client["password"],
        "age": new_client["age"]
    })
    assert response.status_code == 409
    

def test_deposit(client, auth_headers):
    me = client.get("/client/me", headers=auth_headers)
    client_id = me.json()["id"]
    response = client.post(f"/client/{client_id}/deposit", headers=auth_headers, json={
        "amount": 100
    })
    assert response.status_code == 200
    assert response.json()["balance"] == 100


def test_withdraw(client, auth_headers):
    me = client.get("/client/me", headers=auth_headers)
    client_id = me.json()["id"]
    client.post(f"/client/{client_id}/deposit", headers=auth_headers, json={"amount": 100})
    response = client.post(f"/client/{client_id}/withdraw", headers=auth_headers, json={
        "amount": 100
    })
    assert response.status_code == 200
    assert response.json()["balance"] == 0


def test_client_create_valid():
    client = ClientCreateDTO(name="John", email="john@example.com", password="pass1234", age=25, balance=100.0)
    assert client.name == "John"
    assert client.email == "john@example.com"


def test_client_create_missing_name():
    with pytest.raises(ValidationError):
        ClientCreateDTO(email="john@example.com", password="pass1234", age=25)


def test_client_update_valid():
    update = ClientUpdateDTO(name="New Name", age=30)
    assert update.name == "New Name"
    assert update.age == 30


def test_client_update_missing_age():
    with pytest.raises(ValidationError):
        ClientUpdateDTO(name="New Name")


def test_operations_request_valid():
    op = ClientBalanceOperationDTO(amount=150.0)
    assert op.amount == 150.0


def test_operations_request_missing_amount():
    with pytest.raises(ValidationError):
        ClientBalanceOperationDTO()


def test_get_my_orders(client, auth_headers):
    client.post("/order/create_orders", json={"title": "My Order"}, headers=auth_headers)
    response = client.get("/client/me/orders", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_my_stats(client, auth_headers):
    response = client.get("/client/me/stats", headers=auth_headers)
    assert response.status_code == 200
    assert "total_orders" in response.json()
    assert "balance" in response.json()


def test_change_password(client, auth_headers, new_client):
    response = client.post("/auth/change_password", headers=auth_headers, json={
        "old_password": new_client["password"],
        "new_password": "mikle123"
    })
    assert response.status_code == 200


def test_change_password_wrong_old(client, auth_headers):
    response = client.post("/auth/change_password", headers=auth_headers, json={
        "old_password": "wrongpassword",
        "new_password": "mikle123"
    })
    assert response.status_code == 401


def test_change_password_rejects_short_new(client, auth_headers, new_client):
    """The minimum applies when changing a password, not only when registering."""
    response = client.post("/auth/change_password", headers=auth_headers, json={
        "old_password": new_client["password"],
        "new_password": "short1"
    })
    assert response.status_code == 422


def test_reset_password_rejects_short_new(client):
    """Same minimum on the reset path, before the token is even looked at."""
    response = client.post("/auth/reset_password", json={
        "reset_token": "irrelevant",
        "new_password": "short1"
    })
    assert response.status_code == 422


def test_demo_top_up_credits_own_balance(client, auth_headers):
    """Deliberate: reviewers need a balance without a real card. See README."""
    before = client.get("/client/me", headers=auth_headers).json()

    response = client.post(
        f"/client/{before['id']}/deposit",
        headers=auth_headers,
        json={"amount": 50},
    )
    assert response.status_code == 200

    after = client.get("/client/me", headers=auth_headers).json()
    assert float(after["balance"]) == float(before["balance"]) + 50


def test_top_up_of_another_client_is_rejected(client, auth_headers):
    mine = client.get("/client/me", headers=auth_headers).json()

    response = client.post(
        f"/client/{mine['id'] + 1000}/deposit",
        headers=auth_headers,
        json={"amount": 50},
    )
    assert response.status_code in (403, 404)


def test_register_rejects_short_password(client):
    response = client.post("/auth/register", json={
        "name": "Short Pass",
        "email": "short.pass@example.com",
        "password": "short1",
        "age": 25
    })
    assert response.status_code == 422
