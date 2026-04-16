from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from with_dip.core import Priority, Ticket
from with_dip.db import Base
from with_dip.impl import SqlAlchemyTicketRepository


@pytest.fixture
async def sqlite_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def session_factory(sqlite_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=sqlite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
def ticket_repository(
    session_factory: async_sessionmaker[AsyncSession],
) -> SqlAlchemyTicketRepository:
    return SqlAlchemyTicketRepository(session_factory=session_factory)


async def test_sqlalchemy_ticket_repository_saves_ticket_to_database(
    ticket_repository: SqlAlchemyTicketRepository,
) -> None:
    # Arrange
    ticket = Ticket(
        id=UUID("12865c11-a2eb-4d6b-8c4f-9f1dd5b38daf"),
        customer_email="customer@example.com",
        message="Production is down.",
        priority=Priority.CRITICAL,
    )
    # Act
    await ticket_repository.save(ticket)
    # Assert
    saved_ticket = await ticket_repository.get(ticket.id)
    assert saved_ticket is not None
    assert saved_ticket.id == ticket.id
    assert saved_ticket.customer_email == ticket.customer_email
    assert saved_ticket.message == ticket.message
    assert saved_ticket.is_critical is True
