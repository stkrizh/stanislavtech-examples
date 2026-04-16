import asyncio
from collections.abc import Sequence
import re
from uuid import UUID

import httpx
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from with_dip.core import Notifier, Priority, PriorityDetector, Ticket, TicketRepository
from with_dip.db import Ticket as TicketModel


class SqlAlchemyTicketRepository(TicketRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, ticket: Ticket) -> None:
        async with self._session_factory() as db:
            db_ticket = TicketModel(
                id=ticket.id,
                customer_email=ticket.customer_email,
                message=ticket.message,
                is_critical=ticket.priority is Priority.CRITICAL,
            )
            db.add(db_ticket)
            await db.commit()

    async def get(self, ticket_id: UUID) -> Ticket | None:
        async with self._session_factory() as db:
            db_ticket = await db.get(TicketModel, ticket_id)
            if db_ticket is None:
                return None
            return Ticket(
                id=db_ticket.id,
                customer_email=db_ticket.customer_email,
                message=db_ticket.message,
                priority=(
                    Priority.CRITICAL if db_ticket.is_critical else Priority.NORMAL
                ),
            )


class OpenAiPriorityDetector(PriorityDetector):
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def detect(self, text: str) -> Priority:
        llm_instructions = (
            "Analyze the priority of the following support ticket. "
            "Respond with 'CRITICAL' or 'NORMAL'."
        )
        llm_response = await self._client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "developer", "content": llm_instructions},
                {"role": "user", "content": text},
            ],
        )
        return (
            Priority.CRITICAL
            if llm_response.choices[0].message.content == "CRITICAL"
            else Priority.NORMAL
        )


class RegexPriorityDetector(PriorityDetector):
    def __init__(
        self,
        inner: PriorityDetector,
    ) -> None:
        self._inner = inner
        self._critical_pattern = re.compile(
            r"\bproduction\s+is\s+down\b", re.IGNORECASE
        )

    async def detect(self, text: str) -> Priority:
        if self._critical_pattern.search(text):
            return Priority.CRITICAL
        return await self._inner.detect(text)


RegexPrioriryDetector = RegexPriorityDetector


class TelegramNotifier(Notifier):
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        bot_token: str,
        manager_id: str,
    ) -> None:
        self._http_client = http_client
        self._bot_token = bot_token
        self._manager_id = manager_id

    async def notify(self, ticket: Ticket) -> None:
        await self._http_client.post(
            f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
            json={"chat_id": self._manager_id, "text": ticket.message},
        )


class SlackNotifier(Notifier):
    async def notify(self, ticket: Ticket) -> None:
        print("Posting an alert to Slack...")


class CompositeNotifier(Notifier):
    def __init__(self, notifiers: Sequence[Notifier]) -> None:
        self._notifiers = notifiers

    async def notify(self, ticket: Ticket) -> None:
        results = await asyncio.gather(
            *(notifier.notify(ticket) for notifier in self._notifiers),
            return_exceptions=True,
        )
        errors = [result for result in results if isinstance(result, Exception)]
        if errors:
            print("WARNING: one or more notifiers failed", errors)
