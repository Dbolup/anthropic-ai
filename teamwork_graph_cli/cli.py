"""Command-line entrypoint for the Teamwork Graph CLI."""
from __future__ import annotations

import json

import click

from . import bitbucket, bitbucket_auth, jsm
from .auth import interactive_login as atlassian_login, logout as atlassian_logout
from .client import AtlassianSession, BitbucketSession
from .config import AtlassianOAuthAppConfig, BitbucketOAuthAppConfig


def _print(data) -> None:
    click.echo(json.dumps(data, indent=2, default=str))


@click.group()
@click.option("--site", "site_url", default=None, help="Atlassian site URL for JSM calls, e.g. https://yourteam.atlassian.net (defaults to the first accessible site).")
@click.pass_context
def main(ctx: click.Context, site_url: str | None):
    """Query Bitbucket and Jira Service Management directly.

    Bitbucket and JSM are authorized separately: JSM through an Atlassian
    OAuth 2.0 (3LO) app, Bitbucket through its own OAuth consumer. Run
    `login atlassian` and/or `login bitbucket` depending on which you need.
    """
    ctx.obj = {"site_url": site_url}


@main.command()
@click.argument("provider", type=click.Choice(["atlassian", "bitbucket"]))
def login(provider: str):
    """Run a provider's OAuth authorization-code flow and cache the resulting tokens."""
    if provider == "atlassian":
        atlassian_login(AtlassianOAuthAppConfig.from_env())
    else:
        bitbucket_auth.interactive_login(BitbucketOAuthAppConfig.from_env())


@main.command()
@click.argument("provider", type=click.Choice(["atlassian", "bitbucket", "all"]), default="all")
def logout(provider: str):
    """Discard cached OAuth tokens for one provider, or both (the default)."""
    if provider in ("atlassian", "all"):
        atlassian_logout()
    if provider in ("bitbucket", "all"):
        bitbucket_auth.logout()
    click.echo("Cached tokens removed.")


@main.group()
def bb():
    """Bitbucket queries."""


@bb.command("repos")
@click.argument("workspace")
def bb_repos(workspace: str):
    """List repositories in a Bitbucket workspace."""
    _print(bitbucket.list_repositories(BitbucketSession(), workspace))


@bb.command("prs")
@click.argument("workspace")
@click.argument("repo_slug")
@click.option("--state", default="OPEN", help="OPEN, MERGED, DECLINED, or SUPERSEDED.")
def bb_prs(workspace: str, repo_slug: str, state: str):
    """List pull requests for a repository."""
    _print(bitbucket.list_pull_requests(BitbucketSession(), workspace, repo_slug, state))


@bb.command("pr")
@click.argument("workspace")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
def bb_pr(workspace: str, repo_slug: str, pr_id: int):
    """Show a single pull request."""
    _print(bitbucket.get_pull_request(BitbucketSession(), workspace, repo_slug, pr_id))


@bb.command("commits")
@click.argument("workspace")
@click.argument("repo_slug")
@click.option("--branch", default=None)
def bb_commits(workspace: str, repo_slug: str, branch: str | None):
    """List commits for a repository (optionally a specific branch)."""
    _print(bitbucket.list_commits(BitbucketSession(), workspace, repo_slug, branch))


@main.group()
def sd():
    """Jira Service Management (JSM) queries."""


@sd.command("desks")
@click.pass_context
def sd_desks(ctx: click.Context):
    """List service desks visible to this account."""
    _print(jsm.list_service_desks(AtlassianSession(), site_url=ctx.obj["site_url"]))


@sd.command("requests")
@click.option("--service-desk-id", default=None)
@click.option("--status", default=None, help="e.g. 'OPEN', 'CLOSED'.")
@click.pass_context
def sd_requests(ctx: click.Context, service_desk_id: str | None, status: str | None):
    """List customer requests, optionally filtered by service desk or status."""
    _print(jsm.list_requests(AtlassianSession(), service_desk_id, status, site_url=ctx.obj["site_url"]))


@sd.command("request")
@click.argument("issue_key_or_id")
@click.pass_context
def sd_request(ctx: click.Context, issue_key_or_id: str):
    """Show a single customer request."""
    _print(jsm.get_request(AtlassianSession(), issue_key_or_id, site_url=ctx.obj["site_url"]))


@sd.command("create")
@click.option("--service-desk-id", required=True)
@click.option("--request-type-id", required=True)
@click.option("--summary", required=True)
@click.option("--description", default="")
@click.pass_context
def sd_create(ctx: click.Context, service_desk_id: str, request_type_id: str, summary: str, description: str):
    """Create a new customer request."""
    _print(jsm.create_request(
        AtlassianSession(), service_desk_id, request_type_id, summary, description, site_url=ctx.obj["site_url"],
    ))


if __name__ == "__main__":
    main()
