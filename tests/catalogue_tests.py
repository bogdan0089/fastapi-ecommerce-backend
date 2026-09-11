import uuid

import pytest

from tests.conftest import _db_execute


@pytest.fixture
def admin_headers(client, new_client):
    _db_execute("UPDATE clients SET role='superadmin' WHERE email=%s", (new_client["email"],))
    response = client.post("/auth/client_login", data={
        "username": new_client["email"],
        "password": new_client["password"],
    })
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def shelf(client, admin_headers):
    """Products under a name nothing else in the suite uses.

    The test database is shared by the whole session, so every catalogue query
    here is filtered by that tag; otherwise another test's product would drift
    into the counts.
    """
    tag = f"tag{uuid.uuid4().hex[:8]}"

    def stock(*prices: float, category_id: int | None = None) -> str:
        for index, price in enumerate(prices):
            client.post(
                "/product/",
                json={
                    "name": f"{tag} item {index}",
                    "price": price,
                    "color": "black",
                    "category_id": category_id,
                },
                headers=admin_headers,
            )
        _db_execute("UPDATE products SET status='accept' WHERE name LIKE %s", (f"{tag}%",))
        return tag

    return stock


def browse(client, **params):
    return client.get("/product/catalogue", params=params).json()


def test_a_page_carries_its_items_total_and_ceiling(client, shelf):
    tag = shelf(10.0, 20.0, 30.0)

    page = browse(client, name=tag)

    assert len(page["items"]) == 3
    assert page["total"] == 3
    assert page["price_ceiling"] == 30.0


def test_the_total_counts_every_match_not_just_the_page(client, shelf):
    tag = shelf(10.0, 20.0, 30.0, 40.0, 50.0)

    page = browse(client, name=tag, limit=2)

    assert len(page["items"]) == 2
    assert page["total"] == 5


def test_offset_walks_through_the_matches(client, shelf):
    tag = shelf(10.0, 20.0, 30.0, 40.0)

    first = browse(client, name=tag, limit=2, offset=0)
    second = browse(client, name=tag, limit=2, offset=2)

    ids = [p["id"] for p in first["items"]] + [p["id"] for p in second["items"]]
    assert len(set(ids)) == 4


def test_the_price_range_narrows_the_matches(client, shelf):
    tag = shelf(10.0, 50.0, 90.0)

    page = browse(client, name=tag, min_price=20, max_price=60)

    assert [p["price"] for p in page["items"]] == [50.0]
    assert page["total"] == 1


def test_the_ceiling_ignores_the_price_filter(client, shelf):
    tag = shelf(10.0, 50.0, 90.0)

    page = browse(client, name=tag, max_price=20)

    assert page["total"] == 1
    assert page["price_ceiling"] == 90.0


def test_the_ceiling_follows_the_other_filters(client, shelf, admin_headers):
    tag = shelf(10.0, 50.0, 90.0)

    page = browse(client, name=f"{tag} item 0")

    assert page["price_ceiling"] == 10.0


def test_a_category_narrows_the_matches(client, shelf, admin_headers):
    created = client.post(
        "/category/create",
        json={"name": f"Cat-{uuid.uuid4().hex[:8]}"},
        headers=admin_headers,
    )
    category_id = created.json()["id"]
    tag = shelf(15.0, 25.0, category_id=category_id)

    page = browse(client, name=tag, category_id=category_id)

    assert page["total"] == 2
    assert all(p["category"]["id"] == category_id for p in page["items"])


def test_a_category_with_nothing_in_it_returns_an_empty_page(client, shelf, admin_headers):
    created = client.post(
        "/category/create",
        json={"name": f"Cat-{uuid.uuid4().hex[:8]}"},
        headers=admin_headers,
    )
    shelf(15.0)

    page = browse(client, category_id=created.json()["id"])

    assert page["items"] == []
    assert page["total"] == 0
    assert page["price_ceiling"] == 0.0


def test_pending_products_stay_out_of_the_catalogue(client, admin_headers):
    tag = f"tag{uuid.uuid4().hex[:8]}"
    client.post(
        "/product/",
        json={"name": f"{tag} hidden", "price": 10.0, "color": "black"},
        headers=admin_headers,
    )

    page = browse(client, name=tag)

    assert page["total"] == 0


def test_an_oversized_limit_is_refused(client):
    assert client.get("/product/catalogue?limit=1000000").status_code == 422


def test_a_negative_price_is_refused(client):
    assert client.get("/product/catalogue?min_price=-1").status_code == 422
