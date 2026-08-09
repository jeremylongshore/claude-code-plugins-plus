# Mailbox layout, envelope, and sweeper

**Scope note.** This document describes one implementation. It is not a specification: not versioned as
a wire format, not offered for adoption, not something to conform to. Two agents that share this
directory layout interoperate; that is the whole claim.

## Layout

```text
mailbox/
  <recipient-id>/
    inbox/      delivered, unclaimed
    claimed/    a reader has taken it, not yet resolved
    done/       processed successfully
    failed/     exhausted attempts; retained for inspection
```

One tree per recipient. State lives in the directory, so a message file carries no status field and no
state transition needs a write — only a rename. The rename is the transaction.

## Naming

```
<ISO8601-compact-UTC>-<writer>-<random>.json
20260809T120000Z-research-a3f9.json
```

Three components, each load-bearing:

- **Timestamp first** so lexicographic sort equals chronological sort. `ls` becomes an ordered read with
  no parsing.
- **Writer id** so two writers cannot collide on the same name. Timestamp plus random is not enough at
  second granularity under concurrency.
- **Random suffix** for the residual collision case within one writer.

Temporary files during the write window carry a dot prefix (`.tmp-<pid>-…`) so a reader's `*.json` glob
never sees them.

## Envelope

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | yes | Stable across retries — the idempotency key |
| `from` | yes | Writer id; matches the filename component |
| `to` | yes | Recipient id; matches the directory |
| `createdAt` | yes | ISO 8601 UTC |
| `attempts` | yes | Incremented on each claim; drives the poison-message cap |
| `correlationId` | no | Groups related messages, the way a context groups tasks |
| `body` | yes | Opaque to the mailbox — never parsed or validated by it |

The mailbox transports; it does not interpret. Schema validation belongs to the receiving agent, and
putting it in the mailbox couples the transport to every payload change.

### Prefer references to payloads

Put a **path or handle** in `body`, not the artifact:

```json
{ "body": { "digestPath": "runs/2026-08-09/digest.md", "sourceCount": 12 } }
```

Three wins. The mailbox stays small and greppable. The receiver spends no context on data it may not
need. The receiver decides what to read, which is the whole point of pull over push.

## Atomic write

```bash
tmp="mailbox/$to/inbox/.tmp-$$-$RANDOM"
printf '%s' "$envelope" > "$tmp"
mv "$tmp" "mailbox/$to/inbox/${ts}-${from}-${rand}.json"
```

Rename within one directory is atomic on POSIX filesystems. Writing directly into `inbox/` is the
defect this avoids: a reader globbing at the wrong moment consumes a truncated file, and the corruption
is silent because the file is syntactically plausible JSON right up until it is not.

## Claim protocol

```bash
src="mailbox/$me/inbox/$name"
dst="mailbox/$me/claimed/$name"
if mv "$src" "$dst" 2>/dev/null; then
  process "$dst"
else
  continue   # another reader won the race
fi
```

`mv` is the mutual-exclusion primitive. Exactly one rename of a given source succeeds. No lock file, no
lease, no coordination service — and no possibility of a lock outliving the process that took it.

## Resolution

Success moves to `done/`. Failure increments `attempts` and returns to `inbox/`, until the cap, at which
point it moves to `failed/` and stops.

## Sweeper

A periodic task with three jobs:

1. **Reclaim stale claims.** `claimed/` files older than the sweep timeout return to `inbox/`. Set the
   timeout above the longest legitimate processing time, or the sweeper competes with live readers and
   manufactures the duplicate work it exists to recover from.
2. **Prune `done/`.** A retention window measured in days. This is the bulk of the directory.
3. **Report `failed/`.** Never auto-prune on the same schedule as `done/`. `failed/` is the audit trail,
   and it is small by construction — if it is large, that is the finding.

Run the sweeper as a cron entry or a startup step. It holds no state, so a missed run costs latency and
nothing else.

## Permissions

Access control is filesystem permissions. A recipient's tree should be writable by its writers and
readable by its reader. There is no authentication layer, no signing, and no sender verification beyond
what the filesystem enforces — which is exactly why this belongs inside a trust boundary and not
across one.
