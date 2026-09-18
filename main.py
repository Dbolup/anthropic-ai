#!/usr/bin/env python3
"""
Entry point for the Claude Agent for Jira + GitHub PR.

Usage:
    python main.py <JIRA_ISSUE_KEY> [--no-jira-comment]

Example:
    python main.py CI-117
    python main.py CI-117 --no-jira-comment
"""

import argparse
import sys

from src.agent import ClaudeAgent
from src.config import Config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Claude Agent: fetch a Jira issue and open a GitHub PR."
    )
    parser.add_argument("issue_key", help="Jira issue key, e.g. CI-117")
    parser.add_argument(
        "--no-jira-comment",
        action="store_true",
        help="Skip posting the PR link as a Jira comment",
    )
    args = parser.parse_args()

    try:
        config = Config.from_env()
    except EnvironmentError as exc:
        print(f"[ERROR] Configuration problem: {exc}", file=sys.stderr)
        sys.exit(1)

    agent = ClaudeAgent(config)

    print(f"[INFO] Processing Jira issue: {args.issue_key}")
    result = agent.run(
        args.issue_key,
        post_jira_comment=not args.no_jira_comment,
    )

    print(f"[OK] Pull request created: {result.pr.url}")
    print(f"     Branch : {result.branch_name}")
    print(f"     PR #   : {result.pr.number}")
    print(f"     Title  : {result.pr.title}")
    print()
    print("Claude's analysis:")
    print(result.analysis)


if __name__ == "__main__":
    main()
