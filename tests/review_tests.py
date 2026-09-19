import uuid

from tests.conftest import _db_execute


def _create_product(client, auth_headers):
    response = client.post("/product/", json={
        "name": "Test Product",
        "price": 100.0,
        "color": "black"
    }, headers=auth_headers)
    product_id = response.json()["id"]
    _db_execute("UPDATE products SET status='accept' WHERE id=%s", (product_id,))
    return product_id


def test_create_review(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    response = client.post("/review/", json={
        "rating": 5,
        "comment": "Чудовий продукт",
        "product_id": product_id
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["rating"] == 5
    assert response.json()["product_id"] == product_id


def test_create_review_unauthorized(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    response = client.post("/review/", json={
        "rating": 5,
        "product_id": product_id
    })
    assert response.status_code == 401


def test_create_review_invalid_rating(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    response = client.post("/review/", json={
        "rating": 10,
        "product_id": product_id
    }, headers=auth_headers)
    assert response.status_code == 422


def test_get_review_by_id(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    created = client.post("/review/", json={
        "rating": 4,
        "comment": "Добре",
        "product_id": product_id
    }, headers=auth_headers)
    review_id = created.json()["id"]
    response = client.get(f"/review/{review_id}")
    assert response.status_code == 200
    assert response.json()["id"] == review_id
    assert response.json()["rating"] == 4


def test_get_review_not_found(client):
    response = client.get("/review/999999")
    assert response.status_code == 404


def test_get_reviews_by_product(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    client.post("/review/", json={
        "rating": 3,
        "comment": "Нормально",
        "product_id": product_id
    }, headers=auth_headers)
    response = client.get(f"/review/product/{product_id}")
    assert response.status_code == 200
    assert any(r["product_id"] == product_id for r in response.json())


def test_get_reviews_by_product_not_found(client):
    response = client.get("/review/product/999999")
    assert response.status_code == 404


def _login_as_new_client(client, role: str | None = None) -> dict:
    """Register, verify and sign in another client, optionally with a role."""
    email = f"user_{uuid.uuid4().hex[:8]}@gmail.com"
    client.post("/auth/register", json={"name": "Other", "email": email, "password": "pass1234", "age": 30})
    _db_execute("UPDATE clients SET is_verified=true WHERE email=%s", (email,))
    if role:
        _db_execute("UPDATE clients SET role=%s WHERE email=%s", (role, email))
    token = client.post("/auth/client_login", data={"username": email, "password": "pass1234"}).json()
    return {"Authorization": f"Bearer {token['access_token']}"}


def _create_review(client, auth_headers) -> int:
    product_id = _create_product(client, auth_headers)
    created = client.post("/review/", json={"rating": 2, "product_id": product_id}, headers=auth_headers)
    return created.json()["id"]


def test_delete_review(client, auth_headers):
    review_id = _create_review(client, auth_headers)

    response = client.delete(f"/review/{review_id}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(f"/review/{review_id}").status_code == 404


def test_delete_review_not_found(client, auth_headers):
    response = client.delete("/review/999999", headers=auth_headers)
    assert response.status_code == 404


def test_an_anonymous_visitor_cannot_delete_a_review(client, auth_headers):
    review_id = _create_review(client, auth_headers)

    assert client.delete(f"/review/{review_id}").status_code == 401
    assert client.get(f"/review/{review_id}").status_code == 200


def test_another_client_cannot_delete_a_review(client, auth_headers):
    review_id = _create_review(client, auth_headers)
    other = _login_as_new_client(client)

    assert client.delete(f"/review/{review_id}", headers=other).status_code == 403
    assert client.get(f"/review/{review_id}").status_code == 200


def test_a_moderator_can_delete_any_review(client, auth_headers):
    review_id = _create_review(client, auth_headers)
    moderator = _login_as_new_client(client, role="moderator")

    assert client.delete(f"/review/{review_id}", headers=moderator).status_code == 204


def test_second_review_of_the_same_product_is_rejected(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    payload = {"rating": 5, "comment": "Перший", "product_id": product_id}
    assert client.post("/review/", json=payload, headers=auth_headers).status_code == 200

    second = client.post("/review/", json={**payload, "comment": "Другий"}, headers=auth_headers)
    assert second.status_code == 409

    listed = client.get(f"/review/product/{product_id}").json()
    assert len(listed) == 1


def test_review_for_a_missing_product_is_404(client, auth_headers):
    response = client.post("/review/", json={
        "rating": 5,
        "product_id": 999999,
    }, headers=auth_headers)
    assert response.status_code == 404
