from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4


class Priority(Enum):
    NORMAL = "normal"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Ticket:
    customer_email: str
    message: str
    priority: Priority
    id: UUID = field(default_factory=uuid4)

    @property
    def is_critical(self) -> bool:
        return self.priority is Priority.CRITICAL


class TicketRepository(Protocol):
    async def save(self, ticket: Ticket) -> None: ...
    async def get(self, ticket_id: UUID) -> Ticket | None: ...


class PriorityDetector(Protocol):
    async def detect(self, text: str) -> Priority: ...


class Notifier(Protocol):
    async def notify(self, ticket: Ticket) -> None: ...


async def submit_ticket(
    customer_email: str,
    message: str,
    ticket_repository: TicketRepository,
    priority_detector: PriorityDetector,
    notifier: Notifier,
) -> Ticket:
    priority = await priority_detector.detect(message)
    ticket = Ticket(
        customer_email=customer_email,
        message=message,
        priority=priority,
    )
    await ticket_repository.save(ticket)
    if ticket.is_critical:
        await notifier.notify(ticket)
    return ticket
