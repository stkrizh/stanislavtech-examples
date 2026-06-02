from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest


def _llm_response(content: str) -> Mock:
    return Mock(
        choices=[
            Mock(
                message=Mock(content=content),
            )
        ]
    )


async def test_create_ticket_saves_normal_ticket_without_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    # without_dip.api reads env vars and creates its OpenAI client at import time,
    # so importing here lets the autouse fixture prepare that global state first.
    import without_dip.api as api

    monkeypatch.setattr(
        api,
        "CLIENT",
        Mock(
            chat=Mock(
                completions=Mock(create=AsyncMock(return_value=_llm_response("NORMAL")))
            )
        ),
    )
    db = Mock()
    db.commit = AsyncMock()
    http_client = Mock()
    http_client.post = AsyncMock()
    # Act
    response = await api.create_ticket(
        request=api.CreateTicketRequest(
            customer_email="customer@example.com",
            message="The export button is slightly misaligned.",
        ),
        db=db,
        http_client=http_client,
    )
    # Assert
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    http_client.post.assert_not_awaited()
    assert isinstance(response.id, UUID)


async def test_create_ticket_notifies_manager_for_critical_ticket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    # without_dip.api reads env vars and creates its OpenAI client at import time,
    # so importing here lets the autouse fixture prepare that global state first.
    import without_dip.api as api

    monkeypatch.setattr(
        api,
        "CLIENT",
        Mock(
            chat=Mock(
                completions=Mock(
                    create=AsyncMock(return_value=_llm_response("CRITICAL"))
                )
            )
        ),
    )
    db = Mock()
    db.commit = AsyncMock()
    http_client = Mock()
    http_client.post = AsyncMock()
    # Act
    response = await api.create_ticket(
        request=api.CreateTicketRequest(
            customer_email="customer@example.com",
            message="Production is down.",
        ),
        db=db,
        http_client=http_client,
    )
    # Assert
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    http_client.post.assert_awaited_once_with(
        "https://api.telegram.org/bottest-telegram-bot-token/sendMessage",
        json={"chat_id": "test-manager-id", "text": "Production is down."},
    )
    assert isinstance(response.id, UUID)
