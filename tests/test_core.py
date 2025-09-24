"""Tests for OpenFood."""

import pytest

from opengovfood.core.config import Settings
from opengovfood.core.database import DatabaseManager


def test_settings():
    """Test settings configuration."""
    settings = Settings()
    assert settings.PROJECT_NAME == "OpenGov Food"
    assert settings.APP_VERSION == "1.0.0"


def test_database_manager():
    """Test database manager."""
    manager = DatabaseManager()
    assert manager.engine is not None

