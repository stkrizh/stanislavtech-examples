import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, cast
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, EmailStr

from with_dip.core import Notifier, PriorityDetector, TicketRepository, submit_ticket
from with_dip.db import AsyncSessionLocal, init_db
from with_dip.impl import (
    CompositeNotifier,
    OpenAiPriorityDetector,
    RegexPriorityDetector,
    SlackNotifier,
    SqlAlchemyTicketRepository,
    TelegramNotifier,
)
from with_dip.instrumentation import TicketRepositoryWithInstrumentation


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    async with httpx.AsyncClient() as http_client:
        app.state.ticket_repository = TicketRepositoryWithInstrumentation(
            SqlAlchemyTicketRepository(
                session_factory=AsyncSessionLocal,
            )
        )
        app.state.priority_detector = RegexPriorityDetector(
            OpenAiPriorityDetector(
                api_key=os.environ["OPENAI_API_KEY"],
            )
        )
        app.state.notifier = CompositeNotifier(
            [
                TelegramNotifier(
                    http_client=http_client,
                    bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
                    manager_id=os.environ["TELEGRAM_MANAGER_ID"],
                ),
                SlackNotifier(),
            ]
        )
        yield


app = FastAPI(lifespan=lifespan)


def get_ticket_repository(request: Request) -> TicketRepository:
    return cast(TicketRepository, request.app.state.ticket_repository)


def get_priority_detector(request: Request) -> PriorityDetector:
    return cast(PriorityDetector, request.app.state.priority_detector)


def get_notifier(request: Request) -> Notifier:
    return cast(Notifier, request.app.state.notifier)


class CreateTicketRequest(BaseModel):
    customer_email: EmailStr
    message: str


class CreateTicketResponse(BaseModel):
    id: UUID


@app.post("/tickets", status_code=201)
async def create_ticket(
    request: CreateTicketRequest,
    ticket_repository: TicketRepository = Depends(get_ticket_repository),
    priority_detector: PriorityDetector = Depends(get_priority_detector),
    notifier: Notifier = Depends(get_notifier),
) -> CreateTicketResponse:
    ticket = await submit_ticket(
        customer_email=request.customer_email,
        message=request.message,
        ticket_repository=ticket_repository,
        priority_detector=priority_detector,
        notifier=notifier,
    )
    return CreateTicketResponse(id=ticket.id)
