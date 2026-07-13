# Linear Deploy Integration — Implementation Reference

## Overview

Integrate Linear with your deployment pipeline to automatically track deployments,
create deployment issues, and link commits to Linear tickets.

## Prerequisites

- Linear API key with workspace write access
- Deployment platform (Vercel, Railway, GCP Cloud Run, or GitHub Actions)
- Linear team ID

## GitHub Actions Deployment Tracking

```yaml
# .github/workflows/deploy.yml
name: Deploy + Linear Tracking

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy application
        id: deploy
        run: |
          echo "DEPLOY_URL=https://app.example.com" >> $GITHUB_OUTPUT
          echo "DEPLOY_VERSION=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT

      - name: Create Linear deployment issue
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          LINEAR_TEAM_ID: ${{ secrets.LINEAR_TEAM_ID }}
          DEPLOY_VERSION: ${{ steps.deploy.outputs.DEPLOY_VERSION }}
          DEPLOY_URL: ${{ steps.deploy.outputs.DEPLOY_URL }}
        run: python3 scripts/linear_deploy_notify.py
```

## Python Deployment Tracker

```python
import os
import json
import re
import subprocess
import urllib.request
from datetime import datetime

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LINEAR_TEAM_ID = os.environ["LINEAR_TEAM_ID"]


def graphql(query: str, variables: dict) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": LINEAR_API_KEY,
    }
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["data"]


def get_commit_info() -> dict:
    sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    msg = subprocess.check_output(["git", "log", "-1", "--pretty=%s"]).decode().strip()
    author = subprocess.check_output(["git", "log", "-1", "--pretty=%an"]).decode().strip()
    return {"sha": sha, "message": msg, "author": author}


def extract_linear_ids(commit_msg: str) -> list:
    """Parse LINEAR-123 style ticket IDs from commit messages."""
    return re.findall(r"[A-Z]+-[0-9]+", commit_msg)


def link_commit_to_issues(commit: dict) -> None:
    ids = extract_linear_ids(commit["message"])
    if not ids:
        print(f"No Linear IDs found in: {commit['message']}")
        return

    mutation = """
    mutation AddComment($issueId: String!, $body: String!) {
      commentCreate(input: { issueId: $issueId, body: $body }) {
        success
      }
    }
    """
    for identifier in ids:
        query = """
        query Issue($id: String!) {
          issue(id: $id) { id title }
        }
        """
        try:
            result = graphql(query, {"id": identifier})
            issue_id = result["issue"]["id"]
            body = (
                f"**Deployed** at {datetime.utcnow().isoformat()}Z\n\n"
                f"SHA: `{commit['sha']}`\n"
                f"Commit: {commit['message']}\n"
                f"Author: {commit['author']}"
            )
            graphql(mutation, {"issueId": issue_id, "body": body})
            print(f"Linked deploy to {identifier}")
        except Exception as e:
            print(f"Warning: could not link {identifier}: {e}")


def create_deployment_record(env: str, version: str, url: str) -> str:
    mutation = """
    mutation($teamId: String!, $title: String!, $desc: String!) {
      issueCreate(input: { teamId: $teamId, title: $title, description: $desc }) {
        issue { identifier url }
      }
    }
    """
    result = graphql(mutation, {
        "teamId": LINEAR_TEAM_ID,
        "title": f"[Deploy] {env} -- {version}",
        "desc": (
            f"**Environment:** {env}\n"
            f"**Version:** {version}\n"
            f"**URL:** {url}\n"
            f"**Time:** {datetime.utcnow().isoformat()}Z"
        ),
    })
    issue = result["issueCreate"]["issue"]
    print(f"Deployment record: {issue['identifier']} {issue['url']}")
    return issue["identifier"]


if __name__ == "__main__":
    commit = get_commit_info()
    link_commit_to_issues(commit)
    deploy_url = os.environ.get("DEPLOY_URL", "https://app.example.com")
    create_deployment_record("production", commit["sha"], deploy_url)
```

## Vercel Integration via Webhook

```python
# Webhook handler (FastAPI) for Vercel deploy events
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/vercel-deploy")
async def handle_vercel_deploy(request: Request):
    data = await request.json()
    if data.get("type") == "deployment.succeeded":
        deployment = data["payload"]["deployment"]
        create_deployment_record(
            env=deployment.get("meta", {}).get("branch", "unknown"),
            version=deployment["id"][:8],
            url=deployment.get("url", ""),
        )
    return JSONResponse({"ok": True})
```

## Deployment Status Checker

```python
def check_deployment_issues(team_id: str) -> list:
    """List open deployment issues to audit what is live."""
    query = """
    query DeployIssues($filter: IssueFilter!) {
      issues(filter: $filter, first: 20, orderBy: createdAt) {
        nodes { identifier title createdAt state { name } }
      }
    }
    """
    result = graphql(query, {
        "filter": {
            "team": {"id": {"eq": team_id}},
            "title": {"startsWith": {"eq": "[Deploy]"}},
        }
    })
    return result["issues"]["nodes"]
```

## Resources

- [Linear API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [Linear Webhooks](https://developers.linear.app/docs/sdk/webhooks)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
