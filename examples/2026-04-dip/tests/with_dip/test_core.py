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
    assert priority_detector.detected_texts == [
        "The export button is slightly misaligned."
    ]
    assert ticket_repository.saved_tickets == [ticket]
    assert notifier.notified_tickets == []
    assert ticket.customer_email == "customer@example.com"
    assert ticket.priority is Priority.NORMAL


async def test_submit_ticket_notifies_for_critical_ticket(
    ticket_repository: FakeTicketRepository,
    priority_detector: FakePriorityDetector,
    notifier: FakeNotifier,
) -> None:
    # Arrange
    priority_detector.priority = Priority.CRITICAL
    # Act
    ticket = await submit_ticket(
        customer_email="customer@example.com",
        message="Production is down.",
        ticket_repository=ticket_repository,
        priority_detector=priority_detector,
        notifier=notifier,
    )
    # Assert
    assert priority_detector.detected_texts == ["Production is down."]
    assert ticket_repository.saved_tickets == [ticket]
    assert notifier.notified_tickets == [ticket]
    assert ticket.priority is Priority.CRITICAL
