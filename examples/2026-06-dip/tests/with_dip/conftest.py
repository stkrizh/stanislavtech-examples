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
    CRITICAL_MESSAGE = "critical"

    async def detect(self, text: str) -> Priority:
        return Priority.CRITICAL if text == self.CRITICAL_MESSAGE else Priority.NORMAL


class FakeNotifier(Notifier):
    def __init__(self) -> None:
        self.notified_tickets: list[Ticket] = []

    async def notify(self, ticket: Ticket) -> None:
        self.notified_tickets.append(ticket)

    def assert_notification_sent(self) -> None:
        assert self.notified_tickets


@pytest.fixture
def ticket_repository() -> FakeTicketRepository:
    return FakeTicketRepository()


@pytest.fixture
def priority_detector() -> FakePriorityDetector:
    return FakePriorityDetector()


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()
