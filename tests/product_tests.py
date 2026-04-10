import pytest
from pydantic import ValidationError
from schemas.product_schema import ProductCreate, ProductUpdate


def test_product_create_valid():
    product = ProductCreate(name="Nike Air", price=99.99)
    assert product.name == "Nike Air"
    assert product.price == 99.99


def test_product_create_default_price():
    product = ProductCreate(name="Nike Air")
    assert product.price == 0.0


def test_product_create_missing_name():
    with pytest.raises(ValidationError):
        ProductCreate()


def test_product_update_all_optional():
    update = ProductUpdate()
    assert update.name is None
    assert update.price is None


def test_product_update_only_price():
    update = ProductUpdate(price=49.99)
    assert update.price == 49.99
    assert update.name is None
