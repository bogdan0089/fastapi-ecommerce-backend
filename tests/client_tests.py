import pytest
from pydantic import ValidationError
from schemas.client_schema import ClientCreate, ClientUpdate, OperationsRequest


def test_client_create_valid():
    client = ClientCreate(name="John", email="john@example.com", password="pass123", age=25, balance=100.0)
    assert client.name == "John"
    assert client.email == "john@example.com"


def test_client_create_default_balance():
    client = ClientCreate(name="John", email="john@example.com", password="pass", age=25)
    assert client.balance == 0.0


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
