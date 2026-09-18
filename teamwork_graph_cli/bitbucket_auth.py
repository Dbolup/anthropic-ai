"""Bitbucket Cloud's own OAuth 2.0 authorization-code flow.

Unlike Jira/JSM, Bitbucket Cloud is not part of the unified
api.atlassian.com OAuth system: its OAuth consumer is registered from a
workspace's own settings (Workspace settings -> OAuth consumers), and its
authorize/token endpoints live on bitbucket.org. The token endpoint also
authenticates the client with HTTP Basic auth and expects a form-encoded
body, not the JSON body Atlassian's endpoint accepts.
"""
from __future__ import annotations

import time

import requests

from .config import BITBUCKET_AUTH_BASE_URL, BitbucketOAuthAppConfig, clear_tokens, load_tokens, save_tokens
from .oauth_common import authorize_via_browser

PROVIDER = "bitbucket"
AUTHORIZE_URL = f"{BITBUCKET_AUTH_BASE_URL}/authorize"
TOKEN_URL = f"{BITBUCKET_AUTH_BASE_URL}/access_token"


def interactive_login(app: BitbucketOAuthAppConfig, timeout: int = 180) -> dict:
    """Runs the full authorization-code exchange and persists the resulting tokens."""
    query = {
        "client_id": app.client_id,
        "redirect_uri": app.redirect_uri,
        "response_type": "code",
    }
    code = authorize_via_browser(AUTHORIZE_URL, query, app.redirect_uri, "Bitbucket", timeout=timeout)

    tokens = _exchange_code_for_tokens(app, code)
    tokens["obtained_at"] = time.time()
    save_tokens(PROVIDER, tokens)
    print("Bitbucket login successful; tokens cached locally.")
    return tokens


def _exchange_code_for_tokens(app: BitbucketOAuthAppConfig, code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        auth=(app.client_id, app.client_secret),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": app.redirect_uri,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _refresh_tokens(app: BitbucketOAuthAppConfig, refresh_token: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        auth=(app.client_id, app.client_secret),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    tokens = resp.json()
    tokens["obtained_at"] = time.time()
    tokens.setdefault("refresh_token", refresh_token)
    return tokens


def get_access_token(app: BitbucketOAuthAppConfig) -> str:
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


def logout() -> None:
    clear_tokens(PROVIDER)
