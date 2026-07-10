#!/usr/bin/env python3
"""Dependency-free repo preflight scanner for the agent-safety-preflight Claude Code command."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

DELETE_PATTERN = r"\brm\s+-" + r"rf\b|Remove-Item\s+-Recurse\s+-Force"
RISK_PATTERNS = [
    ("destructive-recursive-delete", re.compile(DELETE_PATTERN, re.I)),
    ("shell-network-install", re.compile(r"curl\b[^\n|;]*(\||>)|wget\b[^\n|;]*(\||>)", re.I)),
    (
        "credential-write",
        re.compile(
            r"(?:^|[\n{,])\s*['\"]?(?:AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|STRIPE_SECRET|PAYPAL_(?:CLIENT_ID|CLIENT_SECRET|SECRET|ACCESS_TOKEN|API_KEY))['\"]?\s*[:=]",
            re.I,
        ),
    ),
    (
        "agent-authority",
        re.compile(
            r"(mcpServers|(?:claude|cursor|agent)[-_ ]?hooks|hooks\s*[:=]\s*(\[|\{|['\"]?(pre|post|tool|agent|command))|allowedTools|dangerously|autoApprove|agent[-_ ]?permissions|tool[-_ ]?permissions|permissions['\"]?\s*[:=]\s*(?:['\"]?(?:write|admin|danger|allow)|\[[^\]\n]*(?:write|admin|danger|allow)))",
            re.I,
        ),
    ),
]
INTERESTING_NAMES = {
    ".claude",
    ".mcp.json",
    "mcp.json",
    "claude_desktop_config.json",
    "settings.json",
    "package.json",
    "Makefile",
    "justfile",
    "Dockerfile",
}
INTERESTING_SUFFIXES = {".sh", ".bash", ".zsh", ".ps1", ".yaml", ".yml", ".json", ".toml", ".md"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
MAX_SCAN_BYTES = 120_000
SAFE_ENV_SUFFIXES = (".example", ".sample", ".template")


def is_credential_filename(name: str) -> bool:
    return name == ".env" or (name.startswith(".env.") and not name.endswith(SAFE_ENV_SUFFIXES))


def read_sample(path: Path) -> str:
    with path.open("rb") as handle:
        return handle.read(MAX_SCAN_BYTES).decode("utf-8", errors="ignore")


def git_state(repo: Path) -> str:
    try:
        cp = subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True, timeout=5)
    except Exception:
        return "unavailable"
    if cp.returncode != 0:
        return "unavailable"
    return "dirty" if cp.stdout.strip() else "clean"


def iter_files(repo: Path):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for name in files:
            p = root_path / name
            rel = p.relative_to(repo)
            if (
                any(part in {".claude", ".cursor", ".github"} for part in rel.parts)
                or name in INTERESTING_NAMES
                or is_credential_filename(name)
                or p.suffix in INTERESTING_SUFFIXES
            ):
                yield p


def scan(repo: Path):
    findings = []
    for path in iter_files(repo):
        rel = str(path.relative_to(repo))
        if is_credential_filename(path.name):
            findings.append({"bucket": "credential-write", "path": rel})
        try:
            text = read_sample(path)
        except Exception:
            continue
        for bucket, pattern in RISK_PATTERNS:
            if pattern.search(text):
                findings.append({"bucket": bucket, "path": rel})
    state = git_state(repo)
    buckets = sorted({f["bucket"] for f in findings})
    if any(b in buckets for b in ["destructive-recursive-delete", "credential-write", "shell-network-install"]):
        decision = "Red"
    elif state in {"dirty", "unavailable"} or buckets:
        decision = "Yellow"
    else:
        decision = "Green"
    return {
        "decision": decision,
        "repository": str(repo),
        "git_state": state,
        "risk_buckets": buckets,
        "findings": findings[:50],
    }


def as_markdown(result: dict) -> str:
    lines = [
        "## Agent Safety Preflight Receipt",
        "",
        f"- Decision: {result['decision']}",
        f"- Repository: {result['repository']}",
        f"- Git state: {result['git_state']}",
    ]
    lines.append("- Risk buckets: " + ", ".join(result["risk_buckets"] or ["none"]))
    lines.append("")
    lines.append("### Evidence")
    if result["findings"]:
        for item in result["findings"][:20]:
            lines.append(f"- `{item['bucket']}` in `{item['path']}`")
    else:
        lines.append("- No high-risk markers found by the lightweight scanner.")
    lines.append("")
    next_action = (
        "proceed with scoped edits"
        if result["decision"] == "Green"
        else ("checkpoint and narrow scope" if result["decision"] == "Yellow" else "stop for human review")
    )
    lines.append(f"- Next safe action: {next_action}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    result = scan(repo)
    print(json.dumps(result, indent=2) if args.format == "json" else as_markdown(result))


if __name__ == "__main__":
    main()
