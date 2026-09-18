"""Configuration and token storage for the Teamwork Graph CLI.

Bitbucket Cloud and Jira Service Management (JSM) are NOT reachable through
one unified Atlassian OAuth app: JSM rides on the Jira Cloud platform and is
authorized as part of the "Jira API" scopes in the same 3LO app used for
Jira/Confluence, but Bitbucket Cloud uses its own, separate OAuth consumer
system (registered from a Bitbucket workspace's settings, not
developer.atlassian.com) with its own client id/secret and endpoints. So
this CLI keeps two independent app configs and two independent token
caches.

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

# -- Atlassian (Jira / JSM) --------------------------------------------
ATLASSIAN_AUTH_BASE_URL = "https://auth.atlassian.com"

# read:jira-work is required for the servicedesk API to resolve issues;
# the servicedesk-request scopes are what the Jira API's "Add" button in
# https://developer.atlassian.com/console/myapps/ exposes for JSM (JSM has
# no separate product entry there - its scopes live under Jira API).
DEFAULT_ATLASSIAN_SCOPES = [
    "read:jira-work",
    "read:servicedesk-request",
    "manage:servicedesk-request",
    "offline_access",
]

# -- Bitbucket Cloud ------------------------------------------------------
# Bitbucket's OAuth consumer is created in the workspace, not the unified
# Atlassian developer console, and its authorize/token endpoints live on
# bitbucket.org rather than auth.atlassian.com.
BITBUCKET_AUTH_BASE_URL = "https://bitbucket.org/site/oauth2"

CONFIG_DIR = Path(os.environ.get("TEAMWORK_GRAPH_CONFIG_DIR", Path.home() / ".config" / "teamwork-graph-cli"))


def _token_path(provider: str) -> Path:
    return CONFIG_DIR / f"credentials-{provider}.json"


@dataclass
class AtlassianOAuthAppConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]

    @classmethod
    def from_env(cls) -> "AtlassianOAuthAppConfig":
        client_id = os.environ.get("ATLASSIAN_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("ATLASSIAN_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise SystemExit(
                "Missing ATLASSIAN_OAUTH_CLIENT_ID / ATLASSIAN_OAUTH_CLIENT_SECRET.\n"
                "Create an OAuth 2.0 (3LO) app at https://developer.atlassian.com/console/myapps/,\n"
                "click 'Add' on the Jira API permission, and add its servicedesk-request scopes\n"
                "(JSM has no separate product entry there - it rides on the Jira API scopes).\n"
                "Then export both variables before running this CLI."
            )
        redirect_uri = os.environ.get("ATLASSIAN_OAUTH_REDIRECT_URI", "http://localhost:8765/callback")
        scopes_env = os.environ.get("ATLASSIAN_OAUTH_SCOPES")
        scopes = scopes_env.split() if scopes_env else DEFAULT_ATLASSIAN_SCOPES
        return cls(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scopes=scopes)


@dataclass
class BitbucketOAuthAppConfig:
    client_id: str
    client_secret: str
    redirect_uri: str

    @classmethod
    def from_env(cls) -> "BitbucketOAuthAppConfig":
        client_id = os.environ.get("BITBUCKET_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("BITBUCKET_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise SystemExit(
                "Missing BITBUCKET_OAUTH_CLIENT_ID / BITBUCKET_OAUTH_CLIENT_SECRET.\n"
                "Create an OAuth consumer at https://bitbucket.org/<workspace>/workspace/settings/api\n"
                "(Workspace settings -> OAuth consumers -> Add consumer) with Repositories: Read,\n"
                "Pull requests: Read and Pipelines: Read permissions. Then export both variables\n"
                "before running this CLI."
            )
        redirect_uri = os.environ.get("BITBUCKET_OAUTH_REDIRECT_URI", "http://localhost:8766/callback")
        return cls(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)


def load_tokens(provider: str) -> dict | None:
    path = _token_path(provider)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_tokens(provider: str, tokens: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = _token_path(provider)
    path.write_text(json.dumps(tokens, indent=2))
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def clear_tokens(provider: str) -> None:
    path = _token_path(provider)
    if path.exists():
        path.unlink()
