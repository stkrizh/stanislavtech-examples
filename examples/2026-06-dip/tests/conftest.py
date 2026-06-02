import sys
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def configure_without_dip_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-telegram-bot-token")
    monkeypatch.setenv("TELEGRAM_MANAGER_ID", "test-manager-id")
    sys.modules.pop("without_dip.api", None)
    yield
    sys.modules.pop("without_dip.api", None)
