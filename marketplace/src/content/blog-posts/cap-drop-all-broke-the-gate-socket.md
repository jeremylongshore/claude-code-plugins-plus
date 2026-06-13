---
title: "When --cap-drop ALL Broke the Gate Socket"
description: "Hardening a container hid a permission bug: --cap-drop ALL stripped CAP_DAC_OVERRIDE, and a gate socket silently stopped governing every tool call."
date: "2026-06-12"
tags: ["docker", "debugging", "ai-agents", "devops", "ci-cd"]
featured: false
---
The dogfood run went green. The gate had governed zero calls.

That is the agent-governance-plane's entire job: run an AI coding agent inside a sandbox, route *every* tool call through a Unix-domain-socket gateway, and write a signed, hash-chained journal of every allow/deny. A green run that gated nothing isn't a pass. It's a governance plane governing air.

## The gate that catches its own hollowness

AGP's CI dogfood doesn't just check that the harness exits 0. `evidence-bundle.sh` fails on a 0-gated run — if the journal shows no decisions, the build is red regardless of process exit status. That guard is what surfaced this at all: the agent process came up, the harness reported success, but the bundle had no verdicts to verify. Red.

That's the last I'll say about hollow-green detection here. It's the door, not the room. The room is *why* zero calls reached the gate, and the answer turned out to be a collision between two things that look unrelated until you trace the syscall: Linux capabilities and a Unix socket's permission bits.

## The wrong theory

The first hypothesis blamed the execution path. AGP has a dev-sandbox mode where the agent and the gate share a process, and a docker mode where the agent runs in a container talking to a host daemon over a bind-mounted socket. The theory was that the same-process path was short-circuiting the gate — agent and gate in one address space, the socket round-trip optimized away, decisions never journaled.

Plausible. Wrong. The dev-sandbox path journaled fine in isolation. The failure only appeared in docker mode, and the moment that became clear the investigation moved from "which code path" to "what's different about the container."

What's different about the container is the security posture.

## The real root cause: caps meet a missing write bit

The short version: connecting to a Unix domain socket needs *write* permission on the socket file. `--cap-drop ALL` strips `CAP_DAC_OVERRIDE` — the capability that lets root ignore permission bits — so the container's uid-0 process is bound by the socket's mode bits like any other user. Mode 0775 gave "others" no write, so `connect()` failed with `EACCES` and not a single tool call reached the gate.

The sandbox is hardened on purpose:

```bash
docker run \
  --cap-drop ALL \
  --network none \
  --read-only \
  -v "$GATE_SOCK:$GATE_SOCK" \
  agp-sandbox:latest
```

`--network none` so the agent can't exfiltrate. `--cap-drop ALL` so even though the agent runs as uid 0 inside the container, it holds none of root's privileged capabilities. Fail-closed by default. This is the posture you *want*.

The gate socket is an `AF_UNIX` socket created on the host by the AGP daemon, owned by the host user (a non-root uid), and bind-mounted into the container. Its mode was 0775:

```bash
$ ls -l /run/agp/gate.sock
srwxrwxr-x 1 agp agp 0 Jun 12 08:01 /run/agp/gate.sock
#  ^^^^^^^^^
#  owner rwx | group rwx | others r-x  ← others have NO write bit
```

Here is the part that bites. Connecting to a Unix domain socket is a *write* operation. From `unix(7)`:

> In order to connect to a socket, the connecting process needs to have **write** permission on the socket file.

Read permission is not enough. `connect(2)` on an `AF_UNIX` pathname checks the write bit against the calling process's credentials, exactly like opening a file for writing would.

Normally none of this matters for a root process, because root carries `CAP_DAC_OVERRIDE` — the capability that lets a process bypass all file read/write/execute permission checks. That single capability is the entire mechanism behind "root can touch any file." It is not magic in the kernel; it is a capability bit. When a process calls `connect()` on an `AF_UNIX` path, the kernel does a path lookup that ends in an inode permission check (`inode_permission` → `generic_permission`), and that check asks for `MAY_WRITE` on the socket inode. If the calling process fails the owner/group/other mode test, the kernel doesn't refuse immediately — it first checks whether the process holds `CAP_DAC_OVERRIDE`, and if so, waives the failure. Root "ignoring permissions" is literally this one branch.

Strip the capability and that branch never fires. The discretionary access control (DAC) mode bits become the final word.

`--cap-drop ALL` drops `CAP_DAC_OVERRIDE` along with everything else. So the in-container uid-0 process loses its permission-bypass crutch and becomes subject to ordinary mode bits like any unprivileged user. Walk the DAC check for that process against the socket:

- Is the process the socket's **owner**? No — the socket is owned by the host `agp` user (a non-root uid), and the container's uid-0 process is not `agp`. (Default Docker shares the host uid namespace, so this isn't a remapping artifact: uid 0 in the container *is* uid 0 on the host — it simply isn't the socket's owner.)
- Is the process in the socket's **group**? No.
- So it falls under **others**. Mode 0775 gives others `r-x`. **No write bit.**

`connect()` is refused with a permission error — `EACCES`, the kernel's way of saying "the mode bits don't allow this." The agent literally cannot reach the gate. Every tool call that should have been gated instead hit a socket it had no right to open. Zero calls reached the gate. Zero calls were governed. Green.

What makes this insidious is that none of the three obvious places you'd look were lying. The container started. The agent process was alive. The bind mount was present and the socket existed on both sides. `docker inspect` showed the mount, `ls` inside the container showed the socket node. Every surface said "wired up." The failure lived one syscall deeper than any of those checks reach — in the permission test that `connect()` runs and nothing else does.

The capability you dropped for security was the only thing papering over a file mode that was wrong all along. In dev-sandbox mode the agent ran as the host user, owned the socket, and never needed the override — which is exactly why the bug hid until the container posture exposed it.

## Why not the obvious fixes

There are three tempting ways out, and two of them are worse than the bug.

**Re-add `CAP_DAC_OVERRIDE`.** This works and is also exactly the wrong instinct. You'd be handing the sandboxed agent root's blanket permission-bypass to fix one socket's mode bit. The whole point of `--cap-drop ALL` is that the agent operates under least-privilege isolation, holding *nothing*. Punching a capability back in to dodge a `chmod` trades a hardened posture for a fragile one.

**Match the uids** so the container's uid 0 maps to the socket owner via `--user` or a userns remap. Now the fix depends on uid arithmetic staying aligned across the host daemon, the container runtime, and any future namespace config. That's a load-bearing coincidence waiting to drift: a namespace change down the road silently re-breaks `connect()`, trading a loud mode-bit error for a soft uid-mapping bug that only surfaces in production.

**Fix the one file mode.** The socket needs the write bit for "others" because the connecting process is, correctly, "others." That's a one-line `chmod`, and it's honest about what's actually being asked: let this socket be connected to.

The mode 0775 → 0777 change is safe here for reasons specific to what this socket *is*, per ADR 029:

- It is **local-only**. `--network none` plus a host bind mount means the socket never touches a network interface. World-connectable is bounded to processes already on this host.
- It carries **verdicts, not execution**. The protocol over the socket is allow/deny gate decisions. Connecting to it doesn't grant the ability to run anything; it grants the ability to *ask the gate and be told no*.
- Every decision is **journaled and signed**. An Ed25519 hash chain records each verdict; `agp verify` replays it offline. A rogue local connection can't forge a verdict that survives verification.

World-connectable on a single host, for a verdict-only, fully-audited socket, is a deliberate and narrow tradeoff — not a hole.

## The fix and the proof

`BunClaudeProcess`, the launcher for the Claude Code intendant, chmods the gate socket to 0777 before the container starts, so "others" gain the write bit and `connect()` succeeds:

```typescript
// BunClaudeProcess: widen the gate socket before launching the sandbox.
// Local-only, verdict-only, journaled — see ADR 029.
await chmod(socketPath, 0o777);
await runDockerSandbox({
  capDrop: "ALL",
  network: "none",
  binds: [`${socketPath}:${socketPath}`],
});
```

After the change:

```bash
$ ls -l /run/agp/gate.sock
srwxrwxrwx 1 agp agp 0 Jun 12 08:14 /run/agp/gate.sock
#         ^ others now have the write bit → connect() succeeds
```

Then the payoff. Real Claude Code, inside a `--cap-drop ALL` container, governed end-to-end:

```
gate verdicts (this run):
  Bash       → DENY
  Glob       → DENY
  ToolSearch → DENY
  Read       → ALLOW
gate decisions: 4 (3 deny, 1 allow)
agp verify: OK (rc=0, hash chain intact, 4 signatures valid)
```

Four gate decisions, not zero — three denials and one allow, each one signed. The denials landed, the allow landed, and the signed journal verified offline. To stop this regressing silently, a test asserts the socket is mode 0777 whenever the sandbox is in docker mode:

```typescript
test("docker-mode gate socket is world-connectable", async () => {
  const sock = await launchDockerSandbox();
  const { mode } = await stat(sock.path);
  // 0o777 — others need the write bit, because the container's
  // uid-0 process is "others" and connect() needs MAY_WRITE.
  expect(mode & 0o777).toBe(0o777);
});
```

If a future refactor narrows the mode again — say someone "hardens" it back to 0775 without tracing the syscall — this test goes red before the dogfood does, and the failure message points straight at the write bit instead of at a mysterious unreachable socket.

## The transferable rule

Inside a hardened, cap-dropped container, root is just another uid. The capability that used to bypass your file modes — `CAP_DAC_OVERRIDE` — is gone the instant you drop it, and dropping it is usually the right call. So your permission bits have to be *actually correct*, not correct-because-root-ignores-them. And remember that `connect()` on a Unix domain socket is a write: a socket that's only readable to a connecting process is a socket that process cannot use. The bug that looks like a broken code path is often a file mode that was always wrong and a privilege that was always hiding it.

## Also shipped

The same day, away from the gate socket:

- **braves** — taught the poller to survive "Delayed Start" game statuses and stop latching onto makeup games as if they were the scheduled matchup; added a SQLite fast-path for the batter game log.
- **claude-code-plugins** — added an advisory CI gate enforcing kernel↔vendor version coupling (V ≤ C ≤ K) so a vendor bump can't outrun the kernel it consumes.
- **claude-code-slack-channel** — bound a no-gaps journal invariant to production dispatch, hardened chunked-reply durability, and cleared an esbuild RCE advisory via a `tsx` bump.
- **jeremylongshore/.github** — fleet-wide pinned vps-deploy SHA bump chasing `actions/checkout@v6`.

## Related posts

- [When Green CI Proves Nothing](/posts/when-green-ci-proves-nothing/) — the gate that counts only counts what reaches it
- [Honor the Gate When the Verdict Is Inconvenient](/posts/honor-the-gate-when-the-verdict-is-inconvenient/)
- [HITL Delivery Is a Fail-Closed, Exactly-Once Problem](/posts/hitl-delivery-is-a-fail-closed-exactly-once-problem/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "When --cap-drop ALL Broke the Gate Socket",
  "description": "Hardening a container hid a permission bug: --cap-drop ALL stripped CAP_DAC_OVERRIDE, and a gate socket silently stopped governing every tool call.",
  "datePublished": "2026-06-12T08:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Start AI Tools",
    "logo": {
      "@type": "ImageObject",
      "url": "https://startaitools.com/images/og-image.png"
    }
  },
  "articleBody": "A hardened AI-agent sandbox passed CI green while governing zero tool calls. The cause: docker run --cap-drop ALL removes CAP_DAC_OVERRIDE, the Linux capability that lets a root process bypass file permission checks. connect() on a Unix domain socket requires the write bit, and the gate socket's mode 0775 gave 'others' none — so the container's uid-0 process could not reach the gate. The fix is to chmod the local, verdict-only, journaled socket to 0777 before launching the container.",
  "keywords": ["docker", "debugging", "ai-agents", "devops", "ci-cd", "linux-capabilities", "unix-socket", "container-hardening"]
}
</script>
