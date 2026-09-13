import uuid

import pytest

from tests.conftest import _db_execute


def unique_name(prefix: str) -> str:
    """Category names are unique in the database, so every test needs its own."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


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
    name = unique_name("Shoes")

    response = client.post("/category/create", json={"name": name}, headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["name"] == name
    assert "id" in response.json()


def test_create_duplicate_category_is_rejected(client, admin_headers):
    name = unique_name("Shoes")
    client.post("/category/create", json={"name": name}, headers=admin_headers)

    response = client.post("/category/create", json={"name": name}, headers=admin_headers)

    assert response.status_code == 409


def test_create_category_unauthorized(client, auth_headers):
    response = client.post("/category/create", json={"name": "Shoes"}, headers=auth_headers)
    assert response.status_code == 403


def test_create_category_no_auth(client):
    response = client.post("/category/create", json={"name": "Shoes"})
    assert response.status_code == 401


def find_category(client, name) -> bool:
    """Page through the whole list: the endpoint returns 15 at a time, and the
    database keeps every category earlier runs created."""
    offset = 0
    while True:
        page = client.get(f"/category/all?limit=100&offset={offset}")
        assert page.status_code == 200
        rows = page.json()
        if not rows:
            return False
        if any(c["name"] == name for c in rows):
            return True
        offset += 100


def test_get_all_categories(client, admin_headers):
    name = unique_name("Electronics")
    client.post("/category/create", json={"name": name}, headers=admin_headers)

    assert find_category(client, name) is True


def test_delete_category(client, admin_headers):
    created = client.post(
        "/category/create", json={"name": unique_name("ToDelete")}, headers=admin_headers
    )
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
