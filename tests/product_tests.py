import pytest
from pydantic import ValidationError
from schemas.product_schema import ProductCreate, ProductUpdate
from tests.conftest import _db_execute


def test_create_product(client, auth_headers):
    response = client.post("/product/", json={
        "name": "Nike Air",
        "price": 99.99,
        "color": "black"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Nike Air"
    assert response.json()["price"] == 99.99


def test_create_product_unauthorized(client):
    response = client.post("/product/", json={
        "name": "Nike Air",
        "price": 99.99,
        "color": "black"
    })
    assert response.status_code == 401


def test_get_product(client, auth_headers):
    created = client.post("/product/", json={
        "name": "Adidas",
        "price": 79.99,
        "color": "black"
    }, headers=auth_headers)
    product_id = created.json()["id"]
    response = client.get(f"/product/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id
    assert response.json()["name"] == "Adidas"


def test_get_product_not_found(client):
    response = client.get("/product/999999")
    assert response.status_code == 404


def test_get_all_products(client):
    response = client.get("/product/all")
    assert response.status_code in (200, 404)


def test_filter_products_by_color(client, auth_headers):
    client.post("/product/",  headers=auth_headers, json={
        "name": "iphone", "price": 999, "color": "red"
    })
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("iphone",))
    response = client.get("/product/color/red")
    assert response.status_code == 200
    assert any(p["color"] == "red" for p in response.json())


def test_search_products(client, auth_headers):
    client.post("/product/", json={"name": "Mac", "price": 10.0, "color": "black"}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("Mac",))
    response = client.get("/product/search?name=Mac")
    assert response.status_code == 200
    assert any(p["name"] == "Mac" for p in response.json())


def test_filter_products_by_price(client, auth_headers):
    client.post("/product/", json={"name": "Samsung", "price": 5.0, "color": "black"}, headers=auth_headers)
    _db_execute("UPDATE products SET status='accept' WHERE name=%s", ("Samsung",))
    response = client.get("/product/filter?min_price=1.0&max_price=10.0")
    assert response.status_code == 200
    for product in response.json():
        assert product["price"] >= 1.0
        assert product["price"] <= 10.0


def test_product_create_valid():
    product = ProductCreate(name="Nike Air", price=99.99, color="black")
    assert product.name == "Nike Air"
    assert product.price == 99.99
    assert product.color == "black"


def test_product_create_default_price():
    product = ProductCreate(name="Nike Air", color="black")
    assert product.price == 0.0
    assert product.color == "black"


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