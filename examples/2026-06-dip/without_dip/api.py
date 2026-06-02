import os
from typing import AsyncIterator, cast
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import httpx
from fastapi import Depends, FastAPI, Request
from openai import AsyncOpenAI
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from without_dip.db import AsyncSessionLocal, Ticket, init_db


CLIENT = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MANAGER_ID = os.environ["TELEGRAM_MANAGER_ID"]
LLM_INSTRUCTIONS = (
    "Analyze the priority of the following support ticket. "
    "Respond with 'CRITICAL' or 'NORMAL'."
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_http_client(request: Request) -> httpx.AsyncClient:
    return cast(httpx.AsyncClient, request.app.state.http_client)


class CreateTicketRequest(BaseModel):
    customer_email: EmailStr
    message: str


class CreateTicketResponse(BaseModel):
    id: UUID


@app.post("/tickets", status_code=201)
async def create_ticket(
    request: CreateTicketRequest,
    db: AsyncSession = Depends(get_db),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> CreateTicketResponse:
    llm_response = await CLIENT.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "developer", "content": LLM_INSTRUCTIONS},
            {"role": "user", "content": request.message},
        ],
    )
    is_critical = llm_response.choices[0].message.content == "CRITICAL"
    ticket = Ticket(
        id=uuid4(),
        customer_email=request.customer_email,
        message=request.message,
        is_critical=is_critical,
    )
    db.add(ticket)
    await db.commit()
    if is_critical:
        await http_client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": MANAGER_ID, "text": ticket.message},
        )
    return CreateTicketResponse(id=ticket.id)
