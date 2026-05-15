#!/usr/bin/env python3
"""
Enumerate Tasks-DB rows where Status="To-Do" AND Exec="Agent" via the Notion REST
API, then write the result to state/todo-ids.json in the schema agency-os's
`refresh` command expects.

Why this exists: the Notion MCP currently installed does not expose property-
filtered enumeration of a data source. The REST API does. We call it directly.

Usage:
  python .claude/skills/agency-os/scripts/query-tasks.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

NOTION_API_VERSION = "2025-09-03"
# Path layout: scripts/ -> agency-os/ -> skills/ -> .claude/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = Path(__file__).resolve().parents[1]
POINTERS = SKILL_DIR / "references" / "notion-pointers.json"
SIDECAR = SKILL_DIR / "state" / "todo-ids.json"
ENV_FILE = REPO_ROOT / ".env"


def load_env_var(name: str) -> str:
    val = os.environ.get(name)
    if val:
        return val
    if not ENV_FILE.exists():
        sys.exit(f"error: {name} not in environment and {ENV_FILE} not found")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    sys.exit(f"error: {name} not found in {ENV_FILE}")


def notion_post(path: str, token: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        sys.exit(f"error: Notion API HTTP {e.code}\n{body_text}")


def prop_select(props: dict, name: str) -> str | None:
    p = props.get(name) or {}
    sel = p.get("select") or {}
    return sel.get("name")


def prop_status(props: dict, name: str) -> str | None:
    p = props.get(name) or {}
    st = p.get("status") or {}
    return st.get("name")


def prop_title(props: dict, name: str) -> str:
    p = props.get(name) or {}
    title = p.get("title") or []
    return "".join(t.get("plain_text", "") for t in title).strip()


def prop_date(props: dict, name: str) -> str | None:
    p = props.get(name) or {}
    d = p.get("date") or {}
    return d.get("start")


def prop_relation_ids(props: dict, name: str) -> list[str]:
    p = props.get(name) or {}
    rel = p.get("relation") or []
    return [r.get("id") for r in rel if r.get("id")]


def prop_rollup_number(props: dict, name: str) -> int | None:
    p = props.get(name) or {}
    rp = p.get("rollup") or {}
    if rp.get("type") == "number":
        return rp.get("number")
    if rp.get("type") == "array":
        return len(rp.get("array") or [])
    return None


def fetch_page_status(page_id: str, token: str) -> str | None:
    """Fetch a single page and read its Status property. Used to resolve dep statuses
    for tasks that aren't in the in-batch (To-Do AND Exec=Agent) result set."""
    req = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return None
    props = data.get("properties", {})
    return prop_status(props, "Status") or prop_select(props, "Status")


def fetch_description_preview(page_id: str, token: str) -> str:
    """Walk page blocks; collect text from blocks that appear AFTER the 'Description'
    H2 and BEFORE the next H2. Plain H2 + sibling paragraphs is the layout we observe;
    is_toggleable doesn't matter here. Best-effort; empty string on miss."""
    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=50",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return ""
    in_desc = False
    chunks: list[str] = []
    for blk in data.get("results", []):
        t = blk.get("type")
        if t == "heading_2":
            h2_text = "".join(r.get("plain_text", "") for r in blk.get("heading_2", {}).get("rich_text", []))
            if h2_text.strip().lower() == "description":
                in_desc = True
                continue
            if in_desc:
                break
        elif in_desc and t:
            inner = blk.get(t, {})
            rt = inner.get("rich_text") or []
            text = "".join(r.get("plain_text", "") for r in rt).strip()
            if text:
                chunks.append(text)
                if sum(len(c) for c in chunks) >= 200:
                    break
    return " ".join(chunks)[:200]


def main() -> int:
    token = load_env_var("NOTION_KEY")
    pointers = json.loads(POINTERS.read_text(encoding="utf-8"))
    data_source_id = pointers["tasks_database"]["data_source_id"]

    body = {
        "filter": {
            "and": [
                {"property": "Status", "select": {"equals": "To-Do"}},
                {"property": "Exec", "select": {"equals": "Agent"}},
            ]
        },
        "page_size": 100,
    }

    rows: list[dict] = []
    start_cursor: str | None = None
    while True:
        if start_cursor:
            body["start_cursor"] = start_cursor
        page = notion_post(f"/v1/data_sources/{data_source_id}/query", token, body)
        rows.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        start_cursor = page.get("next_cursor")

    tasks = []
    raw_dep_ids: dict[str, list[str]] = {}
    in_batch_ids: set[str] = set()
    for r in rows:
        props = r.get("properties", {})
        title = prop_title(props, "Title")
        status = prop_status(props, "Status") or prop_select(props, "Status")
        exec_val = prop_select(props, "Exec")
        if status != "To-Do" or exec_val != "Agent":
            print(f"dropped (post-fetch sanity): {title} status={status} exec={exec_val}")
            continue
        parent_ids = prop_relation_ids(props, "Parent Task")
        dep_ids = prop_relation_ids(props, "Dependencies")
        subtasks_count = prop_rollup_number(props, "Subtasks") or 0
        page_id = r["id"]
        in_batch_ids.add(page_id)
        raw_dep_ids[page_id] = dep_ids
        desc = fetch_description_preview(page_id, token)
        tasks.append({
            "id": page_id,
            "url": r.get("url"),
            "title": title,
            "corpus": prop_select(props, "Corpus"),
            "priority": prop_select(props, "Priority"),
            "effort": prop_select(props, "Effort"),
            "type": prop_select(props, "Type"),
            "cadence": prop_select(props, "Cadence"),
            "last_done": prop_date(props, "Last Done"),
            "exec": exec_val,
            "parent_task_id": parent_ids[0] if parent_ids else None,
            "has_todo_subtasks": subtasks_count > 0,
            "description_preview": desc,
            "dependencies": [],  # filled below
        })

    # Resolve dep statuses. Deps that share the in-batch set are "To-Do" by construction
    # (that's why they're in the sidecar). Everything else is fetched one page at a time.
    ext_status_cache: dict[str, str | None] = {}
    for t in tasks:
        deps_out = []
        for dep_id in raw_dep_ids.get(t["id"], []):
            if dep_id in in_batch_ids:
                dep_status = "To-Do"
            else:
                if dep_id not in ext_status_cache:
                    ext_status_cache[dep_id] = fetch_page_status(dep_id, token)
                dep_status = ext_status_cache[dep_id]
            deps_out.append({"id": dep_id, "status": dep_status})
        t["dependencies"] = deps_out

    SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "tasks": tasks,
    }
    SIDECAR.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"refreshed: {len(tasks)} agent-runnable To-Do tasks -> state/todo-ids.json")
    for t in tasks:
        print(f"  [{t['priority'] or '-'}/{t['effort'] or '-'}] {t['title']}  ->  {t['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
