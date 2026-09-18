"""Atlassian OAuth 2.0 (3LO) authorization-code flow.

Runs a short-lived local HTTP server to catch the redirect, exchanges the
authorization code for an access/refresh token pair, and transparently
refreshes an expired access token before each API call.
"""
from __future__ import annotations

import http.server
import secrets
import threading
import time
import urllib.parse
import webbrowser

import requests

from .config import AUTH_BASE_URL, OAuthAppConfig, load_tokens, save_tokens

AUTHORIZE_URL = f"{AUTH_BASE_URL}/authorize"
TOKEN_URL = f"{AUTH_BASE_URL}/oauth/token"
ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    result: dict = {}

    def do_GET(self):  # noqa: N802 - required method name
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _CallbackHandler.result["code"] = params.get("code", [None])[0]
        _CallbackHandler.result["state"] = params.get("state", [None])[0]
        _CallbackHandler.result["error"] = params.get("error_description", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        body = "Authorization complete, you can close this tab and return to the terminal."
        if _CallbackHandler.result["error"]:
            body = f"Authorization failed: {_CallbackHandler.result['error']}"
        self.wfile.write(body.encode())

    def log_message(self, *args):  # silence default request logging
        pass


def _run_callback_server(port: int, timeout: int) -> dict:
    _CallbackHandler.result = {}
    server = http.server.HTTPServer(("localhost", port), _CallbackHandler)
    server.timeout = timeout
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    deadline = time.time() + timeout
    while thread.is_alive() and time.time() < deadline:
        time.sleep(0.1)
    server.server_close()
    return _CallbackHandler.result


def interactive_login(app: OAuthAppConfig, timeout: int = 180) -> dict:
    """Runs the full authorization-code exchange and persists the resulting tokens."""
    state = secrets.token_urlsafe(24)
    parsed_redirect = urllib.parse.urlparse(app.redirect_uri)
    port = parsed_redirect.port or 8765

    query = {
        "audience": "api.atlassian.com",
        "client_id": app.client_id,
        "scope": " ".join(app.scopes),
        "redirect_uri": app.redirect_uri,
        "state": state,
        "response_type": "code",
        "prompt": "consent",
    }
    authorize_url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(query)}"

    print("Opening browser for Atlassian sign-in...")
    print(f"If it doesn't open automatically, visit:\n  {authorize_url}\n")
    webbrowser.open(authorize_url)

    result = _run_callback_server(port, timeout)

    if not result or not result.get("code"):
        raise SystemExit(result.get("error") or "Timed out waiting for the OAuth redirect.")
    if result.get("state") != state:
        raise SystemExit("OAuth state mismatch; aborting for safety.")

    tokens = _exchange_code_for_tokens(app, result["code"])
    tokens["obtained_at"] = time.time()
    save_tokens(tokens)
    print("Login successful; tokens cached locally.")
    return tokens


def _exchange_code_for_tokens(app: OAuthAppConfig, code: str) -> dict:
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


def _refresh_tokens(app: OAuthAppConfig, refresh_token: str) -> dict:
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


def get_access_token(app: OAuthAppConfig) -> str:
    """Returns a valid access token, refreshing or re-authenticating as needed."""
    tokens = load_tokens()
    if tokens is None:
        tokens = interactive_login(app)

    expires_at = tokens.get("obtained_at", 0) + tokens.get("expires_in", 0)
    if time.time() >= expires_at - 30:
        try:
            tokens = _refresh_tokens(app, tokens["refresh_token"])
            save_tokens(tokens)
        except (requests.HTTPError, KeyError):
            tokens = interactive_login(app)

    return tokens["access_token"]


def get_accessible_resources(access_token: str) -> list[dict]:
    """Returns the cloud sites (Jira/Confluence/Bitbucket workspaces) this token can reach."""
    resp = requests.get(
        ACCESSIBLE_RESOURCES_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def logout() -> None:
    from .config import clear_tokens

    clear_tokens()
