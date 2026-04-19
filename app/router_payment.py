from fastapi import APIRouter, Request
import stripe
from core.config import settings
from schemas.transaction_schema import RequestPayment, CreateTransaction
from utils.dependencies import CurrentClient
from database.unit_of_work import UnitOfWork
from core.enum import TransactionType


stripe.api_key = settings.STRIPE_SECRET_KEY

router_payment = APIRouter(prefix="/payment")



@router_payment.post("/create")
async def payment_create(data: RequestPayment, current_client: CurrentClient):
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
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        client_id = int(intent["metadata"]["client_id"])
        amount = intent["amount"] / 100
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if client:
                client.balance += amount
                await uow.transaction.create_transaction(CreateTransaction(
                    amount=amount,
                    type=TransactionType.deposit,
                    description="Stripe payment",
                    client_fk=client_id
                ))
    return {"status": "ok"}

        


