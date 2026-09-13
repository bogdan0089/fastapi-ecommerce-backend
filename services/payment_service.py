from decimal import Decimal

from core.enum import TransactionType
from database.unit_of_work import UnitOfWork
from schemas.transaction.input_dto import TransactionCreateDTO
from utils.logger import get_logger

logger = get_logger(__name__)


class PaymentService:

    @staticmethod
    async def handle_payment_success(event_id: str, client_id: int, amount: Decimal) -> bool:
        """Credit a successful payment once, however many times Stripe sends it.

        Returns False when this event was already processed.
        """
        async with UnitOfWork() as uow:
            if not await uow.stripe_event.claim(event_id):
                logger.info(
                    "payment_already_processed",
                    extra={"extra_fields": {"event_id": event_id, "client_id": client_id}},
                )
                return False

            client = await uow.client.get_client_with_lock(client_id)
            if client is None:
                logger.error(
                    "payment_for_unknown_client",
                    extra={
                        "extra_fields": {
                            "event_id": event_id,
                            "client_id": client_id,
                            "amount": str(amount),
                        }
                    },
                )
                return False

            client.balance += amount
            await uow.transaction.create_transaction(TransactionCreateDTO(
                amount=amount,
                type=TransactionType.deposit,
                description="deposit",
                client_fk=client.id
            ))

        logger.info(
            "payment_success",
            extra={
                "extra_fields": {
                    "event_id": event_id,
                    "client_id": client_id,
                    "amount": str(amount),
                }
            },
        )
        return True
