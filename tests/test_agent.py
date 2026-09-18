"""
Tests for src/agent.py
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agent import ClaudeAgent, AgentResult
from src.config import Config
from src.jira_client import JiraIssue
from src.github_client import PullRequestResult


_MOCK_PLAN = {
    "analysis": "This issue requires building a Claude-based agent.",
    "implementation_plan": ["Step 1: Set up project", "Step 2: Implement agent"],
    "branch_slug": "build-claude-agent",
    "pr_title": "Build Claude Agent for Jira PR automation",
    "pr_description": "## Overview\nThis PR introduces the Claude Agent.",
}

_MOCK_ISSUE = JiraIssue(
    key="CI-117",
    summary="Claude Agent for Jira for GitHub PR",
    description="Build an agent that integrates Jira and GitHub.",
    issue_type="Story",
    status="Open",
    priority="High",
    assignee="Alice",
    reporter="Bob",
)

_MOCK_PR = PullRequestResult(
    number=7,
    url="https://github.com/owner/repo/pull/7",
    title="CI-117 Build Claude Agent for Jira PR automation",
    head_branch="claude/CI-117/build-claude-agent",
    base_branch="main",
)


def _make_config() -> Config:
    return Config(
        anthropic_api_key="test-key",
        claude_model="claude-opus-4-5",
        jira_url="https://example.atlassian.net",
        jira_username="user@example.com",
        jira_api_token="jira-token",
        github_token="ghp_test",
        github_repo="owner/repo",
        github_base_branch="main",
    )


@patch("src.agent.GitHubClient")
@patch("src.agent.JiraClient")
@patch("src.agent.anthropic.Anthropic")
def test_agent_run_success(mock_anthropic_cls, mock_jira_cls, mock_gh_cls):
    # Setup Claude mock
    mock_anthropic = MagicMock()
    mock_anthropic_cls.return_value = mock_anthropic
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(_MOCK_PLAN))]
    mock_anthropic.messages.create.return_value = mock_message

    # Setup Jira mock
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.get_issue.return_value = _MOCK_ISSUE

    # Setup GitHub mock
    mock_gh = MagicMock()
    mock_gh_cls.return_value = mock_gh
    mock_gh.unique_branch_name.return_value = "claude/CI-117/build-claude-agent"
    mock_gh.create_pull_request.return_value = _MOCK_PR

    agent = ClaudeAgent(_make_config())
    result = agent.run("CI-117", post_jira_comment=True)

    # Assertions
    assert isinstance(result, AgentResult)
    assert result.jira_key == "CI-117"
    assert result.pr.number == 7
    assert result.branch_name == "claude/CI-117/build-claude-agent"
    assert "Claude-based agent" in result.analysis

    mock_jira.get_issue.assert_called_once_with("CI-117")
    mock_gh.create_branch.assert_called_once()
    mock_gh.create_or_update_file.assert_called_once()
    mock_gh.create_pull_request.assert_called_once()
    mock_jira.add_comment.assert_called_once()


@patch("src.agent.GitHubClient")
@patch("src.agent.JiraClient")
@patch("src.agent.anthropic.Anthropic")
def test_agent_run_no_jira_comment(mock_anthropic_cls, mock_jira_cls, mock_gh_cls):
    mock_anthropic = MagicMock()
    mock_anthropic_cls.return_value = mock_anthropic
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(_MOCK_PLAN))]
    mock_anthropic.messages.create.return_value = mock_message

    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.get_issue.return_value = _MOCK_ISSUE

    mock_gh = MagicMock()
    mock_gh_cls.return_value = mock_gh
    mock_gh.unique_branch_name.return_value = "claude/CI-117/build-claude-agent"
    mock_gh.create_pull_request.return_value = _MOCK_PR

    agent = ClaudeAgent(_make_config())
    agent.run("CI-117", post_jira_comment=False)

    mock_jira.add_comment.assert_not_called()


@patch("src.agent.GitHubClient")
@patch("src.agent.JiraClient")
@patch("src.agent.anthropic.Anthropic")
def test_agent_handles_json_wrapped_in_code_fences(mock_anthropic_cls, mock_jira_cls, mock_gh_cls):
    mock_anthropic = MagicMock()
    mock_anthropic_cls.return_value = mock_anthropic
    fenced = f"```json\n{json.dumps(_MOCK_PLAN)}\n```"
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=fenced)]
    mock_anthropic.messages.create.return_value = mock_message

    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.get_issue.return_value = _MOCK_ISSUE

    mock_gh = MagicMock()
    mock_gh_cls.return_value = mock_gh
    mock_gh.unique_branch_name.return_value = "claude/CI-117/build-claude-agent"
    mock_gh.create_pull_request.return_value = _MOCK_PR

    agent = ClaudeAgent(_make_config())
    result = agent.run("CI-117", post_jira_comment=False)
    assert result.analysis == _MOCK_PLAN["analysis"]


def test_sanitize_slug_basic():
    assert ClaudeAgent._sanitize_slug("my feature slug") == "my-feature-slug"


def test_sanitize_slug_special_chars():
    # Special characters become dashes which are then collapsed
    assert ClaudeAgent._sanitize_slug("Hello World! #1") == "hello-world-1"


def test_sanitize_slug_collapses_dashes():
    result = ClaudeAgent._sanitize_slug("hello---world")
    assert result == "hello-world"


def test_sanitize_slug_empty_falls_back():
    assert ClaudeAgent._sanitize_slug("!!!") == "feature"


def test_build_notes_file_contains_key_sections():
    notes = ClaudeAgent._build_notes_file(_MOCK_ISSUE, _MOCK_PLAN)
    assert "CI-117" in notes
    assert "Claude Agent for Jira for GitHub PR" in notes
    assert "Step 1" in notes
    assert "Step 2" in notes


def test_build_pr_body_contains_key_and_attribution():
    body = ClaudeAgent._build_pr_body(_MOCK_PLAN, "CI-117")
    assert "Key: CI-117" in body
    assert "Co-authored by Claude agent for Jira" in body
    assert "## Overview" in body
