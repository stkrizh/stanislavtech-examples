from with_dip.core import (
    Priority,
    submit_ticket,
)
from tests.with_dip.conftest import (
    FakeNotifier,
    FakePriorityDetector,
    FakeTicketRepository,
)


async def test_submit_ticket_saves_normal_ticket_without_notification(
    ticket_repository: FakeTicketRepository,
    priority_detector: FakePriorityDetector,
    notifier: FakeNotifier,
) -> None:
    # Act
    ticket = await submit_ticket(
        customer_email="customer@example.com",
        message="The export button is slightly misaligned.",
        ticket_repository=ticket_repository,
        priority_detector=priority_detector,
        notifier=notifier,
    )
    # Assert
    assert await ticket_repository.get(ticket.id) == ticket
    assert notifier.notified_tickets == []
    assert ticket.customer_email == "customer@example.com"
    assert ticket.priority is Priority.NORMAL


async def test_submit_ticket_notifies_for_critical_ticket(
    ticket_repository: FakeTicketRepository,
    priority_detector: FakePriorityDetector,
    notifier: FakeNotifier,
) -> None:
    # Act
    ticket = await submit_ticket(
        customer_email="customer@example.com",
        message=FakePriorityDetector.CRITICAL_MESSAGE,
        ticket_repository=ticket_repository,
        priority_detector=priority_detector,
        notifier=notifier,
    )
    # Assert
    assert await ticket_repository.get(ticket.id) == ticket
    assert ticket.priority is Priority.CRITICAL
    notifier.assert_notification_sent()
