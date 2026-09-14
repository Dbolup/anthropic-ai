# Claude Agent for Jira

This directory documents the **Claude → Jira** integration workflow, which allows you to assign a Jira ticket directly to Claude and receive a GitHub Pull Request as output — automatically.

---

## How It Works

```
Jira Ticket Created / Updated
        │
        ▼
  Assignee = Claude (Anthropic-hosted sandbox)
        │
        ▼
  Claude Agent analyses the ticket description
        │
        ▼
  Claude reads the target GitHub repository
        │
        ▼
  Claude implements the required changes on a feature branch
        │
        ▼
  Claude pushes the branch and opens a Draft PR
        │
        ▼
  PR linked back to the Jira ticket (Key in title & description)
```

---

## Workflow Steps

### 1. Create or Update a Jira Ticket
- Set the **Assignee** to the Claude agent user in your Jira project.
- Provide a clear **Summary** and **Description** that includes:
  - The target GitHub repository URL.
  - What needs to be built, fixed, or documented.

### 2. Claude Picks Up the Ticket
The Anthropic-hosted sandbox polls (or receives a webhook for) tickets assigned to Claude. Once detected, Claude:
- Reads the ticket metadata (Key, Summary, Description).
- Clones / accesses the linked GitHub repository.
- Reads `AGENTS.md` (if present) for project-specific conventions.

### 3. Claude Implements the Changes
Claude follows the repository's existing patterns, runs tests, and ensures the code is correct before committing.

Branch naming convention:
```
claude/{JIRA-KEY}/{short-slug}
```

Commit message convention:
```
{JIRA-KEY} {short description of change}
```

### 4. Pull Request is Opened
Claude pushes the branch and opens a **Draft Pull Request** with:
- **Title:** `{JIRA-KEY} {Summary}`
- **Description:** Full explanation of changes made, followed by:
  ```
  Key: {JIRA-KEY}
  Co-authored by Claude agent for Jira.
  ```

---

## Benefits

| Without Claude Agent | With Claude Agent |
|---|---|
| Engineer reads ticket manually | Claude reads & analyses ticket automatically |
| Engineer writes code | Claude writes idiomatic, tested code |
| Engineer opens PR | Claude opens a Draft PR instantly |
| Review cycle starts later | Review cycle starts immediately |

---

## Example

**Jira Ticket:**
- Key: `CWOWP-18`
- Summary: *Claude to Jira*
- Description: Assign a Jira ticket to Claude, get a pull request.

**Result:**
- Branch: `claude/CWOWP-18/claude-to-jira`
- PR Title: `CWOWP-18 Claude to Jira`
- PR Description includes `Key: CWOWP-18` and attribution line.

---

## Setup Requirements

1. A Jira project with a dedicated Claude agent user account.
2. An Anthropic-hosted Claude sandbox with:
   - Jira API credentials (to poll / receive webhooks).
   - GitHub credentials (to push branches and open PRs).
3. A GitHub repository the Claude agent has write access to.
4. *(Optional)* An `AGENTS.md` file in the repository root with project-specific conventions.

---

## Security Notes

- Claude operates with **least-privilege** GitHub credentials (write to feature branches only; cannot merge or delete protected branches).
- Jira API tokens are stored as secrets in the sandbox environment — never in the repository.
- All changes are in a **Draft PR** so a human engineer reviews before merging.
