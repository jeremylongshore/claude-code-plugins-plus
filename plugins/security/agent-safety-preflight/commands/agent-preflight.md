---
name: agent-preflight
description: Generate a lightweight repository risk receipt before AI-agent edits
shortcut: apf
---
# Agent Safety Preflight

Generate a local, auditable preflight receipt before Claude Code or another AI coding agent changes a repository.

## What You Do

1. Identify the repository root. Use the current workspace unless the user supplied a path.
2. Run the bundled lightweight scanner when possible. Do not assume the current working directory is the plugin package; the user is usually inside the repo being checked.

Use this local-only bootstrap:

```bash
python3 - <<'PY'
from pathlib import Path
import subprocess
import sys

repo = Path.cwd()
trusted_roots = [Path.home() / ".claude", Path.home() / ".config" / "claude"]
patterns = (
    "**/agent-safety-preflight/scripts/agent_preflight_lite.py",
    "**/agent_preflight_lite.py",
)
candidates = []
seen = set()
for root in trusted_roots:
    if not root.exists():
        continue
    try:
        trusted_root = root.resolve()
    except OSError:
        continue
    for pattern in patterns:
        for scanner in root.glob(pattern):
            try:
                resolved = scanner.resolve()
            except OSError:
                continue
            if not resolved.is_relative_to(trusted_root) or resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(resolved)

for scanner in candidates:
    if scanner.is_file():
        raise SystemExit(subprocess.call([sys.executable, str(scanner), "--repo", str(repo), "--format", "markdown"]))

print("Bundled agent_preflight_lite.py was not found from this workspace.")
print("Use the manual decision rules in this command; do not claim an automated scan ran.")
PY
```

If the scanner cannot be located, use the manual decision rules below instead of sending code, secrets, or repository contents anywhere.

Then continue:

1. Inspect the receipt and classify the repo as Green, Yellow, or Red.
2. Tell the user the decision, the evidence, and the next safe action before making edits.

## Decision Rules

- **Green**: clean git state and no high-risk automation markers found. Routine agent edits can proceed after the user confirms scope.
- **Yellow**: uncommitted changes or medium-risk hooks/agent config are present. Ask for a checkpoint or narrower scope before broad edits.
- **Red**: destructive command patterns, credential-writing automation, or risky shell/network install chains appear in agent-controlled paths. Stop and ask for human review before editing.

## Output Format

```markdown
## Agent Safety Preflight Receipt

- Decision: Green | Yellow | Red
- Repository: <path>
- Git state: <clean/dirty/unavailable>
- Risk buckets: <bullets>
- Evidence: <file/path markers>
- Next safe action: <proceed/checkpoint/stop>
```

## Safety Boundaries

This command is local-first and read-only. Do not exfiltrate files, secrets, tokens, private source, payment credentials, or environment variables. Do not perform security testing against third-party systems.

## More Complete Free Workflow

For the full open-source scanner, sample receipts, and maintainer handoff examples, use:

<https://github.com/el-zachariah/ai-agent-safety-starter-pack>
