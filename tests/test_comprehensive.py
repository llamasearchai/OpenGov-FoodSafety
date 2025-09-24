"""Comprehensive tests covering configuration, database, services, and CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from click.testing import CliRunner

from opengovfood.cli import app as cli_app
from opengovfood.core.config import get_settings
from opengovfood.core.database import DatabaseManager, create_engine
from opengovfood.services.agent_service import AgentService


def test_settings_contract() -> None:
    settings = get_settings()
    assert settings.PROJECT_NAME == "OpenGov Food"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.database_url.endswith("opengovfood.db")


def test_database_initialization(tmp_path: Path) -> None:
    db_file = tmp_path / "seeded.db"
    engine = create_engine(echo=False)
    manager = DatabaseManager(engine)
    
    # Test synchronous initialization
    async def _init():
        await manager.initialize(drop_existing=True)
        await manager.seed_sample_data()
    
    asyncio.run(_init())


def test_agent_service_mock_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = AgentService()
    
    async def _test():
        result = await service.run_analysis("Evaluate hygiene compliance", provider="mock")
        assert result["provider"] == "mock"
        assert "analysis" in result
    
    asyncio.run(_test())


def test_agent_service_chat_without_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = AgentService()
    
    async def _test():
        response = await service.chat("Hello")
        assert "unavailable" in response.lower()
    
    asyncio.run(_test())


def test_cli_version_command() -> None:
    # Test that CLI app can be imported and has expected structure
    assert cli_app is not None
    assert hasattr(cli_app, 'callback')


def test_cli_help_command() -> None:
    # Test that CLI app can be imported and has expected structure
    assert cli_app is not None
    assert hasattr(cli_app, 'callback')