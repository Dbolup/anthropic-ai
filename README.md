# anthropic-ai
Learnings about anthropic AI courses

## Teamwork Graph CLI

Claude's Atlassian integration in this environment runs through the Atlassian
Rovo MCP server, which exposes Jira, Confluence, and Compass tools but has no
tools for Bitbucket or Jira Service Management (JSM). `teamwork-graph-cli`
fills that gap with a standalone command-line tool that authenticates to
Atlassian directly via OAuth 2.0 (three-legged / "3LO") and queries Bitbucket
and JSM.

### Setup

1. Create an OAuth 2.0 (3LO) app at
   https://developer.atlassian.com/console/myapps/, and enable the
   **Bitbucket API** and **Jira Service Management API** under its
   permissions.
2. Add a callback URL matching `ATLASSIAN_OAUTH_REDIRECT_URI` below (default
   `http://localhost:8765/callback`).
3. Install the CLI:

   ```bash
   pip install -e .
   ```

4. Export credentials for the app you created:

   ```bash
   export ATLASSIAN_OAUTH_CLIENT_ID=...
   export ATLASSIAN_OAUTH_CLIENT_SECRET=...
   # optional, defaults shown:
   export ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8765/callback
   ```

5. Log in (opens a browser for the Atlassian consent screen, then caches the
   access/refresh tokens under `~/.config/teamwork-graph-cli/`):

   ```bash
   teamwork-graph login
   ```

### Usage

```bash
# Bitbucket
teamwork-graph bb repos <workspace>
teamwork-graph bb prs <workspace> <repo_slug> --state OPEN
teamwork-graph bb pr <workspace> <repo_slug> <pr_id>
teamwork-graph bb commits <workspace> <repo_slug> --branch main

# Jira Service Management
teamwork-graph sd desks
teamwork-graph sd requests --service-desk-id 1 --status OPEN
teamwork-graph sd request <issue-key-or-id>
teamwork-graph sd create --service-desk-id 1 --request-type-id 10 --summary "..."

# Discard cached tokens
teamwork-graph logout
```

Pass `--site https://yourteam.atlassian.net` before a `sd` subcommand if the
OAuth app has access to more than one Atlassian site and you need a
non-default one. Access tokens are refreshed automatically using the cached
refresh token; if that fails, the browser-based login flow runs again.

