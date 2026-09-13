from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import ProcessedStripeEvent


class StripeEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def claim(self, event_id: str) -> bool:
        """Try to mark an event as ours to process.

        Returns False when the row is already there, which means a previous
        delivery of the same event was handled and this one must be ignored.
        ON CONFLICT DO NOTHING keeps the check and the insert in one statement,
        so two concurrent deliveries cannot both win.
        """
        statement = (
            insert(ProcessedStripeEvent)
            .values(event_id=event_id)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(ProcessedStripeEvent.event_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None
