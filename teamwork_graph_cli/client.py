"""Thin authenticated HTTP client shared by the Bitbucket and JSM wrappers."""
from __future__ import annotations

import requests

from .auth import get_access_token, get_accessible_resources
from .config import OAuthAppConfig

BITBUCKET_API_BASE = "https://api.bitbucket.org/2.0"
JIRA_EX_BASE = "https://api.atlassian.com/ex/jira"


class AtlassianSession:
    """Wraps `requests` with a bearer token and resolves the active cloud site."""

    def __init__(self, app: OAuthAppConfig | None = None):
        self.app = app or OAuthAppConfig.from_env()
        self._access_token: str | None = None
        self._cloud_id: str | None = None

    @property
    def access_token(self) -> str:
        if self._access_token is None:
            self._access_token = get_access_token(self.app)
        return self._access_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def cloud_id(self, site_url: str | None = None) -> str:
        """Resolves the Jira/JSM cloud id for the connected site (first one, unless `site_url` is given)."""
        if self._cloud_id and site_url is None:
            return self._cloud_id
        resources = get_accessible_resources(self.access_token)
        if not resources:
            raise SystemExit("No accessible Atlassian sites for this token; check the app's granted scopes.")
        chosen = resources[0]
        if site_url:
            for resource in resources:
                if resource.get("url", "").rstrip("/") == site_url.rstrip("/"):
                    chosen = resource
                    break
            else:
                raise SystemExit(f"No accessible site matched {site_url!r}. Known sites: "
                                  f"{[r['url'] for r in resources]}")
        self._cloud_id = chosen["id"]
        return self._cloud_id

    # -- Bitbucket -----------------------------------------------------
    def bitbucket_get(self, path: str, params: dict | None = None) -> dict:
        url = path if path.startswith("http") else f"{BITBUCKET_API_BASE}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # -- Jira Service Management ----------------------------------------
    def jsm_get(self, path: str, params: dict | None = None, site_url: str | None = None) -> dict:
        cloud_id = self.cloud_id(site_url)
        url = f"{JIRA_EX_BASE}/{cloud_id}/rest/servicedeskapi{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def jsm_post(self, path: str, json_body: dict, site_url: str | None = None) -> dict:
        cloud_id = self.cloud_id(site_url)
        url = f"{JIRA_EX_BASE}/{cloud_id}/rest/servicedeskapi{path}"
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        resp = requests.post(url, headers=headers, json=json_body, timeout=30)
        resp.raise_for_status()
        return resp.json()
