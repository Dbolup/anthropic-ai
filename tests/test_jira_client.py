"""
Tests for src/jira_client.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.jira_client import JiraClient, JiraIssue


def _make_mock_issue(
    key="CI-117",
    summary="Test summary",
    description="Test description",
    issue_type="Story",
    status="Open",
    priority="Medium",
    assignee_name="Alice",
    reporter_name="Bob",
    labels=None,
    components=None,
):
    issue = MagicMock()
    issue.key = key
    fields = MagicMock()
    fields.summary = summary
    fields.description = description
    fields.issuetype.name = issue_type
    fields.status.name = status
    fields.priority.name = priority
    fields.assignee.displayName = assignee_name
    fields.reporter.displayName = reporter_name
    fields.labels = labels or []
    component_mocks = []
    for name in (components or []):
        c = MagicMock()
        c.name = name
        component_mocks.append(c)
    fields.components = component_mocks
    issue.fields = fields
    return issue


@patch("src.jira_client.JIRA")
def test_get_issue_basic(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.issue.return_value = _make_mock_issue()

    client = JiraClient("https://test.atlassian.net", "user", "token")
    result = client.get_issue("CI-117")

    assert isinstance(result, JiraIssue)
    assert result.key == "CI-117"
    assert result.summary == "Test summary"
    assert result.description == "Test description"
    assert result.issue_type == "Story"
    assert result.status == "Open"
    assert result.priority == "Medium"
    assert result.assignee == "Alice"
    assert result.reporter == "Bob"


@patch("src.jira_client.JIRA")
def test_get_issue_with_labels_and_components(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.issue.return_value = _make_mock_issue(
        labels=["backend", "urgent"],
        components=["API", "Auth"],
    )

    client = JiraClient("https://test.atlassian.net", "user", "token")
    result = client.get_issue("CI-117")

    assert result.labels == ["backend", "urgent"]
    assert result.components == ["API", "Auth"]


@patch("src.jira_client.JIRA")
def test_get_issue_no_assignee(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    issue = _make_mock_issue()
    issue.fields.assignee = None
    mock_jira.issue.return_value = issue

    client = JiraClient("https://test.atlassian.net", "user", "token")
    result = client.get_issue("CI-117")
    assert result.assignee is None


def test_jira_issue_to_prompt_text():
    issue = JiraIssue(
        key="CI-1",
        summary="Build the agent",
        description="Full details here.",
        issue_type="Task",
        status="In Progress",
        priority="High",
        assignee="Charlie",
        reporter="Dave",
        labels=["ml"],
        components=["Core"],
    )
    text = issue.to_prompt_text()

    assert "CI-1" in text
    assert "Build the agent" in text
    assert "Full details here." in text
    assert "ml" in text
    assert "Core" in text


def test_jira_issue_to_prompt_text_no_optional_fields():
    issue = JiraIssue(
        key="CI-2",
        summary="Minimal",
        description="",
        issue_type="Bug",
        status="Open",
        priority="Low",
        assignee=None,
        reporter=None,
    )
    text = issue.to_prompt_text()
    assert "Unassigned" in text
    assert "no description" in text


@patch("src.jira_client.JIRA")
def test_add_comment(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira

    client = JiraClient("https://test.atlassian.net", "user", "token")
    client.add_comment("CI-117", "Hello from the agent")

    mock_jira.add_comment.assert_called_once_with("CI-117", "Hello from the agent")


@patch("src.jira_client.JIRA")
def test_transition_issue_success(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.transitions.return_value = [
        {"id": "10", "name": "In Progress"},
        {"id": "20", "name": "Done"},
    ]

    client = JiraClient("https://test.atlassian.net", "user", "token")
    client.transition_issue("CI-117", "In Progress")

    mock_jira.transition_issue.assert_called_once_with("CI-117", "10")


@patch("src.jira_client.JIRA")
def test_transition_issue_not_found(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.transitions.return_value = [{"id": "10", "name": "Done"}]

    client = JiraClient("https://test.atlassian.net", "user", "token")
    with pytest.raises(ValueError, match="not found"):
        client.transition_issue("CI-117", "Review")
