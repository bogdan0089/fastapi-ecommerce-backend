import pytest
from tests.conftest import _db_execute


@pytest.fixture
def admin_headers(client, new_client):
    _db_execute("UPDATE clients SET role='superadmin' WHERE email=%s", (new_client["email"],))
    response = client.post("/auth/client_login", data={
        "username": new_client["email"],
        "password": new_client["password"],
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_category(client, admin_headers):
    response = client.post("/category/create", json={"name": "Shoes"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Shoes"
    assert "id" in response.json()


def test_create_category_unauthorized(client, auth_headers):
    response = client.post("/category/create", json={"name": "Shoes"}, headers=auth_headers)
    assert response.status_code == 403


def test_create_category_no_auth(client):
    response = client.post("/category/create", json={"name": "Shoes"})
    assert response.status_code == 401


def test_get_all_categories(client, admin_headers):
    client.post("/category/create", json={"name": "Electronics"}, headers=admin_headers)
    response = client.get("/category/all")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert any(c["name"] == "Electronics" for c in response.json())


def test_delete_category(client, admin_headers):
    created = client.post("/category/create", json={"name": "ToDelete"}, headers=admin_headers)
    category_id = created.json()["id"]
    response = client.delete(f"/category/{category_id}", headers=admin_headers)
    assert response.status_code == 204


def test_delete_category_not_found(client, admin_headers):
    response = client.delete("/category/999999", headers=admin_headers)
    assert response.status_code == 404


def test_delete_category_unauthorized(client, auth_headers):
    response = client.delete("/category/1", headers=auth_headers)
    assert response.status_code == 403


def test_delete_category_no_auth(client):
    response = client.delete("/category/1")
    assert response.status_code == 401
