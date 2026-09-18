"""
Tests for src/github_client.py
"""

from unittest.mock import MagicMock, patch, call

import pytest
from github import GithubException

from src.github_client import GitHubClient, PullRequestResult


def _make_client(repo_name="owner/repo"):
    with patch("src.github_client.Github") as mock_gh_cls:
        mock_gh = MagicMock()
        mock_gh_cls.return_value = mock_gh
        mock_repo = MagicMock()
        mock_gh.get_repo.return_value = mock_repo
        client = GitHubClient("ghp_test", repo_name)
        return client, mock_repo


def test_branch_exists_true():
    client, mock_repo = _make_client()
    mock_repo.get_branch.return_value = MagicMock()
    assert client.branch_exists("feature/x") is True


def test_branch_exists_false():
    client, mock_repo = _make_client()
    mock_repo.get_branch.side_effect = GithubException(404, {}, {})
    assert client.branch_exists("feature/x") is False


def test_create_branch_success():
    client, mock_repo = _make_client()
    base = MagicMock()
    base.commit.sha = "abc123"

    # branch_exists returns False first (new branch), then returns base
    mock_repo.get_branch.side_effect = [GithubException(404, {}, {}), base]

    client.create_branch("new-branch", "main")

    mock_repo.create_git_ref.assert_called_once_with(
        ref="refs/heads/new-branch", sha="abc123"
    )


def test_create_branch_already_exists_raises():
    client, mock_repo = _make_client()
    mock_repo.get_branch.return_value = MagicMock()  # already exists

    with pytest.raises(ValueError, match="already exists"):
        client.create_branch("existing-branch", "main")


def test_unique_branch_name_no_conflict():
    client, mock_repo = _make_client()
    mock_repo.get_branch.side_effect = GithubException(404, {}, {})
    assert client.unique_branch_name("claude/CI-1/my-feature") == "claude/CI-1/my-feature"


def test_unique_branch_name_with_conflict():
    client, mock_repo = _make_client()
    existing = MagicMock()
    # First call (exact name) exists, second call (-1) exists, third (-2) does not
    mock_repo.get_branch.side_effect = [existing, existing, GithubException(404, {}, {})]
    result = client.unique_branch_name("claude/CI-1/slug")
    assert result == "claude/CI-1/slug-2"


def test_create_or_update_file_create():
    client, mock_repo = _make_client()
    mock_repo.get_contents.side_effect = GithubException(404, {}, {})

    client.create_or_update_file("path/file.md", "content", "Add file", "branch")

    mock_repo.create_file.assert_called_once_with(
        path="path/file.md",
        message="Add file",
        content="content",
        branch="branch",
    )


def test_create_or_update_file_update():
    client, mock_repo = _make_client()
    existing = MagicMock()
    existing.sha = "filsha"
    mock_repo.get_contents.return_value = existing

    client.create_or_update_file("path/file.md", "new content", "Update file", "branch")

    mock_repo.update_file.assert_called_once_with(
        path="path/file.md",
        message="Update file",
        content="new content",
        sha="filsha",
        branch="branch",
    )


def test_create_pull_request():
    client, mock_repo = _make_client()
    mock_pr = MagicMock()
    mock_pr.number = 42
    mock_pr.html_url = "https://github.com/owner/repo/pull/42"
    mock_pr.title = "CI-117 My PR"
    mock_repo.create_pull.return_value = mock_pr

    result = client.create_pull_request(
        title="CI-117 My PR",
        body="Description",
        head_branch="claude/CI-117/slug",
        base_branch="main",
    )

    assert isinstance(result, PullRequestResult)
    assert result.number == 42
    assert result.url == "https://github.com/owner/repo/pull/42"
    assert result.head_branch == "claude/CI-117/slug"
    assert result.base_branch == "main"


def test_get_default_branch():
    client, mock_repo = _make_client()
    mock_repo.default_branch = "develop"
    assert client.get_default_branch() == "develop"
