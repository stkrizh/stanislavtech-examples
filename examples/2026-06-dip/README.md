# DIP Examples

Examples for https://stanislav.tech/articles/dip

This project contains two FastAPI apps that implement the same support ticket submission
flow in different ways:

- `without_dip`: a version with infrastructure wired directly into the request handler
- `with_dip`: a version that separates core logic from infrastructure using DIP

## Requirements

- Python 3.14
- `uv`

## Install dependencies

```bash
uv sync
```

## Environment variables

Both apps expect the same environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_MANAGER_ID="your-telegram-manager-id"
```

## Run the app without DIP

```bash
uv run uvicorn without_dip.api:app --reload
```

## Run the app with DIP

```bash
uv run uvicorn with_dip.api:app --reload
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "message": "Production is down."
  }'
```

## Development

### Run Ruff checks

```bash
uv run ruff check .
```

### Format with Ruff

```bash
uv run ruff format .
```

### Run mypy

```bash
uv run mypy .
```

### Run pytest

```bash
uv run pytest
```
