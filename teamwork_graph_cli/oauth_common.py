"""Shared local-redirect plumbing for the two OAuth 2.0 flows this CLI drives.

Atlassian (for JSM) and Bitbucket run separate OAuth systems with different
token endpoints and client-authentication styles, but both are a standard
authorization-code flow that needs a local HTTP server to catch the
redirect. That part is shared here; the provider-specific pieces live in
`auth.py` (Atlassian) and `bitbucket_auth.py` (Bitbucket).
"""
from __future__ import annotations

import http.server
import secrets
import threading
import time
import urllib.parse
import webbrowser


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


def authorize_via_browser(
    authorize_url_base: str,
    query: dict,
    redirect_uri: str,
    provider_label: str,
    timeout: int = 180,
) -> str:
    """Opens `authorize_url_base?query` in a browser and waits for the redirect's `code`.

    `query` must already include everything but `state`, which is generated here
    for CSRF protection and validated against the callback.
    """
    state = secrets.token_urlsafe(24)
    query = {**query, "state": state}
    parsed_redirect = urllib.parse.urlparse(redirect_uri)
    port = parsed_redirect.port
    if not port:
        raise SystemExit(f"{provider_label} redirect URI must include an explicit port: {redirect_uri!r}")

    authorize_url = f"{authorize_url_base}?{urllib.parse.urlencode(query)}"
    print(f"Opening browser for {provider_label} sign-in...")
    print(f"If it doesn't open automatically, visit:\n  {authorize_url}\n")
    webbrowser.open(authorize_url)

    result = _run_callback_server(port, timeout)

    if not result or not result.get("code"):
        raise SystemExit(result.get("error") or f"Timed out waiting for the {provider_label} OAuth redirect.")
    if result.get("state") != state:
        raise SystemExit("OAuth state mismatch; aborting for safety.")

    return result["code"]
