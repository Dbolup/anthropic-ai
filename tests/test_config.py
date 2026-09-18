"""
Tests for src/config.py
"""

import os
import pytest
from unittest.mock import patch

from src.config import Config


_REQUIRED_ENV = {
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "JIRA_URL": "https://example.atlassian.net",
    "JIRA_USERNAME": "user@example.com",
    "JIRA_API_TOKEN": "jira-token",
    "GITHUB_TOKEN": "ghp_test",
    "GITHUB_REPO": "owner/repo",
}


def test_config_from_env_success():
    with patch.dict(os.environ, _REQUIRED_ENV, clear=True):
        cfg = Config.from_env()

    assert cfg.anthropic_api_key == "test-anthropic-key"
    assert cfg.jira_url == "https://example.atlassian.net"
    assert cfg.github_repo == "owner/repo"
    assert cfg.github_base_branch == "main"  # default
    assert cfg.claude_model == "claude-opus-4-5"  # default


def test_config_custom_model_and_branch():
    env = {**_REQUIRED_ENV, "CLAUDE_MODEL": "claude-3-5-sonnet-20241022", "GITHUB_BASE_BRANCH": "develop"}
    with patch.dict(os.environ, env, clear=True):
        cfg = Config.from_env()

    assert cfg.claude_model == "claude-3-5-sonnet-20241022"
    assert cfg.github_base_branch == "develop"


def test_config_missing_env_raises():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError, match="Missing required environment variables"):
            Config.from_env()


def test_config_partial_missing_env_raises():
    partial = {k: v for k, v in list(_REQUIRED_ENV.items())[:3]}
    with patch.dict(os.environ, partial, clear=True):
        with pytest.raises(EnvironmentError):
            Config.from_env()
