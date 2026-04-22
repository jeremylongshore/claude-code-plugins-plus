# Tool Allowlist Enforcement

The tool allowlist — the list of tools an agent is allowed to call — is a
security boundary, not a suggestion. This reference covers how to make it
actually enforceable, the free-text ReAct trap that makes it advisory, and
the arg-level deny-list that stops the allowed tools from being weaponized.

## The free-text ReAct trap (P32)

The legacy ReAct pattern prompted the model with text like:

```
You have access to: lookup_order, lookup_shipment
Respond in this format:
Action: <tool_name>
Action Input: <json>
```

The agent parsed `Action: <name>` lines out of the response text. If the model
hallucinated `Action: shell_exec`, a permissive parser tried to call
`tools_by_name["shell_exec"]` — `KeyError`, or in a looser implementation,
fell through to a default handler. The allowlist was only as strong as the
parser's exception handling.

Provider-native tool calling (Anthropic's `tool_use`, OpenAI's
`function_calling`, Gemini's `function_calling`) replaces text parsing with a
structured API contract: the model returns a tool call object whose `name`
field is constrained by the server to the tool schema sent in the request.
The model physically cannot emit a tool name outside the bound list.

## The enforcement primitive — `create_react_agent`

LangGraph's prebuilt `create_react_agent` (1.0+) uses provider-native tool
calling. Bind the tools you want, and the provider enforces the allowlist:

```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by ID."""
    return db.fetch_order(order_id)

model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
agent = create_react_agent(model, tools=[lookup_order])
```

No parser, no string matching, no room for `shell_exec` to leak through. If
someone asks you to add a free-text ReAct agent to a production codebase,
treat it as a security review item — it is.

## Per-request allowlist for multi-tenant

In a multi-tenant SaaS, Tenant A may call `lookup_order` while Tenant B may
not. Bind tools per request:

```python
def agent_for_tenant(tenant_id: str):
    perms = permissions_for(tenant_id)
    tools = [t for t in ALL_TOOLS if t.name in perms.allowed_tools]
    return create_react_agent(model, tools=tools)

# Per-request
agent = agent_for_tenant(request.tenant_id)
result = agent.invoke({"messages": [("user", request.query)]})
```

Constructing a fresh agent per request is cheap (< 1ms) compared to the
model call. Do not cache by tenant — a deploy could leak tenants (see P33
in the pack pain catalog).

## Tool-arg deny-list

The allowlist covers tool *names*. Tool *arguments* are still free text
the model chooses. A `WebBaseLoader` tool called with a link-local URL
probes internal services:

| URL | What it probes |
|-----|----------------|
| `http://169.254.169.254/latest/meta-data/` | AWS instance metadata (IAM creds) |
| `http://metadata.google.internal/` | GCP instance metadata |
| `http://169.254.169.254/metadata/instance?api-version=2021-02-01` | Azure instance metadata |
| `http://127.0.0.1:6379/` | Local Redis |
| `file:///etc/passwd` | Local filesystem |
| `ftp://internal-share.corp/` | Internal FTP |

The defense is a Pydantic validator on every URL-accepting tool:

```python
from pydantic import BaseModel, HttpUrl, field_validator
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"docs.example.com", "api.example.com"}
BLOCKED_HOSTS = {
    "169.254.169.254", "127.0.0.1", "0.0.0.0", "::1",
    "localhost", "metadata.google.internal",
}
BLOCKED_CIDRS = [  # link-local + loopback
    "127.0.0.0/8", "169.254.0.0/16", "10.0.0.0/8",
    "172.16.0.0/12", "192.168.0.0/16",
]

import ipaddress

def _is_blocked_ip(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in ipaddress.ip_network(c) for c in BLOCKED_CIDRS)

class FetchArgs(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def _check_host(cls, v):
        host = urlparse(str(v)).hostname or ""
        if host in BLOCKED_HOSTS or _is_blocked_ip(host):
            raise ValueError(f"blocked host: {host}")
        if host not in ALLOWED_DOMAINS:
            raise ValueError(f"host not in allowlist: {host}")
        return v

@tool
def fetch_url(args: FetchArgs) -> str:
    """Fetch a web page. Only allowlisted domains permitted."""
    return requests.get(str(args.url), timeout=5).text
```

## Tool-arg patterns to reject

| Pattern | Reject because |
|---------|----------------|
| Shell metacharacters in a command-like arg: `;`, `\|`, `&&`, backticks | Arg is building a shell command — never let the model build shell commands |
| `../` in file paths | Path traversal |
| `file://`, `ftp://`, `gopher://` in URL args | SSRF / exfil |
| Raw SQL fragments in a "query" arg | SQL injection — use parameterized queries, not model-generated SQL |
| Arg length > 10KB | Prompt-injection via arg — inspect before use |

## Never: shell tools in production

A `run_shell(command: str)` tool is a security incident waiting to happen.
If you need command execution, use a sandboxed executor (gVisor, Firecracker,
a Docker container with read-only filesystem and no network) and an arg
allowlist so the model can only run predefined commands with parameterized
arguments:

```python
ALLOWED_COMMANDS = {
    "list_files": ["ls", "-la"],
    "check_disk": ["df", "-h"],
}

@tool
def sandboxed_command(name: str) -> str:
    """Run a preapproved read-only diagnostic command. Name must be one of: list_files, check_disk."""
    if name not in ALLOWED_COMMANDS:
        raise ValueError(f"unknown command: {name}")
    return subprocess.run(ALLOWED_COMMANDS[name], capture_output=True, text=True).stdout
```

The model chooses a command *name*, never builds a command *string*.

## Auditability

Every tool call should emit a structured log event: `{tool, args, tenant_id,
request_id, result_summary, duration_ms}`. In multi-tenant, partition logs
per tenant so an auditor can reconstruct the exact tool-call chain. Tie back
to the OTEL trace via `request_id` (see `langchain-observability`).

## Resources

- [LangGraph `create_react_agent`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)
- [OWASP LLM07 — Insecure Plugin Design](https://genai.owasp.org/llmrisk/llm07-insecure-plugin-design/)
- [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- Pack pain catalog: P32, P33, P50
