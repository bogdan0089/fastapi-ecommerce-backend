import uuid
import pytest
from pydantic import ValidationError
from schemas.client_schema import ClientCreate, ClientUpdate, OperationsRequest


def test_register(client):
    email = f"user_{uuid.uuid4().hex[:8]}@gmail.com"
    response = client.post("/auth/register", json={
        "name": "Bohdan",
        "email": email,
        "password": "1111",
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
    client = ClientCreate(name="John", email="john@example.com", password="pass123", age=25, balance=100.0)
    assert client.name == "John"
    assert client.email == "john@example.com"


def test_client_create_missing_name():
    with pytest.raises(ValidationError):
        ClientCreate(email="john@example.com", password="pass", age=25)


def test_client_update_valid():
    update = ClientUpdate(name="New Name", age=30)
    assert update.name == "New Name"
    assert update.age == 30


def test_client_update_missing_age():
    with pytest.raises(ValidationError):
        ClientUpdate(name="New Name")


def test_operations_request_valid():
    op = OperationsRequest(amount=150.0)
    assert op.amount == 150.0


def test_operations_request_missing_amount():
    with pytest.raises(ValidationError):
        OperationsRequest()
