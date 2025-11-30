import pytest
from unittest.mock import patch
import os


class TestAppliersConfig:
    """Tests for appliers_config.py functions."""

    def test_process_for_providers_filters_provider_portals(self):
        """Test that process_for_providers keeps only provider portal applications."""
        from app.core.appliers_config import process_for_providers

        data = {
            "user_id": 123,
            "content": {
                "app1": {"portal": "workday", "title": "Job 1"},
                "app2": {"portal": "greenhouse", "title": "Job 2"},
                "app3": {"portal": "unknown_portal", "title": "Job 3"},
            }
        }

        result = process_for_providers(data)

        assert result is not None
        assert result["user_id"] == 123
        assert "app1" in result["content"]
        assert "app2" in result["content"]
        assert "app3" not in result["content"]

    def test_process_for_providers_returns_none_when_no_matches(self):
        """Test that process_for_providers returns None when no portals match."""
        from app.core.appliers_config import process_for_providers

        data = {
            "user_id": 123,
            "content": {
                "app1": {"portal": "unknown_portal", "title": "Job 1"},
            }
        }

        result = process_for_providers(data)
        assert result is None

    def test_process_for_skyvern_filters_non_provider_portals(self):
        """Test that process_for_skyvern keeps non-provider portal applications."""
        from app.core.appliers_config import process_for_skyvern

        data = {
            "user_id": 123,
            "content": {
                "app1": {"portal": "workday", "title": "Job 1"},
                "app2": {"portal": "unknown_portal", "title": "Job 2"},
                "app3": {"portal": "custom_site", "title": "Job 3"},
            }
        }

        result = process_for_skyvern(data)

        assert result is not None
        assert result["user_id"] == 123
        assert "app1" not in result["content"]
        assert "app2" in result["content"]
        assert "app3" in result["content"]

    def test_process_for_skyvern_returns_none_when_no_matches(self):
        """Test that process_for_skyvern returns None when all portals are providers."""
        from app.core.appliers_config import process_for_skyvern

        data = {
            "user_id": 123,
            "content": {
                "app1": {"portal": "workday", "title": "Job 1"},
                "app2": {"portal": "greenhouse", "title": "Job 2"},
            }
        }

        result = process_for_skyvern(data)
        assert result is None

    def test_process_default_returns_data_unchanged(self):
        """Test that process_default returns data as-is."""
        from app.core.appliers_config import process_default

        data = {"user_id": 123, "content": {"app1": {"title": "Job"}}}
        result = process_default(data)
        assert result == data

    def test_process_for_providers_handles_invalid_content(self):
        """Test that process_for_providers handles non-dict content gracefully."""
        from app.core.appliers_config import process_for_providers

        data = {"user_id": 123, "content": "invalid"}
        result = process_for_providers(data)
        assert result == {"user_id": 123, "content": {}}

    def test_process_for_skyvern_handles_invalid_content(self):
        """Test that process_for_skyvern handles non-dict content gracefully."""
        from app.core.appliers_config import process_for_skyvern

        data = {"user_id": 123, "content": "invalid"}
        result = process_for_skyvern(data)
        assert result == {"user_id": 123, "content": {}}


class TestAppliersConfigEnvironment:
    """Tests for environment-based APPLIERS configuration."""

    def test_default_config_has_providers_enabled(self):
        """Test that providers applier is enabled by default."""
        # Need to reload the module to get fresh config
        import importlib
        import app.core.appliers_config as config_module

        with patch.dict(os.environ, {}, clear=True):
            importlib.reload(config_module)
            assert 'providers' in config_module.APPLIERS
            assert 'skyvern' not in config_module.APPLIERS

    def test_skyvern_enabled_via_env(self):
        """Test that Skyvern can be enabled via environment variable."""
        import importlib
        import app.core.appliers_config as config_module

        with patch.dict(os.environ, {"ENABLE_SKYVERN_APPLIER": "true"}, clear=False):
            importlib.reload(config_module)
            assert 'skyvern' in config_module.APPLIERS

    def test_providers_disabled_via_env(self):
        """Test that providers can be disabled via environment variable."""
        import importlib
        import app.core.appliers_config as config_module

        with patch.dict(os.environ, {"ENABLE_PROVIDERS_APPLIER": "false"}, clear=False):
            importlib.reload(config_module)
            assert 'providers' not in config_module.APPLIERS
