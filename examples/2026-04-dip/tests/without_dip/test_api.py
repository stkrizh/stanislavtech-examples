import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from without_dip.db import Ticket


def _llm_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def test_create_ticket_saves_normal_ticket_without_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # without_dip.api reads env vars and creates its OpenAI client at import time,
    # so importing here lets the autouse fixture prepare that global state first.
    import without_dip.api as api

    monkeypatch.setattr(
        api,
        "CLIENT",
        SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(return_value=_llm_response("NORMAL"))
                )
            )
        ),
    )
    added_tickets: list[Ticket] = []
    db = Mock()
    db.commit = AsyncMock()

    def add(ticket: Ticket) -> None:
        if getattr(ticket, "id", None) is None:
            ticket.id = uuid4()
        added_tickets.append(ticket)

    db.add.side_effect = add
    http_client = Mock()
    http_client.post = AsyncMock()
    request = api.CreateTicketRequest(
        customer_email="customer@example.com",
        message="The export button is slightly misaligned.",
    )

    response = asyncio.run(
        api.create_ticket(request=request, db=db, http_client=http_client)
    )

    assert len(added_tickets) == 1
    saved_ticket = added_tickets[0]
    assert saved_ticket.customer_email == "customer@example.com"
    assert saved_ticket.message == request.message
    assert saved_ticket.is_critical is False
    db.commit.assert_awaited_once()
    http_client.post.assert_not_awaited()
    assert response.id == saved_ticket.id


def test_create_ticket_notifies_manager_for_critical_ticket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # without_dip.api reads env vars and creates its OpenAI client at import time,
    # so importing here lets the autouse fixture prepare that global state first.
    import without_dip.api as api

    monkeypatch.setattr(
        api,
        "CLIENT",
        SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(return_value=_llm_response("CRITICAL"))
                )
            )
        ),
    )
    added_tickets: list[Ticket] = []
    db = Mock()
    db.commit = AsyncMock()

    def add(ticket: Ticket) -> None:
        if getattr(ticket, "id", None) is None:
            ticket.id = uuid4()
        added_tickets.append(ticket)

    db.add.side_effect = add
    http_client = Mock()
    http_client.post = AsyncMock()
    request = api.CreateTicketRequest(
        customer_email="customer@example.com",
        message="Production is down.",
    )

    response = asyncio.run(
        api.create_ticket(request=request, db=db, http_client=http_client)
    )

    assert len(added_tickets) == 1
    saved_ticket = added_tickets[0]
    assert saved_ticket.is_critical is True
    db.commit.assert_awaited_once()
    http_client.post.assert_awaited_once_with(
        "https://api.telegram.org/bottest-telegram-bot-token/sendMessage",
        json={"chat_id": "test-manager-id", "text": "Production is down."},
    )
    assert response.id == saved_ticket.id
