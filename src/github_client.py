"""
GitHub client wrapper.

Creates branches and pull requests on behalf of the agent.
"""

from __future__ import annotations

from dataclasses import dataclass

from github import Github, GithubException
from github.Repository import Repository


@dataclass
class PullRequestResult:
    number: int
    url: str
    title: str
    head_branch: str
    base_branch: str


class GitHubClient:
    def __init__(self, token: str, repo_full_name: str) -> None:
        self._gh = Github(token)
        self._repo: Repository = self._gh.get_repo(repo_full_name)

    # ------------------------------------------------------------------
    # Branch helpers
    # ------------------------------------------------------------------

    def branch_exists(self, branch_name: str) -> bool:
        try:
            self._repo.get_branch(branch_name)
            return True
        except GithubException:
            return False

    def create_branch(self, branch_name: str, base_branch: str) -> None:
        """Create a new branch off *base_branch*."""
        if self.branch_exists(branch_name):
            raise ValueError(f"Branch '{branch_name}' already exists.")
        base_ref = self._repo.get_branch(base_branch)
        self._repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_ref.commit.sha,
        )

    def unique_branch_name(self, desired: str) -> str:
        """Return *desired* (or *desired-N*) guaranteed not to exist yet."""
        if not self.branch_exists(desired):
            return desired
        counter = 1
        while True:
            candidate = f"{desired}-{counter}"
            if not self.branch_exists(candidate):
                return candidate
            counter += 1

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def create_or_update_file(
        self,
        path: str,
        content: str,
        commit_message: str,
        branch: str,
    ) -> None:
        """Create or overwrite a file on *branch*."""
        try:
            existing = self._repo.get_contents(path, ref=branch)
            self._repo.update_file(
                path=path,
                message=commit_message,
                content=content,
                sha=existing.sha,
                branch=branch,
            )
        except GithubException:
            self._repo.create_file(
                path=path,
                message=commit_message,
                content=content,
                branch=branch,
            )

    # ------------------------------------------------------------------
    # Pull-request helpers
    # ------------------------------------------------------------------

    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        draft: bool = False,
    ) -> PullRequestResult:
        """Open a pull request and return its details."""
        pr = self._repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch,
            draft=draft,
        )
        return PullRequestResult(
            number=pr.number,
            url=pr.html_url,
            title=pr.title,
            head_branch=head_branch,
            base_branch=base_branch,
        )

    def get_default_branch(self) -> str:
        return self._repo.default_branch
