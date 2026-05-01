# Access Control Schema

The Slack channel uses `~/.claude/channels/slack/access.json` to control who can reach your Claude Code session.

## Schema

```json
{
  "dmPolicy": "pairing | allowlist | disabled",
  "allowFrom": ["U12345678"],
  "channels": {
    "C12345678": {
      "requireMention": true,
      "allowFrom": ["U12345678"],
      "allowBotIds": [],
      "audit": "off"
    }
  },
  "pending": {
    "ABC123": {
      "senderId": "U87654321",
      "chatId": "D12345678",
      "createdAt": 1711000000000,
      "expiresAt": 1711003600000,
      "replies": 1
    }
  },
  "ackReaction": "eyes",
  "textChunkLimit": 4000,
  "chunkMode": "newline"
}
```

## Fields

### `dmPolicy`
Controls how DMs from unknown users are handled.

| Value | Behavior |
|-------|----------|
| `allowlist` | Only users in `allowFrom` can DM; others are silently dropped (default in this hardened fork) |
| `pairing` | Unknown senders get a 6-character code to approve via `/slack-channel:access pair` (upstream default; opt-in only) |
| `disabled` | All DMs dropped |

> **Note — default is `allowlist`:** this fork defaults to `allowlist` instead
> of the upstream `pairing` default. The pairing flow lets any workspace
> member DM the bot, receive a pairing code, and then socially-engineer the
> operator into pasting `/slack-channel:access pair <code>`. To avoid that
> foothold, the operator must explicitly add their own Slack user ID to
> `allowFrom` before DMs will reach the bot:
>
> ```
> /slack-channel:access add U01234567
> ```
>
> Replace `U01234567` with your Slack user ID (visible from your Slack
> profile → More → Copy member ID). There is no longer a self-service
> pairing-code emission by default. To temporarily re-enable the pairing
> flow — for example, to onboard an additional trusted user — edit
> `~/.claude/channels/slack/access.json` and set `dmPolicy` to `pairing`,
> then switch it back to `allowlist` afterwards.

### `allowFrom`
Array of Slack user IDs (e.g., `U12345678`) allowed to send DMs. Managed via `/slack-channel:access add/remove`.

### `channels`
Map of channel IDs to policies. Only channels listed here are monitored.

- `requireMention`: If true, only messages that @mention the bot are delivered
- `allowFrom`: If non-empty, only these user IDs are delivered from this channel
- `allowBotIds`: Opt-in list of bot user IDs allowed to deliver messages in this channel. Absent or empty (default) = all bot messages dropped. See "Multi-agent coordination" below.
- `audit`: Audit-log projection mode for this channel. See "Audit projection (`audit`)" below. Absent or `'off'` (default) = no projection. Values: `'off'` | `'compact'` | `'full'`.

### Multi-agent coordination (`allowBotIds`)

By default, every message with a `bot_id` is dropped at the gate to prevent bot-loop amplification and unintended interactions with third-party integrations (Zapier, PagerDuty, GitHub, etc.). Channels that need to host multiple cooperating agents — for example, an ops-monitor bot and an engineering bot coordinating in an `#incidents` channel — opt in by listing specific bot user IDs in `allowBotIds`.

```json
"channels": {
  "C_INCIDENTS": {
    "requireMention": false,
    "allowFrom": ["U_OPS_BOT", "U_ENG_BOT", "U_HUMAN"],
    "allowBotIds": ["U_OPS_BOT", "U_ENG_BOT"]
  }
}
```

Only bot user IDs explicitly listed in `allowBotIds` can deliver bot messages. Every other bot is dropped. Additional invariants enforced at the gate:

- **Self-echo** from this bot is always filtered — even if its own user ID appears in `allowBotIds`. Filtering matches on `bot_id`, `bot_profile.app_id`, or `user === botUserId` to cover payload variants (including `as_user=false` posts and multi-workspace installs).
- **Permission-reply-shaped messages** from peer bots (`y abcde`, `no xyzwq`) are dropped at the gate before reaching the permission relay. Peer bots cannot approve tool calls regardless of `allowBotIds` membership — the permission relay additionally requires the approver to be in the top-level `allowFrom`.
- **`requireMention` and `allowFrom`** still apply. `allowBotIds` only gets a peer-bot message past the default `bot_id` drop; the usual channel gating runs afterward.
- **DMs** are unaffected. `allowBotIds` is channel-scoped; bot messages in DM channels are always dropped.

> **Security note:** Only add bot user IDs you operate or trust. A peer bot's messages reach Claude with the same effective trust as human messages, and a compromised peer bot can attempt prompt injection. The system prompt treats peer-bot content as untrusted, but that's a last-line defense — the first line is you being deliberate about what's in `allowBotIds`. Cross-bot delivery requires explicit opt-in precisely so operators have to think about this tradeoff before enabling it.

### Audit projection (`audit`)

Per-channel setting that controls whether tool-call decisions are mirrored into the Slack thread where they were issued. The **authoritative** audit record always lives in the hash-chained local journal at `~/.claude/channels/slack/audit.log` — see [`000-docs/audit-journal-architecture.md`](000-docs/audit-journal-architecture.md). The `audit` field here controls a *projection* of those journal events into Slack so operators can see what Claude is doing in the same thread they're reading.

Three modes:

| Mode | Projection | Content |
|---|---|---|
| `'off'` (default) | None. Zero Slack messages from the projection layer. | — |
| `'compact'` | One threaded receipt per approved tool call. | `:receipt: <tool>` + correlation ID. No tool inputs. |
| `'full'` | Same as compact plus a redacted preview of the tool's inputs. | `:receipt: <tool>` + `input_preview` (redacted per 30-A) + correlation ID. |

Example:

```json
"channels": {
  "C_DEPLOY": {
    "requireMention": false,
    "allowFrom": ["U_OPERATOR"],
    "audit": "compact"
  }
}
```

**Invariants:**

- **Default-safe.** Absent or `'off'` = no projection. No existing channel starts posting receipts on upgrade.
- **Projection never blocks execution.** If Slack's API is flaky, rate-limited, or returns an error, the receipt post is skipped and the tool call still runs. Failures are logged to stderr only. The authoritative journal is unaffected.
- **Receipt ≠ outcome.** A receipt means "this tool call passed policy and was allowed to run." Whether it *succeeded* is not something the bridge observes — MCP's permission relay carries no completion signal. For real outcomes, inspect the local journal with `bun server.ts --verify-audit-log <path>`.
- **Self-echoes stay filtered.** If a channel opts into both `audit` and `allowBotIds`, the bot's own receipts don't loop through its own gate. Locked in by Epic 30-B.8.

> **PII warning for `'full'` mode:** tool `input_preview` is a string representation of the first ~200 chars of whatever Claude passed the tool. For `Read`/`Write`/`Bash` calls this usually includes file paths or command fragments; for text-generation tools it can include arbitrary user-authored content. The 30-A redaction layer scrubs known token patterns (API keys, GitHub tokens, etc.) but cannot catch unstructured PII. Only enable `'full'` in channels where the expected content is acceptable for the audience of that channel.

### `pending`
Active pairing codes. Auto-pruned on every gate check.

- Max 3 pending codes at once
- Each code expires after 1 hour
- Max 2 replies per code (initial + 1 reminder)

### `ackReaction`
Emoji name (without colons) to react with when a message is delivered. Set to `""` or omit to disable.

### `textChunkLimit`
Maximum characters per outbound message. Default: 4000 (Slack's limit).

### `chunkMode`
How to split long messages: `"newline"` (paragraph-aware, default) or `"length"` (fixed character count).

## Security

- File permissions: `0o600` (owner read/write only)
- Writes are atomic (write `.tmp`, then rename)
- Corrupt files are moved aside and replaced with defaults
- In static mode (`SLACK_ACCESS_MODE=static`), the file is read once at boot and never mutated

## State directory layout

All plugin state lives under `~/.claude/channels/slack/`. Files are mode `0o600`, directories `0o700` — owner-only access. The plugin is single-writer per state directory; running two plugin instances against the same directory is undefined behavior.

```
~/.claude/channels/slack/
├── .env                        # tokens (xoxb / xapp), SLACK_SENDABLE_ROOTS, SLACK_ACCESS_MODE   (0o600)
├── access.json                 # this file — allowlist, pairing codes, per-channel policy        (0o600)
├── inbox/                      # downloaded attachments, auto-allowed for re-share via `reply`   (0o700)
└── sessions/                   # per-thread conversation state (v0.5.0+)                          (0o700)
    ├── .migrated               # sentinel: migrator has run; future boots skip the scan          (0o600)
    ├── C0123456789/            # one directory per Slack channel ID
    │   ├── default.json        #   migrated flat pre-0.5.0 session, if the channel had one       (0o600)
    │   ├── 1700000000.000100.json   # one file per thread_ts                                     (0o600)
    │   └── 1700000500.000200.json   #                                                            (0o600)
    └── D0987654321/            # DMs use the same per-channel layout (channel ID starts with D)
        └── 1700000100.000300.json
```

### How thread-scoping works

A **session** is the unit of conversation state. One session corresponds to one Slack thread — **not** one channel. Two parallel threads in the same channel get two independent sessions and never observe each other's state.

- `channel` — Slack channel ID, e.g. `C0123456789` (channel) or `D0123456789` (DM).
- `thread` — `thread_ts` from the Slack event. For top-level (non-threaded) messages, the plugin synthesises `thread = ts` of the root message, so the first reply anchors the thread naturally.

Session files are **self-describing**: each JSON file duplicates the `(channel, thread)` key inside the file body. A moved or copied session file stays traceable under forensic inspection.

### Migration from v0.4.x

Pre-0.5.0, the plugin kept one file per channel at `sessions/<channel>.json`. The migrator runs once at boot:

- Finds each `sessions/*.json` that is a regular file.
- Creates `sessions/<channel>/` at mode `0o700`.
- Moves the legacy file to `sessions/<channel>/default.json` (atomic rename; mode preserved).
- Drops `sessions/.migrated` so subsequent boots no-op.

Existing conversations that predate thread-scoping surface as the `default` thread and continue without context loss. If the migrator encounters a partial prior migration (per-channel dir already exists), it leaves the legacy file in place and surfaces the conflict rather than clobber.

### Safety invariants

- **Realpath-guarded joins.** Every path is validated against `/^[A-Za-z0-9._-]+$/` and additionally rejected if the component is exactly `.` or `..` (both match the regex but would escape the `sessions/` layer via `path.join`). After the per-channel directory is created, `realpath` resolves it and the plugin verifies the state root is still a prefix — catches symlink-based smuggling (CWE-22).
- **Atomic writes.** Every session save is `writeFile(<path>.tmp.<pid>, {flag: 'wx', mode: 0o600})` → `chmod 0o600` → `rename`. Readers never observe a partial file; the `wx` flag makes a stale `.tmp.*` from a crashed prior writer a loud failure rather than a silent overwrite.
- **Fail-closed loader.** `loadSession` realpaths the file before reading; any containment breach or malformed JSON throws and the supervisor Quarantines the session. No silent degradation to an empty session.

Full design reference: [`000-docs/session-state-machine.md`](000-docs/session-state-machine.md).

## Policy schema (v0.5.0+)

A **policy** decides whether an MCP tool call proceeds, is denied, or requires a human approver. Policies are authored as JSON and validated at load with a Zod schema. The evaluator (`evaluate()` in `policy.ts`) is pure and uses first-applicable combining — the first rule whose `match` applies wins. See [`000-docs/policy-evaluation-flow.md`](000-docs/policy-evaluation-flow.md) for the full decision procedure and worked examples.

### PolicyRule

```ts
type PolicyRule =
  | { id: string; effect: 'auto_approve';     match: MatchSpec; priority?: number }
  | { id: string; effect: 'deny';             match: MatchSpec; priority?: number; reason: string }
  | { id: string; effect: 'require_approval'; match: MatchSpec; priority?: number; ttlMs?: number; approvers?: number }
```

- **`id`** — stable, human-readable. Shows up in the audit journal and any error surfaced to Claude. Duplicate ids are a load-time error.
- **`effect`** — one of three: `auto_approve` (allow without prompting), `deny` (refuse with a non-sensitive reason string), `require_approval` (hold until human approver(s) respond on Slack within `ttlMs`).
- **`priority`** — default `100`. Position in the policy array is the *primary* sort key (first-applicable). `priority` is a tie-breaker *within effect* when two rules would otherwise be equivalent — not a global sort.
- **`reason`** (deny only) — 1–200 chars, surfaced to Claude so the model knows why the call was rejected. Keep non-sensitive.
- **`ttlMs`** (require_approval only) — approval freshness window. Default 5 minutes, hard ceiling 24 hours. Once granted, an approval auto-approves subsequent matching calls in the same `(rule, sessionKey)` until expiry.
- **`approvers`** (require_approval only) — quorum threshold. Default `1` (single-approver). Accepts 1–10. When ≥2, votes accumulate with NIST two-person integrity: the server dedups on verified Slack `user_id` (never display name) so the same human cannot double-satisfy quorum. A single `deny` vote from any allowlisted user rejects the request immediately regardless of the quorum count — one "no" overrides any number of "yes" answers.

#### Boot-time linters

The loader runs three checks at boot; all are warn-not-block except parse errors:

1. **Duplicate-id detection** — fatal at boot. Two rules sharing an `id` cannot coexist.
2. **Shadow detection** — warning. Flags later rules made unreachable by an earlier, less-specific rule. Operators may intentionally author unreachable rules (placeholders during refactors) so this is informational.
3. **Broad-auto-approve linter** (ccsc-me6.7) — warning. Flags `auto_approve` rules whose `match` lacks both `tool` and `pathPrefix`. Without one of those, the rule auto-approves *any* tool call within its scope — almost always a misconfiguration. Narrow the rule or convert to `require_approval`.

### MatchSpec

```ts
type MatchSpec = {
  tool?:       string              // exact MCP tool name, e.g. "upload_file"
  pathPrefix?: string              // canonicalized via realpath before compare (CWE-22 safe)
  channel?:    string              // Slack channel ID, ^[CD][A-Z0-9]+$
  actor?:      'session_owner' | 'claude_process'
  argEquals?:  Record<string, unknown>   // subset-equality on validated MCP input args
}
```

**At least one field must be constrained.** A match that restricts zero fields (either literally `{}` or `{ argEquals: {} }`) is a load-time error — a rule that matches every call is almost always a bug.

- **`tool`** — exact match only; no globbing.
- **`pathPrefix`** — compared after `realpath` resolves both sides; `/etc/passwd` does **not** match prefix `/etc/pass` (there's a `+ sep` guard). A rule pointing at a nonexistent path is a load-time error.
- **`channel`** — Slack IDs starting with `C` (channel) or `D` (DM). Validated against `^[CD][A-Z0-9]+$`.
- **`actor`** — who is calling the tool. `session_owner` is the human at the terminal; `claude_process` is the Claude Code session. Human approvers arrive as a later turn (permission reply) and are never the `actor` on the original call.
- **`argEquals`** — subset equality on the MCP input object. Every listed key must match the call's input. Comparison is structural (JSON round-trip) — suitable for plain-JSON values only.

### Default-branch behavior

When no rule matches:

- **Deny** — if the tool is in the `requireAuthoredPolicy` set (`['upload_file']` by default; grows as dangerous tools are added). Decision: `{ kind: 'deny', rule: 'default', reason: 'no policy authored for …' }`.
- **Allow** — otherwise. Decision: `{ kind: 'allow' }` (no `rule` field, since no rule matched).

The evaluator is a **veto layer**, not the sole gate. Even an allowed decision still flows through `assertOutboundAllowed` and `assertSendable` downstream — the policy engine is additional authorization, never sole authorization.

### Safety checks the loader runs

- **Schema validation** — Zod rejects malformed rules with structured errors naming the field and id.
- **Duplicate-id rejection** — two rules sharing an `id` fail load.
- **Shadow-detection linter** — warns (doesn't block) when a later rule is unreachable because an earlier rule's match is less-specific-or-equal on every field. Warnings go to stderr + audit log; operator sees them at boot and in CI.
- **Monotonicity invariant** — on hot reload, refuses to adopt a policy set that contains a new `auto_approve` rule whose match is covered by an existing `deny`. Fail-closed because an accidental weakening reload is the exact shape of an attack via operator coercion.

### Where policies live

Policies live under the top-level `policy` key in `access.json` (same file as `dmPolicy`, `allowFrom`, `channels`). The server parses and validates them **once at boot** via `parsePolicyRules()`; `detectShadowing()` runs and emits warnings to stderr. A malformed rule or a duplicate id is **fatal at boot** — the server exits with a descriptive error message. Silent degradation to "no policy" is not offered: policy enforcement is safety-critical, so a parse failure demands operator action rather than opening a hole.

```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["U012AB3CD4E"],
  "channels": { "C0123456789": { "replyAllowedFrom": [] } },
  "pending": {},
  "policy": [
    { "id": "safe-reads", "effect": "auto_approve", "match": { "tool": "read_file", "pathPrefix": "/workspace/docs" } },
    { "id": "no-shell",   "effect": "deny",         "match": { "tool": "run_shell" }, "reason": "Shell execution is not permitted from this channel." }
  ]
}
```

A missing or empty `policy` field means "no authored rules" and is **not** an error — the evaluator applies defaults (allow most tools, deny tools in `requireAuthoredPolicy` like `upload_file`). This is the first-install path.

**Hot reload is intentionally not supported** (see `000-docs/v0.6.0-release-plan.md` §R3). Operators restart the server to apply new rules. The `checkMonotonicity()` invariant is reserved for a future hot-reload path; landing one now would require a signal handler and a drain-in-flight-approvals protocol that v0.6.0 deliberately defers.

Epic 29-B wired the loader and the `evaluate()` call into the permission-relay handler. The wiring lives in `server.ts` at the `PermissionRequestSchema` handler — see the `decidePermissionRoute()` helper in `lib.ts` for the pure decision-routing logic.

### Authoring rules without hand-editing

The `/slack-channel:policy` skill (`skills/policy/SKILL.md`) is the ergonomic front door to authoring rules. It wraps atomic `access.json` writes with pre-write validation via `scripts/policy-validate.ts`, which runs the same `parsePolicyRules()` + `detectShadowing()` + `detectBroadAutoApprove()` functions the server uses at boot. Subcommands: `list`, `lint`, `add <id> <effect> <json-match> [opts]`, `remove <id>`. The skill complements the hand-edit path; it does not replace it. Hot reload remains unsupported — every successful mutation ends with a "restart the server" notice.

## File attachments — sendable roots

The `reply` tool can attach files to Slack messages, but only files whose
real path (symlinks resolved) sits under an **explicit allowlist of roots**.

### Default allowlist

- `~/.claude/channels/slack/inbox/` — always allowed; re-shares previously
  downloaded attachments.

### Adding additional roots

Set `SLACK_SENDABLE_ROOTS` in `~/.claude/channels/slack/.env` to a
colon-separated list of absolute paths:

```env
SLACK_SENDABLE_ROOTS=/Users/you/projects/report-outputs:/tmp/claude-artifacts
```

- Paths must be absolute; relative entries are silently dropped.
- **Every configured path must exist and be readable at server startup.** The
  server fails fast (`process.exit(1)` with a message listing each bad path)
  if any entry cannot be `realpath`-resolved — missing directory, broken
  symlink, or permission denied. Fix the path or remove it from `.env` and
  restart. This closes a TOCTOU window where a post-boot symlink could flip
  a previously-inaccessible root into a structurally different check.
- Symlinks are followed via `realpath` before the allowlist check, so
  symlinking a secret file into an allowed root will not bypass the guard.
- The guard also applies a **basename denylist** that rejects common secret
  filenames even inside allowlisted roots:
  `.env`, `.env.*`, `.netrc`, `.npmrc`, `.pypirc`, `*.pem`, `*.key`,
  `id_rsa` / `id_ecdsa` / `id_ed25519` / `id_dsa` (and `.pub`),
  `credentials`, `credentials.*`, `.git-credentials`.
- Any path descending through `.ssh`, `.aws`, `.gnupg`, `.config/gcloud`,
  `.config/gh`, or `.git` is rejected.
- Paths containing a `..` component are rejected.

If the reply tool tries to attach a path outside the allowlist (or on the
denylist), the upload is blocked with a generic error that names WHICH
check failed but does not echo the attempted path.
