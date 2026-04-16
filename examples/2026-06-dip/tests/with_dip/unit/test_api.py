from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import with_dip.api as api
from tests.with_dip.conftest import (
    FakeNotifier,
    FakePriorityDetector,
    FakeTicketRepository,
)


@pytest.fixture
def client(
    ticket_repository: FakeTicketRepository,
    priority_detector: FakePriorityDetector,
    notifier: FakeNotifier,
) -> Iterator[TestClient]:
    api.app.dependency_overrides[api.get_ticket_repository] = lambda: ticket_repository
    api.app.dependency_overrides[api.get_priority_detector] = lambda: priority_detector
    api.app.dependency_overrides[api.get_notifier] = lambda: notifier

    with TestClient(api.app) as test_client:
        yield test_client

    api.app.dependency_overrides.clear()


def test_create_ticket_runs_core_logic_if_request_valid(
    client: TestClient,
    ticket_repository: FakeTicketRepository,
) -> None:
    # Act
    response = client.post(
        "/tickets",
        json={
            "customer_email": "test@email.example",
            "message": "Production is down.",
        },
    )
    # Assert
    assert response.status_code == 201
    assert len(ticket_repository.saved_tickets) == 1


def test_create_ticket_validates_request_body_without_running_core_logic(
    client: TestClient,
    ticket_repository: FakeTicketRepository,
) -> None:
    # Act
    response = client.post(
        "/tickets",
        json={
            "customer_email": "invalid-email",
            "message": "Production is down.",
        },
    )
    # Assert
    assert response.status_code == 422
    assert ticket_repository.saved_tickets == []
