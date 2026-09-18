# Claude Agent for Jira + GitHub PR

An AI-powered agent that bridges **Jira** and **GitHub**.  
Given a Jira issue key, it:

1. **Fetches** the full Jira issue (summary, description, labels, components, …)
2. **Asks Claude** to analyse the issue and produce an implementation plan, a branch name, a PR title, and a detailed PR description
3. **Creates a GitHub branch** (named `claude/<JIRA-KEY>/<slug>`) off your configured base branch
4. **Commits** an implementation-notes Markdown file to that branch
5. **Opens a pull request** on GitHub with the AI-generated title and description
6. **Posts a comment** back to the Jira issue with the PR link (optional)

---

## Quick Start

### 1 — Clone & install dependencies

```bash
git clone https://github.com/Dbolup/anthropic-ai.git
cd anthropic-ai
pip install -r requirements.txt
```

### 2 — Configure environment variables

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `CLAUDE_MODEL` | ➖ | Model to use (default: `claude-opus-4-5`) |
| `JIRA_URL` | ✅ | Your Jira instance URL, e.g. `https://myorg.atlassian.net` |
| `JIRA_USERNAME` | ✅ | Jira account email |
| `JIRA_API_TOKEN` | ✅ | Jira API token |
| `GITHUB_TOKEN` | ✅ | GitHub personal access token (needs `repo` scope) |
| `GITHUB_REPO` | ✅ | Target repository in `owner/repo` format |
| `GITHUB_BASE_BRANCH` | ➖ | Branch to open PRs against (default: `main`) |

### 3 — Run the agent

```bash
python main.py CI-117
```

To skip posting a comment back to Jira:

```bash
python main.py CI-117 --no-jira-comment
```

---

## Project Structure

```
anthropic-ai/
├── main.py                  # CLI entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py            # Environment-based configuration
│   ├── jira_client.py       # Jira API wrapper
│   ├── github_client.py     # GitHub API wrapper
│   └── agent.py             # Core orchestration agent
└── tests/
    ├── test_config.py
    ├── test_jira_client.py
    ├── test_github_client.py
    └── test_agent.py
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## How It Works

```
User → main.py CI-117
         │
         ▼
   JiraClient.get_issue("CI-117")
         │
         ▼
   ClaudeAgent._ask_claude(issue)   ← Anthropic API
         │ Returns JSON plan
         ▼
   GitHubClient.create_branch(...)
   GitHubClient.create_or_update_file(...)   ← implementation notes
   GitHubClient.create_pull_request(...)
         │
         ▼
   JiraClient.add_comment(...)      ← PR link posted to Jira
         │
         ▼
   Print result to stdout
```
