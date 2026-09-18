"""
Core Claude Agent.

Orchestrates the end-to-end flow:
  1. Fetch Jira issue details.
  2. Ask Claude to analyse the issue and produce a plan + PR artefacts.
  3. Create a GitHub branch, commit placeholder/implementation files.
  4. Open a pull request.
  5. (Optionally) post a comment back to the Jira issue.
"""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass
from typing import Any

import anthropic

from .config import Config
from .github_client import GitHubClient, PullRequestResult
from .jira_client import JiraClient, JiraIssue


# ---------------------------------------------------------------------------
# Data classes returned to callers
# ---------------------------------------------------------------------------


@dataclass
class AgentResult:
    jira_key: str
    pr: PullRequestResult
    branch_name: str
    analysis: str


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert software engineer and technical lead.
    You will be given a Jira work item and must:
      1. Briefly analyse the issue (2-4 sentences).
      2. Propose a concrete implementation plan (bullet points).
      3. Suggest a short, kebab-case Git branch name (no spaces) without
         any prefix like "feature/" — the caller adds the prefix.
      4. Write a GitHub pull-request title (≤72 characters).
      5. Write a detailed GitHub pull-request description in Markdown.
      6. Output ONLY valid JSON matching this schema — no prose outside JSON:

    {
      "analysis": "<string>",
      "implementation_plan": ["<step>", ...],
      "branch_slug": "<kebab-case-slug>",
      "pr_title": "<string>",
      "pr_description": "<markdown string>"
    }
    """
).strip()


def _build_user_prompt(issue: JiraIssue) -> str:
    return f"Please analyse the following Jira issue and respond with JSON:\n\n{issue.to_prompt_text()}"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class ClaudeAgent:
    """Main agent that ties Jira, Claude, and GitHub together."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._claude = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._jira = JiraClient(
            url=config.jira_url,
            username=config.jira_username,
            api_token=config.jira_api_token,
        )
        self._github = GitHubClient(
            token=config.github_token,
            repo_full_name=config.github_repo,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, jira_issue_key: str, *, post_jira_comment: bool = True) -> AgentResult:
        """
        Full pipeline: Jira → Claude → GitHub PR.

        Parameters
        ----------
        jira_issue_key:
            e.g. ``"CI-117"``
        post_jira_comment:
            When *True*, post the PR link back as a Jira comment.
        """
        # 1. Fetch Jira issue
        issue = self._jira.get_issue(jira_issue_key)

        # 2. Ask Claude to analyse the issue
        plan = self._ask_claude(issue)

        # 3. Create GitHub branch
        desired_slug = self._sanitize_slug(plan["branch_slug"])
        desired_branch = f"claude/{jira_issue_key.upper()}/{desired_slug}"
        branch_name = self._github.unique_branch_name(desired_branch)
        self._github.create_branch(branch_name, self._config.github_base_branch)

        # 4. Commit a summary / notes file to the branch so the PR has a diff
        notes_path = f"docs/{jira_issue_key.lower()}-implementation-notes.md"
        notes_content = self._build_notes_file(issue, plan)
        self._github.create_or_update_file(
            path=notes_path,
            content=notes_content,
            commit_message=f"{jira_issue_key} Add implementation notes",
            branch=branch_name,
        )

        # 5. Open pull request
        pr_body = self._build_pr_body(plan, jira_issue_key)
        pr = self._github.create_pull_request(
            title=f"{jira_issue_key} {plan['pr_title']}",
            body=pr_body,
            head_branch=branch_name,
            base_branch=self._config.github_base_branch,
        )

        # 6. Optionally comment on the Jira issue
        if post_jira_comment:
            self._jira.add_comment(
                jira_issue_key,
                f"🤖 Claude Agent opened a pull request:\n{pr.url}",
            )

        return AgentResult(
            jira_key=jira_issue_key,
            pr=pr,
            branch_name=branch_name,
            analysis=plan["analysis"],
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ask_claude(self, issue: JiraIssue) -> dict[str, Any]:
        """Call Claude and parse the JSON response."""
        message = self._claude.messages.create(
            model=self._config.claude_model,
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(issue)}],
        )
        raw = message.content[0].text
        # Strip markdown code fences if Claude wraps the JSON
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw.strip())
        return json.loads(raw)

    @staticmethod
    def _sanitize_slug(slug: str) -> str:
        """Ensure the slug is safe for use as a branch name component."""
        slug = slug.lower().strip()
        slug = re.sub(r"[^a-z0-9\-]", "-", slug)
        slug = re.sub(r"-{2,}", "-", slug)
        return slug.strip("-") or "feature"

    @staticmethod
    def _build_notes_file(issue: JiraIssue, plan: dict[str, Any]) -> str:
        steps = "\n".join(f"- {s}" for s in plan.get("implementation_plan", []))
        return textwrap.dedent(
            f"""
            # Implementation Notes — {issue.key}

            ## Issue Summary
            {issue.summary}

            ## Analysis
            {plan['analysis']}

            ## Implementation Plan
            {steps}
            """
        ).lstrip()

    @staticmethod
    def _build_pr_body(plan: dict[str, Any], jira_key: str) -> str:
        description = plan.get("pr_description", "")
        return (
            f"{description}\n\n"
            f"---\n"
            f"Key: {jira_key}\n\n"
            f"Co-authored by Claude agent for Jira."
        )
