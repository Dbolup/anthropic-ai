#!/usr/bin/env python3
"""
claude_jira_agent.py

Minimal reference implementation of the Claude → Jira integration.

This script demonstrates how Claude picks up a Jira ticket assigned to it,
analyses the description, and creates a GitHub Pull Request.

Dependencies:
    pip install anthropic jira PyGithub

Environment variables required:
    ANTHROPIC_API_KEY   - Anthropic API key
    JIRA_SERVER         - e.g. https://yourcompany.atlassian.net
    JIRA_EMAIL          - Jira user email
    JIRA_API_TOKEN      - Jira API token
    GITHUB_TOKEN        - GitHub personal access token (repo write scope)
    CLAUDE_JIRA_USER    - Jira username/accountId that represents Claude
"""

import os
import sys
import time
import logging

import anthropic
from jira import JIRA
from github import Github, GithubException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (loaded from environment)
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
JIRA_SERVER = os.environ["JIRA_SERVER"]
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
CLAUDE_JIRA_USER = os.environ["CLAUDE_JIRA_USER"]

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))


# ---------------------------------------------------------------------------
# Jira helpers
# ---------------------------------------------------------------------------

def connect_jira() -> JIRA:
    return JIRA(
        server=JIRA_SERVER,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
    )


def get_tickets_assigned_to_claude(jira: JIRA) -> list:
    """Return open Jira issues currently assigned to the Claude agent user."""
    jql = f'assignee = "{CLAUDE_JIRA_USER}" AND statusCategory != Done ORDER BY updated DESC'
    return jira.search_issues(jql, maxResults=10)


def extract_github_repo(description: str) -> str | None:
    """Parse the first GitHub repository URL from a Jira issue description."""
    import re
    match = re.search(r"https://github\.com/[\w.\-]+/[\w.\-]+", description or "")
    return match.group(0) if match else None


# ---------------------------------------------------------------------------
# Claude helper
# ---------------------------------------------------------------------------

def ask_claude(system_prompt: str, user_message: str) -> str:
    """Send a message to Claude and return the text response."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def get_or_create_branch(repo, branch_name: str, base_branch: str = "main"):
    """Create a new branch from base_branch if it does not already exist."""
    try:
        repo.get_branch(branch_name)
        log.info("Branch %s already exists", branch_name)
    except GithubException:
        base = repo.get_branch(base_branch)
        repo.create_git_ref(f"refs/heads/{branch_name}", base.commit.sha)
        log.info("Created branch %s from %s", branch_name, base_branch)


def open_draft_pr(repo, branch_name: str, title: str, body: str) -> str:
    """Open a draft pull request and return its HTML URL."""
    pr = repo.create_pull(
        title=title,
        body=body,
        head=branch_name,
        base=repo.default_branch,
        draft=True,
    )
    return pr.html_url


# ---------------------------------------------------------------------------
# Core agent loop
# ---------------------------------------------------------------------------

def process_ticket(jira: JIRA, issue) -> None:
    """Analyse a single Jira ticket and create a GitHub PR."""
    key = issue.key
    summary = issue.fields.summary
    description = getattr(issue.fields, "description", "") or ""

    log.info("Processing ticket %s: %s", key, summary)

    # 1. Extract the GitHub repo from the description
    repo_url = extract_github_repo(description)
    if not repo_url:
        log.warning("No GitHub repo URL found in %s — skipping", key)
        return

    repo_path = repo_url.removeprefix("https://github.com/")  # e.g. "Dbolup/anthropic-ai"

    # 2. Ask Claude what changes to make
    system_prompt = (
        "You are an expert software engineer. "
        "Given a Jira ticket, describe the minimal code changes needed "
        "to fulfil the requirements. Be concise and specific."
    )
    user_message = (
        f"Jira ticket {key}: {summary}\n\n"
        f"Description:\n{description}\n\n"
        "What changes should be made to the GitHub repository to fulfil this ticket?"
    )
    plan = ask_claude(system_prompt, user_message)
    log.info("Claude's plan for %s:\n%s", key, plan)

    # 3. Create the feature branch
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(repo_path)

    slug = summary.lower().replace(" ", "-")[:40]
    branch_name = f"claude/{key}/{slug}"
    get_or_create_branch(repo, branch_name)

    # 4. Commit Claude's plan as a markdown file (placeholder for real code changes)
    file_path = f"claude-plans/{key}.md"
    file_content = f"# {key}: {summary}\n\n## Claude's Implementation Plan\n\n{plan}\n"
    commit_message = f"{key} {summary}"

    try:
        existing = repo.get_contents(file_path, ref=branch_name)
        repo.update_file(file_path, commit_message, file_content, existing.sha, branch=branch_name)
    except GithubException:
        repo.create_file(file_path, commit_message, file_content, branch=branch_name)

    log.info("Committed plan for %s to branch %s", key, branch_name)

    # 5. Open a Draft PR
    pr_title = f"{key} {summary}"
    pr_body = (
        f"## Summary\n\n{plan}\n\n"
        f"---\n\nKey: {key}\n"
        "Co-authored by Claude agent for Jira."
    )
    pr_url = open_draft_pr(repo, branch_name, pr_title, pr_body)
    log.info("Opened Draft PR for %s: %s", key, pr_url)

    # 6. Add a comment on the Jira ticket with the PR link
    jira.add_comment(key, f"Claude has opened a Draft Pull Request: {pr_url}")


def run_poll_loop() -> None:
    """Continuously poll Jira for tickets assigned to Claude and process them."""
    jira = connect_jira()
    processed: set[str] = set()

    log.info("Claude Jira Agent started — polling every %ds", POLL_INTERVAL_SECONDS)

    while True:
        try:
            tickets = get_tickets_assigned_to_claude(jira)
            for issue in tickets:
                if issue.key not in processed:
                    process_ticket(jira, issue)
                    processed.add(issue.key)
        except Exception as exc:  # noqa: BLE001
            log.error("Error during poll cycle: %s", exc)

        time.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_poll_loop()
    except KeyboardInterrupt:
        log.info("Agent stopped.")
        sys.exit(0)
