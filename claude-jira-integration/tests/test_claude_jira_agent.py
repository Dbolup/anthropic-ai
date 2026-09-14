"""
Tests for the Claude → Jira agent helper functions.

Run with:  pytest tests/test_claude_jira_agent.py -v
"""

import sys
import os
import types

import pytest

# ---------------------------------------------------------------------------
# Stub out heavy optional dependencies so tests run without them installed
# ---------------------------------------------------------------------------

for mod_name in ("anthropic", "jira", "github"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

# Provide minimal stubs that the module-level imports resolve against
sys.modules["jira"].JIRA = object
sys.modules["github"].Github = object
sys.modules["github"].GithubException = Exception

# Set required env vars before importing the agent module
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("JIRA_SERVER", "https://example.atlassian.net")
os.environ.setdefault("JIRA_EMAIL", "bot@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "test-token")
os.environ.setdefault("GITHUB_TOKEN", "test-gh-token")
os.environ.setdefault("CLAUDE_JIRA_USER", "claude-bot")

# Now import the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from claude_jira_agent import extract_github_repo  # noqa: E402


# ---------------------------------------------------------------------------
# Tests for extract_github_repo
# ---------------------------------------------------------------------------

class TestExtractGithubRepo:
    def test_plain_url(self):
        desc = "See https://github.com/Dbolup/anthropic-ai for details."
        assert extract_github_repo(desc) == "https://github.com/Dbolup/anthropic-ai"

    def test_url_with_path(self):
        desc = "Repo: https://github.com/org/my-repo and more text."
        assert extract_github_repo(desc) == "https://github.com/org/my-repo"

    def test_no_url_returns_none(self):
        assert extract_github_repo("No link here.") is None

    def test_empty_description(self):
        assert extract_github_repo("") is None

    def test_none_description(self):
        assert extract_github_repo(None) is None

    def test_url_with_hyphens_and_dots(self):
        desc = "https://github.com/my-org/my.repo.name"
        assert extract_github_repo(desc) == "https://github.com/my-org/my.repo.name"

    def test_first_url_returned_when_multiple(self):
        desc = (
            "Primary: https://github.com/org/repo-a, "
            "secondary: https://github.com/org/repo-b"
        )
        assert extract_github_repo(desc) == "https://github.com/org/repo-a"
