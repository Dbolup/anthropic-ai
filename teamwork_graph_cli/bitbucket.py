"""Read-oriented Bitbucket Cloud queries used by the CLI."""
from __future__ import annotations

from .client import AtlassianSession


def list_repositories(session: AtlassianSession, workspace: str) -> list[dict]:
    repos, url = [], f"/repositories/{workspace}"
    params = {"pagelen": 50}
    while url:
        data = session.bitbucket_get(url, params=params)
        repos.extend(data.get("values", []))
        url, params = data.get("next"), None
    return repos


def list_pull_requests(session: AtlassianSession, workspace: str, repo_slug: str, state: str = "OPEN") -> list[dict]:
    prs, url = [], f"/repositories/{workspace}/{repo_slug}/pullrequests"
    params = {"pagelen": 50, "state": state}
    while url:
        data = session.bitbucket_get(url, params=params)
        prs.extend(data.get("values", []))
        url, params = data.get("next"), None
    return prs


def get_pull_request(session: AtlassianSession, workspace: str, repo_slug: str, pr_id: int) -> dict:
    return session.bitbucket_get(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}")


def list_commits(session: AtlassianSession, workspace: str, repo_slug: str, branch: str | None = None) -> list[dict]:
    path = f"/repositories/{workspace}/{repo_slug}/commits"
    if branch:
        path += f"/{branch}"
    commits, url = [], path
    params = {"pagelen": 50}
    while url:
        data = session.bitbucket_get(url, params=params)
        commits.extend(data.get("values", []))
        url, params = data.get("next"), None
    return commits
