"""Jira Service Management (JSM) queries used by the CLI."""
from __future__ import annotations

from .client import AtlassianSession


def list_service_desks(session: AtlassianSession, site_url: str | None = None) -> list[dict]:
    return session.jsm_get("/servicedesk", site_url=site_url).get("values", [])


def list_requests(
    session: AtlassianSession,
    service_desk_id: str | None = None,
    status: str | None = None,
    site_url: str | None = None,
) -> list[dict]:
    params: dict = {}
    if service_desk_id:
        params["serviceDeskId"] = service_desk_id
    if status:
        params["requestStatus"] = status
    return session.jsm_get("/request", params=params, site_url=site_url).get("values", [])


def get_request(session: AtlassianSession, issue_key_or_id: str, site_url: str | None = None) -> dict:
    return session.jsm_get(f"/request/{issue_key_or_id}", site_url=site_url)


def create_request(
    session: AtlassianSession,
    service_desk_id: str,
    request_type_id: str,
    summary: str,
    description: str = "",
    site_url: str | None = None,
) -> dict:
    body = {
        "serviceDeskId": service_desk_id,
        "requestTypeId": request_type_id,
        "requestFieldValues": {"summary": summary, "description": description},
    }
    return session.jsm_post("/request", json_body=body, site_url=site_url)
