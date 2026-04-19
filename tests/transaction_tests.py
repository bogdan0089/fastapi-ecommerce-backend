import pytest
from pydantic import ValidationError
from core.enum import TransactionType
from schemas.transaction_schema import CreateTransaction


def test_get_my_transaction(client, auth_headers):
    response = client.get("/transaction/me/transactions", headers=auth_headers)
    assert response.status_code in (200, 404)
    

def test_create_transaction_valid():
    tr= CreateTransaction(
        amount=200.0,
        type=TransactionType.deposit,
        description="i love python",
        client_fk=1,
    )
    assert tr.amount == 200.0
    assert tr.type == TransactionType.deposit


def test_create_transaction_invalid_type():
    with pytest.raises(ValidationError):
        CreateTransaction(amount=100.0, type="invalid_type", description="test", client_fk=1)


def test_create_transaction_missing_amount():
    with pytest.raises(ValidationError):
        CreateTransaction(type=TransactionType.withdraw, description="test", client_fk=1)


def test_all_transaction_types():
    for tx_type in TransactionType:
        tx = CreateTransaction(amount=10.0, type=tx_type, description="test", client_fk=1)
        assert tx.type == tx_type
