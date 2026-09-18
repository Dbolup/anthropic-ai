"""Teamwork Graph CLI: reach Bitbucket and Jira Service Management via Atlassian OAuth 2.0 (3LO).

The Atlassian MCP connection used by Claude exposes Jira, Confluence, and Compass
tools, but not Bitbucket or Jira Service Management (JSM). This package implements
its own OAuth 2.0 (3LO) authorization-code flow so those products can be queried
directly from the command line.
"""

__version__ = "0.1.0"
