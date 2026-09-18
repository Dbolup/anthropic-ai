"""Configuration and token storage for the Teamwork Graph CLI.

Credentials are read from environment variables so no secrets live in the
repo. Tokens obtained via OAuth are cached on disk with owner-only
permissions so repeated commands don't re-open a browser every time.
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

AUTH_BASE_URL = "https://auth.atlassian.com"
API_BASE_URL = "https://api.atlassian.com"

# Bitbucket needs repository read/write style scopes; JSM needs the
# service-desk scopes. Jira/Confluence scopes are intentionally left out
# since those are already reachable through the Atlassian Rovo MCP server.
DEFAULT_SCOPES = [
    "read:repository:bitbucket",
    "read:pullrequest:bitbucket",
    "read:pipeline:bitbucket",
    "read:jira-work",
    "read:servicedesk-request",
    "manage:servicedesk-request",
    "offline_access",
]

CONFIG_DIR = Path(os.environ.get("TEAMWORK_GRAPH_CONFIG_DIR", Path.home() / ".config" / "teamwork-graph-cli"))
TOKEN_PATH = CONFIG_DIR / "credentials.json"


@dataclass
class OAuthAppConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]

    @classmethod
    def from_env(cls) -> "OAuthAppConfig":
        client_id = os.environ.get("ATLASSIAN_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("ATLASSIAN_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise SystemExit(
                "Missing ATLASSIAN_OAUTH_CLIENT_ID / ATLASSIAN_OAUTH_CLIENT_SECRET.\n"
                "Create an OAuth 2.0 (3LO) app at https://developer.atlassian.com/console/myapps/\n"
                "with the Bitbucket and Jira Service Management APIs enabled, then export both "
                "variables before running this CLI."
            )
        redirect_uri = os.environ.get("ATLASSIAN_OAUTH_REDIRECT_URI", "http://localhost:8765/callback")
        scopes_env = os.environ.get("ATLASSIAN_OAUTH_SCOPES")
        scopes = scopes_env.split() if scopes_env else DEFAULT_SCOPES
        return cls(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scopes=scopes)


def load_tokens() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    return json.loads(TOKEN_PATH.read_text())


def save_tokens(tokens: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(tokens, indent=2))
    os.chmod(TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)


def clear_tokens() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
