import uuid

import stripe

import app.router_payment as payment_router


def _event(event_id: str, client_id: int, amount_cents: int) -> dict:
    return {
        "id": event_id,
        "type": "payment_intent.succeeded",
        "data": {"object": {"amount": amount_cents, "metadata": {"client_id": client_id}}},
    }


def test_duplicate_stripe_event_credits_the_balance_once(client, auth_headers, monkeypatch):
    """Stripe retries a webhook until it gets a 2xx, so the same event can arrive twice."""
    me = client.get("/client/me", headers=auth_headers).json()
    event = _event(f"evt_{uuid.uuid4().hex}", me["id"], 2500)
    monkeypatch.setattr(
        payment_router.stripe.Webhook, "construct_event", lambda *a, **kw: event
    )
    headers = {"stripe-signature": "whatever"}

    first = client.post("/payment/webhook", content=b"{}", headers=headers)
    second = client.post("/payment/webhook", content=b"{}", headers=headers)

    assert (first.status_code, second.status_code) == (200, 200)
    after = client.get("/client/me", headers=auth_headers).json()
    assert after["balance"] == me["balance"] + 25


def test_two_different_events_credit_twice(client, auth_headers, monkeypatch):
    me = client.get("/client/me", headers=auth_headers).json()
    events = [
        _event(f"evt_{uuid.uuid4().hex}", me["id"], 1000),
        _event(f"evt_{uuid.uuid4().hex}", me["id"], 1000),
    ]
    monkeypatch.setattr(
        payment_router.stripe.Webhook, "construct_event", lambda *a, **kw: events.pop(0)
    )
    headers = {"stripe-signature": "whatever"}

    client.post("/payment/webhook", content=b"{}", headers=headers)
    client.post("/payment/webhook", content=b"{}", headers=headers)

    after = client.get("/client/me", headers=auth_headers).json()
    assert after["balance"] == me["balance"] + 20


def test_invalid_signature_is_a_400(client, monkeypatch):
    """A 5xx would make Stripe retry a request that can never succeed."""

    def reject(*args, **kwargs):
        raise stripe.error.SignatureVerificationError("bad signature", "sig")

    monkeypatch.setattr(payment_router.stripe.Webhook, "construct_event", reject)

    response = client.post(
        "/payment/webhook", content=b"{}", headers={"stripe-signature": "forged"}
    )

    assert response.status_code == 400


def test_unknown_event_type_is_ignored(client, auth_headers, monkeypatch):
    me = client.get("/client/me", headers=auth_headers).json()
    event = {"id": f"evt_{uuid.uuid4().hex}", "type": "charge.refunded", "data": {"object": {}}}
    monkeypatch.setattr(
        payment_router.stripe.Webhook, "construct_event", lambda *a, **kw: event
    )

    response = client.post(
        "/payment/webhook", content=b"{}", headers={"stripe-signature": "whatever"}
    )

    assert response.status_code == 200
    after = client.get("/client/me", headers=auth_headers).json()
    assert after["balance"] == me["balance"]
