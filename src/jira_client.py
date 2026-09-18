"""
Jira client wrapper.

Fetches issue details and formats them into a structured dict that the agent
can reason about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from jira import JIRA


@dataclass
class JiraIssue:
    key: str
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    assignee: Optional[str]
    reporter: Optional[str]
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        """Return a human-readable representation suitable for an LLM prompt."""
        lines = [
            f"Jira Issue: {self.key}",
            f"Summary: {self.summary}",
            f"Type: {self.issue_type}",
            f"Priority: {self.priority}",
            f"Status: {self.status}",
            f"Assignee: {self.assignee or 'Unassigned'}",
            f"Reporter: {self.reporter or 'Unknown'}",
        ]
        if self.labels:
            lines.append(f"Labels: {', '.join(self.labels)}")
        if self.components:
            lines.append(f"Components: {', '.join(self.components)}")
        lines.append("")
        lines.append("Description:")
        lines.append(self.description or "(no description provided)")
        return "\n".join(lines)


class JiraClient:
    def __init__(self, url: str, username: str, api_token: str) -> None:
        self._client = JIRA(server=url, basic_auth=(username, api_token))

    def get_issue(self, issue_key: str) -> JiraIssue:
        """Fetch a Jira issue by key (e.g. 'CI-117') and return a JiraIssue."""
        issue = self._client.issue(issue_key)
        fields = issue.fields

        def _account_name(field_value) -> Optional[str]:
            if field_value is None:
                return None
            return getattr(field_value, "displayName", None) or getattr(
                field_value, "name", None
            )

        return JiraIssue(
            key=issue.key,
            summary=fields.summary or "",
            description=fields.description or "",
            issue_type=getattr(fields.issuetype, "name", "Unknown"),
            status=getattr(fields.status, "name", "Unknown"),
            priority=getattr(fields.priority, "name", "Unknown") if fields.priority else "Unknown",
            assignee=_account_name(fields.assignee),
            reporter=_account_name(fields.reporter),
            labels=list(fields.labels or []),
            components=[c.name for c in (fields.components or [])],
        )

    def add_comment(self, issue_key: str, comment: str) -> None:
        """Post a comment to a Jira issue."""
        self._client.add_comment(issue_key, comment)

    def transition_issue(self, issue_key: str, transition_name: str) -> None:
        """Move an issue to a named transition (e.g. 'In Progress')."""
        transitions = self._client.transitions(issue_key)
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                self._client.transition_issue(issue_key, t["id"])
                return
        raise ValueError(
            f"Transition '{transition_name}' not found for issue {issue_key}. "
            f"Available: {[t['name'] for t in transitions]}"
        )
