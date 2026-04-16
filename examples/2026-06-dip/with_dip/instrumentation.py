from uuid import UUID

from time import perf_counter

from with_dip.core import Ticket, TicketRepository


class TicketRepositoryWithInstrumentation(TicketRepository):
    def __init__(self, inner: TicketRepository) -> None:
        self._inner = inner

    async def save(self, ticket: Ticket) -> None:
        start = perf_counter()
        await self._inner.save(ticket)
        end = perf_counter()
        print("Total time:", end - start)

    async def get(self, ticket_id: UUID) -> Ticket | None:
        start = perf_counter()
        ticket = await self._inner.get(ticket_id)
        end = perf_counter()
        print("Total time:", end - start)
        return ticket
