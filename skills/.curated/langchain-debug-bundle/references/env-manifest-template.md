# Environment Manifest Template

The first file in every debug bundle is `manifest.yaml` — a plain-text snapshot
that lets a colleague reproduce the exact environment on a different host.

## Non-negotiable rule

**Env-var names only, never values.** The manifest records that
`ANTHROPIC_API_KEY` was set, not what it was. Values go through the sanitization
pass ([sanitization-checklist.md](sanitization-checklist.md)) — but the safest
design is to never capture them in the first place.

## Exact shape

```yaml
bundle_spec_version: "1.0"
generated_at: "2026-04-21T18:42:17Z"
incident_id: "INC-2026-0421-A"    # free-form, link to ticket if any

runtime:
  python: "3.12.3"
  platform: "Linux-6.8.0-101-generic-x86_64"
  cpu_count: 8
  architecture: "x86_64"
  process:
    pid: 48231
    cwd: "/app"
    argv: ["python", "app/main.py"]

packages:                          # pip show output, one entry per relevant package
  - name: langchain-core
    version: "1.0.4"
  - name: langchain
    version: "1.0.3"
  - name: langgraph
    version: "1.0.2"
  - name: langchain-anthropic
    version: "1.0.3"
  - name: langchain-openai
    version: "1.0.5"
  - name: langsmith
    version: "0.1.52"
  - name: anthropic
    version: "0.42.0"
  - name: openai
    version: "1.57.0"
  - name: pydantic
    version: "2.10.3"

models:                            # discovered from running chain, not static
  - provider: anthropic
    model_id: "claude-sonnet-4-6"
    temperature: 0
    max_tokens: 4096
    timeout: 30

env_var_names_present:             # NAMES ONLY. Never values.
  - ANTHROPIC_API_KEY              # redacted: present=true
  - OPENAI_API_KEY
  - LANGSMITH_API_KEY
  - LANGSMITH_TRACING              # value captured only for this one (bool-safe)
  - LANGSMITH_PROJECT              # value captured (project name is not secret)
  - LANGSMITH_ENDPOINT

langsmith:
  tracing_enabled: true            # from LANGSMITH_TRACING env var
  project: "my-project"
  trace_url: "https://smith.langchain.com/public/<uuid>/r"   # from RunTree
  run_id: "<uuid>"

langgraph:                         # if a graph is running
  graph_name: "support_agent"
  thread_id: "thread-abc-123"       # REDACT if user-identifying
  checkpointer: "PostgresSaver"
  recursion_limit: 25
  current_node: "route_intent"     # last node that emitted

invocation:
  invoke_id: "inv-2026-0421-1842-xyz"
  started_at: "2026-04-21T18:42:10Z"
  duration_ms: 7342
  status: "error"                  # success | error | timeout | user_abort
  error_class: "GraphRecursionError"
  error_message: "Recursion limit of 25 reached without hitting a stop condition."

notes: |
  Free-form text from the on-call engineer. What they observed, what they tried,
  what the user reported. Sanitize manually — anything you type here is published.
```

## Population at runtime

```python
# ${CLAUDE_SKILL_DIR}/bundle_builder.py  -- conceptual, adapt to your app
import platform, sys, os, datetime, subprocess, json
from langchain import __version__ as lc_version

RELEVANT = [
    "langchain-core", "langchain", "langgraph",
    "langchain-anthropic", "langchain-openai", "langchain-google-genai",
    "langsmith", "anthropic", "openai", "pydantic",
]

def pip_show(name: str) -> str | None:
    """Read version from pip show. Returns None if not installed."""
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "show", name],
            stderr=subprocess.DEVNULL, text=True,
        )
        for line in out.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        return None

def build_manifest(incident_id: str, invoke_meta: dict) -> dict:
    return {
        "bundle_spec_version": "1.0",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "incident_id": incident_id,
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "architecture": platform.machine(),
            "process": {
                "pid": os.getpid(),
                "cwd": os.getcwd(),
                "argv": sys.argv,
            },
        },
        "packages": [
            {"name": n, "version": pip_show(n)} for n in RELEVANT
            if pip_show(n) is not None
        ],
        "env_var_names_present": sorted(
            name for name in os.environ
            if name.startswith(("LANGSMITH_", "LANGCHAIN_", "ANTHROPIC_", "OPENAI_", "GOOGLE_"))
        ),
        "langsmith": {
            "tracing_enabled": os.environ.get("LANGSMITH_TRACING", "").lower() == "true",
            "project": os.environ.get("LANGSMITH_PROJECT"),
        },
        "invocation": invoke_meta,
    }
```

Emit as YAML so humans can read it at triage time — JSON is fine if your tooling
prefers it, but the human reader is the primary consumer.

## What to NOT include

- API key values, even partial prefixes
- Raw user PII (names, emails, phone numbers) from prompts — that goes through
  [sanitization](sanitization-checklist.md)
- Full chat history beyond the failing invocation
- Database URIs with embedded credentials (`postgres://user:pass@host/db`)
- Internal hostnames or IPs of services not directly relevant to the incident

## Versioning

`bundle_spec_version` is pinned at the top. When the shape changes (new field,
renamed field), bump the spec and update the triage playbook — old bundles
stay readable under the old spec.
