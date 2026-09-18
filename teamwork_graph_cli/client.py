"""Thin authenticated HTTP clients used by the Bitbucket and JSM wrappers.

These are deliberately separate: Bitbucket and JSM are authorized through
two independent OAuth flows (see `auth.py` and `bitbucket_auth.py`) with
different tokens, so a Bitbucket call must never be made with an Atlassian
token or vice versa.
"""
from __future__ import annotations

import requests

from . import bitbucket_auth
from .auth import get_access_token, get_accessible_resources
from .config import AtlassianOAuthAppConfig, BitbucketOAuthAppConfig

BITBUCKET_API_BASE = "https://api.bitbucket.org/2.0"
JIRA_EX_BASE = "https://api.atlassian.com/ex/jira"


class AtlassianSession:
    """Wraps `requests` with a Jira/JSM bearer token and resolves the active cloud site."""

    def __init__(self, app: AtlassianOAuthAppConfig | None = None):
        self.app = app or AtlassianOAuthAppConfig.from_env()
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


class BitbucketSession:
    """Wraps `requests` with a Bitbucket bearer token, obtained via Bitbucket's own OAuth consumer."""

    def __init__(self, app: BitbucketOAuthAppConfig | None = None):
        self.app = app or BitbucketOAuthAppConfig.from_env()
        self._access_token: str | None = None

    @property
    def access_token(self) -> str:
        if self._access_token is None:
            self._access_token = bitbucket_auth.get_access_token(self.app)
        return self._access_token

    def bitbucket_get(self, path: str, params: dict | None = None) -> dict:
        url = path if path.startswith("http") else f"{BITBUCKET_API_BASE}{path}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
