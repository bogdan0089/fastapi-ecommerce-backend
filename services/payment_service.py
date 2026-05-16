from core.enum import TransactionType
from database.unit_of_work import UnitOfWork
from schemas.transaction.input_dto import TransactionCreateDTO



class PaymentService:

    @staticmethod
    async def handle_payment_success(client_id: int, amount: float):
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if client:
                client.balance += amount
                await uow.transaction.create_transaction(TransactionCreateDTO(
                    amount=amount,
                    type=TransactionType.deposit,
                    description="deposit",
                    client_fk=client.id
                ))