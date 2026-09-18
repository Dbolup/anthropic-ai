"""Atlassian OAuth 2.0 (3LO) authorization-code flow, used for Jira Service Management.

Exchanges the authorization code for an access/refresh token pair and
transparently refreshes an expired access token before each API call. See
`bitbucket_auth.py` for the separate flow Bitbucket Cloud requires.
"""
from __future__ import annotations

import time

import requests

from .config import ATLASSIAN_AUTH_BASE_URL, AtlassianOAuthAppConfig, clear_tokens, load_tokens, save_tokens
from .oauth_common import authorize_via_browser

PROVIDER = "atlassian"
AUTHORIZE_URL = f"{ATLASSIAN_AUTH_BASE_URL}/authorize"
TOKEN_URL = f"{ATLASSIAN_AUTH_BASE_URL}/oauth/token"
ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


def interactive_login(app: AtlassianOAuthAppConfig, timeout: int = 180) -> dict:
    """Runs the full authorization-code exchange and persists the resulting tokens."""
    query = {
        "audience": "api.atlassian.com",
        "client_id": app.client_id,
        "scope": " ".join(app.scopes),
        "redirect_uri": app.redirect_uri,
        "response_type": "code",
        "prompt": "consent",
    }
    code = authorize_via_browser(AUTHORIZE_URL, query, app.redirect_uri, "Atlassian", timeout=timeout)

    tokens = _exchange_code_for_tokens(app, code)
    tokens["obtained_at"] = time.time()
    save_tokens(PROVIDER, tokens)
    print("Atlassian login successful; tokens cached locally.")
    return tokens


def _exchange_code_for_tokens(app: AtlassianOAuthAppConfig, code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        json={
            "grant_type": "authorization_code",
            "client_id": app.client_id,
            "client_secret": app.client_secret,
            "code": code,
            "redirect_uri": app.redirect_uri,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _refresh_tokens(app: AtlassianOAuthAppConfig, refresh_token: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        json={
            "grant_type": "refresh_token",
            "client_id": app.client_id,
            "client_secret": app.client_secret,
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    tokens = resp.json()
    tokens["obtained_at"] = time.time()
    # Atlassian rotates refresh tokens; fall back to the old one if a new one wasn't issued.
    tokens.setdefault("refresh_token", refresh_token)
    return tokens


def get_access_token(app: AtlassianOAuthAppConfig) -> str:
    """Returns a valid access token, refreshing or re-authenticating as needed."""
    tokens = load_tokens(PROVIDER)
    if tokens is None:
        tokens = interactive_login(app)

    expires_at = tokens.get("obtained_at", 0) + tokens.get("expires_in", 0)
    if time.time() >= expires_at - 30:
        try:
            tokens = _refresh_tokens(app, tokens["refresh_token"])
            save_tokens(PROVIDER, tokens)
        except (requests.HTTPError, KeyError):
            tokens = interactive_login(app)

    return tokens["access_token"]


def get_accessible_resources(access_token: str) -> list[dict]:
    """Returns the cloud sites (Jira/Confluence workspaces) this token can reach."""
    resp = requests.get(
        ACCESSIBLE_RESOURCES_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def logout() -> None:
    clear_tokens(PROVIDER)
