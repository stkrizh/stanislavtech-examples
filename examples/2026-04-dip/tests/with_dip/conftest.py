from uuid import UUID

import pytest

from with_dip.core import Notifier, Priority, PriorityDetector, Ticket, TicketRepository


class FakeTicketRepository(TicketRepository):
    def __init__(self) -> None:
        self.saved_tickets: list[Ticket] = []

    async def save(self, ticket: Ticket) -> None:
        self.saved_tickets.append(ticket)

    async def get(self, ticket_id: UUID) -> Ticket | None:
        for ticket in reversed(self.saved_tickets):
            if ticket.id == ticket_id:
                return ticket
        return None


class FakePriorityDetector(PriorityDetector):
    def __init__(self, priority: Priority) -> None:
        self.priority = priority
        self.detected_texts: list[str] = []

    async def detect(self, text: str) -> Priority:
        self.detected_texts.append(text)
        return self.priority


class FakeNotifier(Notifier):
    def __init__(self) -> None:
        self.notified_tickets: list[Ticket] = []

    async def notify(self, ticket: Ticket) -> None:
        self.notified_tickets.append(ticket)


@pytest.fixture
def ticket_repository() -> FakeTicketRepository:
    return FakeTicketRepository()


@pytest.fixture
def priority_detector() -> FakePriorityDetector:
    return FakePriorityDetector(Priority.NORMAL)


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()
