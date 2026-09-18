# anthropic-ai
Learnings about anthropic AI courses

## Teamwork Graph CLI

Claude's Atlassian integration in this environment runs through the Atlassian
Rovo MCP server, which exposes Jira, Confluence, and Compass tools but has no
tools for Bitbucket or Jira Service Management (JSM). `teamwork-graph-cli`
fills that gap with a standalone command-line tool that queries Bitbucket and
JSM directly.

Bitbucket and JSM are **not** reachable through one unified Atlassian OAuth
app, so this CLI authorizes them separately:

- **JSM** rides on the Jira Cloud platform, so it's authorized through a
  standard Atlassian OAuth 2.0 (3LO) app
  (https://developer.atlassian.com/console/myapps/). JSM has no separate
  product entry in that console's permissions list — its scopes
  (`read:servicedesk-request`, `manage:servicedesk-request`, ...) are added
  by clicking **Add** on the **Jira API** row.
- **Bitbucket Cloud** uses its own, older OAuth system entirely: an OAuth
  *consumer* registered from a Bitbucket workspace's own settings, not the
  developer console, with its own client id/secret and its own
  authorize/token endpoints on `bitbucket.org`. It does not appear in the
  developer console's permissions list at all.

### Setup

1. Install the CLI:

   ```bash
   pip install -e .
   ```

2. **For JSM:** create an OAuth 2.0 (3LO) app at
   https://developer.atlassian.com/console/myapps/, click **Add** on the
   **Jira API** permission and add its servicedesk-request scopes, and add a
   callback URL matching `ATLASSIAN_OAUTH_REDIRECT_URI` below (default
   `http://localhost:8765/callback`). Then export:

   ```bash
   export ATLASSIAN_OAUTH_CLIENT_ID=...
   export ATLASSIAN_OAUTH_CLIENT_SECRET=...
   # optional, defaults shown:
   export ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8765/callback
   ```

3. **For Bitbucket:** create an OAuth consumer at
   `https://bitbucket.org/<workspace>/workspace/settings/api` (Workspace
   settings -> OAuth consumers -> Add consumer) with **Repositories: Read**,
   **Pull requests: Read**, and **Pipelines: Read** permissions, and a
   callback URL matching `BITBUCKET_OAUTH_REDIRECT_URI` below (default
   `http://localhost:8766/callback`). Then export:

   ```bash
   export BITBUCKET_OAUTH_CLIENT_ID=...       # the consumer's "Key"
   export BITBUCKET_OAUTH_CLIENT_SECRET=...   # the consumer's "Secret"
   # optional, default shown:
   export BITBUCKET_OAUTH_REDIRECT_URI=http://localhost:8766/callback
   ```

4. Log in to whichever provider(s) you need (opens a browser for that
   provider's consent screen, then caches access/refresh tokens under
   `~/.config/teamwork-graph-cli/`):

   ```bash
   teamwork-graph login atlassian
   teamwork-graph login bitbucket
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

# Discard cached tokens (both providers, or pass 'atlassian'/'bitbucket' for just one)
teamwork-graph logout
```

Pass `--site https://yourteam.atlassian.net` before a `sd` subcommand if the
Atlassian app has access to more than one site and you need a non-default
one. Access tokens are refreshed automatically using the cached refresh
token for each provider; if that fails, that provider's browser-based login
flow runs again.

