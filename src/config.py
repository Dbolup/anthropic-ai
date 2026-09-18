"""
Configuration management for Claude Agent for Jira + GitHub PR.

Loads settings from environment variables (or a .env file).
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Anthropic / Claude
    anthropic_api_key: str
    claude_model: str

    # Jira
    jira_url: str
    jira_username: str
    jira_api_token: str

    # GitHub
    github_token: str
    github_repo: str          # "owner/repo"
    github_base_branch: str   # branch to open PRs against, e.g. "main"

    @classmethod
    def from_env(cls) -> "Config":
        missing = []

        def require(key: str) -> str:
            val = os.getenv(key)
            if not val:
                missing.append(key)
            return val or ""

        cfg = cls(
            anthropic_api_key=require("ANTHROPIC_API_KEY"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-4-5"),
            jira_url=require("JIRA_URL"),
            jira_username=require("JIRA_USERNAME"),
            jira_api_token=require("JIRA_API_TOKEN"),
            github_token=require("GITHUB_TOKEN"),
            github_repo=require("GITHUB_REPO"),
            github_base_branch=os.getenv("GITHUB_BASE_BRANCH", "main"),
        )

        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cfg
