from decimal import Decimal

import stripe
from fastapi import APIRouter, Request

from core.config import settings
from core.exceptions import InvalidWebhookSignatureError
from schemas.transaction.input_dto import PaymentRequestDTO
from services.payment_service import PaymentService
from utils.dependencies import CurrentClient, RateLimit

stripe.api_key = settings.STRIPE_SECRET_KEY

router_payment = APIRouter(prefix="/payment", tags=["Payment"])

@router_payment.post("/create")
async def payment_create(_: RateLimit, data: PaymentRequestDTO, current_client: CurrentClient):
    intent = stripe.PaymentIntent.create(
        amount=int(data.amount * 100),
        currency="usd",
        metadata={"client_id": current_client.id},
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
    )
    return {"client_secret": intent["client_secret"]}

@router_payment.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise InvalidWebhookSignatureError() from exc

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        client_id = int(intent["metadata"]["client_id"])
        amount = Decimal(intent["amount"]) / 100
        await PaymentService.handle_payment_success(event["id"], client_id, amount)
    return {
        "status": "ok"
    }
