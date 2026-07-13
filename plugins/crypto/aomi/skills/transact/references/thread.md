# Thread Reference

Read this when:

- You need to know **where** conversation history, pending txs, or signed receipts live.
- `aomi tx list` returns `No active thread` and you need to recover the right thread.
- The user asks "what's in `~/.aomi/`?" or wants to clean up old threads.
- You're picking between `--new-session`, `aomi thread resume <N>`, and just letting the active thread continue.

## Two-tier storage model

A "thread" is split across two stores. Knowing what lives where prevents wrong-place lookups.

**Backend (the aomi server)** holds the durable record:

- The full conversation transcript (user prompts + assistant prose).
- All tool calls + tool outputs the agent made silently.
- System events (BYOK key changes, sponsorship decisions, etc.).
- Indexed by a `sessionId` UUID.

`aomi thread log`, `aomi thread events`, and the message replay in `aomi thread status` all hit the backend with the local `sessionId`. If the backend is unreachable or the sessionId is wrong, these will silently return empty or fail.

**Local on disk** (`$AOMI_STATE_DIR` if set, else `~/.aomi/`) holds the lookup keys and the parts the wallet flow needs:

- `sessionId` and `clientId` (UUIDs the backend uses to find the rest).
- `publicKey`, `chainId`, `baseUrl` (current wallet/chain/backend context).
- `pendingTxs[]` and `signedTxs[]` (full calldata, gas estimates, hashes — same data the backend has, mirrored locally so `aomi tx list` works without a network round-trip).
- `secretHandles{}` (handle names only — values are never stored locally).

The local state is what `aomi tx list`, `aomi tx sign`, and `aomi config current` read from. None of these touch the backend. (`aomi wallet ls` is the separate linked-wallets view: one table with address, chain, provider, signing mode, grant expiry, autonomous_ok, and primary.)

## File layout

```
~/.aomi/
├── active-session.txt              # one line, the local thread id (e.g. "43")
├── aa.json                         # AA config cache; usually "{}"
└── sessions/
    ├── session-1.json
    ├── session-2.json
    ├── ...
    ├── session-<N>.json            # one file per local thread
    ├── current.json                # rolling pointer/cache used by the REPL
    └── messages-cli-<unix-ns>.json # per-call message buffers (REPL streaming)
```

Each `session-<N>.json` is the local source of truth for that thread. Inspecting it is safe — it does not contain credential values, only handle names. Useful when debugging:

```bash
cat ~/.aomi/sessions/session-43.json | jq '{sessionId, chainId, publicKey, pending: (.pendingTxs|length), signed: (.signedTxs|length)}'
```

## The `active-session.txt` mechanic

`aomi tx list`, `aomi tx sign`, and `aomi tx simulate` all need an **active** thread. The active thread is just the local id stored in `~/.aomi/active-session.txt`. Set automatically by:

- `aomi --prompt "..."` (creates or reuses one)
- `aomi chat "..."` (same)
- `aomi --new-session ...` (creates a new one)
- `aomi thread new` (creates a new one, no chat)
- `aomi thread resume <id>` (sets active to an existing thread)

Cleared by `aomi thread close` and sometimes by errors mid-flight.

**The "No active thread" recovery pattern**: if `aomi tx list` reports no active thread, run `aomi thread list` to find the right thread by topic or pending count, then `aomi thread resume <N> > /dev/null && aomi tx list` in the same shell call (the active-thread pointer can be lost between subprocess invocations).

## Lifecycle: `--new-session` vs `resume` vs neither

Three rules, in order:

1. **Starting fresh work in a new assistant thread or terminal**: pass `--new-session` on the first chat command. Old thread context (pending txs from previous tasks, accumulated message tokens) won't bleed in.
2. **Continuing a task you started earlier (same thread)**: don't pass `--new-session`. The active thread persists across `aomi` invocations; the next `aomi chat "proceed"` lands in the same conversation.
3. **Picking up a previous thread by id**: `aomi thread resume <N>` first, then issue commands. Useful when `aomi tx list` shows pending txs you need to sign from a thread that was closed earlier (e.g. thread-43 in our run had pending Across txs after the shell rotated).

Account login is no longer nested under `wallet` or `account`: use `aomi login` for the browser/device flow, `aomi account` to inspect the active account, and `aomi wallet ls` to inspect linked wallets and signing policy.

## Cleanup hygiene

Threads accumulate. After a few weeks of use, `~/.aomi/sessions/` can hold 50–100+ files. Cleanup is safe:

```bash
aomi thread list                   # see what's there, with topics + pending counts
aomi thread delete <id>            # delete one — safe if no pending txs
aomi thread close                  # clear active pointer; next chat starts fresh
```

**Before deleting a thread, check it has no pending wallet requests** (`aomi tx list` after `aomi thread resume <id>`). Deleting a thread with pending txs orphans them — the backend may still know about them, but the local CLI loses the calldata and ids needed to sign.

`messages-cli-*.json` buffer files in `sessions/` are safe to remove manually — they're per-invocation REPL caches, not thread state.

The `secretHandles{}` block in a thread JSON is safe to read and inspect. The values they reference are stored on the backend, scoped to that thread's `clientId`. `aomi secret clear` removes them from the backend; deleting the thread locally does not.

## When to override the state dir

`AOMI_STATE_DIR` lets the user point the CLI at a non-default state root. Common reasons:

- Test setups: `AOMI_STATE_DIR=$(mktemp -d) aomi --prompt "..."` — clean slate per run, no contamination of the user's main `~/.aomi/`.
- Multiple identities: separate dirs for separate wallets / backends, switched via shell function or `direnv`.

The skill itself does not set this variable. If the user wants isolation, they configure it in their own shell.
