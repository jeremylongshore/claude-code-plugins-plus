/**
 * supervisor.ts — Session supervisor interface for the MCP server.
 *
 * This file is the Epic 32-B entry point. It declares the shape of the
 * SessionSupervisor actor — the single component allowed to create,
 * transition, or destroy sessions — without providing a runtime. The
 * activate / quiesce / deactivate implementations land in sibling beads
 * (ccsc-xa3.2, ccsc-xa3.3, and the deactivate + reaper beads under
 * ccsc-xa3.14). See 000-docs/session-state-machine.md §221-267 for the
 * full behavioural contract this interface pins down, and Armstrong
 * (2003) for the supervisor / lifecycle pattern it borrows from.
 *
 * Design notes:
 *
 *   - **Actor, not a library.** Every mutation of a live session flows
 *     through a single SessionSupervisor owned by server.ts. lib.ts
 *     primitives (sessionPath, saveSession, loadSession) are called only
 *     from here. A session file written by any other path is a bug.
 *
 *   - **One mutex per session file.** Two Slack threads in the same
 *     channel are independent; their handles carry independent mutexes.
 *     The supervisor guarantees serialised `update()` calls per key, not
 *     per channel.
 *
 *   - **Crash is not data loss.** The on-disk file is the source of
 *     truth. In-memory handles are caches. If the process crashes mid-
 *     flight, the next inbound event for that key re-enters Activating
 *     and re-reads the file (see session-state-machine.md §239-247).
 *
 *   - **No policy, no gate, no journal.** The supervisor decides when a
 *     session is loaded, held, flushed, or quarantined — it does not
 *     decide who can speak (inbound gate), which tools run (Epic 29-B),
 *     or what gets logged (Epic 30-A). Those subsystems observe session
 *     state; they never mutate it.
 *
 * SPDX-License-Identifier: MIT
 */

import type { JournalWriter } from './journal'
import type { Session, SessionKey } from './lib'
import { loadSession, saveSession, sessionPath } from './lib'

// ---------------------------------------------------------------------------
// Lifecycle state
// ---------------------------------------------------------------------------

/** Observable lifecycle state for one session, mirroring the five-state
 *  FSM in 000-docs/session-state-machine.md §109-155. Nonexistent is
 *  implicit (no handle) so it is not an enumerated value here.
 *
 *  Transitions are strict and are the supervisor's responsibility — the
 *  doc diagram is authoritative, this type is descriptive.
 *
 *    - `activating`   — load-or-create in progress; single-writer critical
 *                       section. Callers of activate() observe this only
 *                       through the returned Promise resolving.
 *    - `active`       — handle is live, `session` reflects the on-disk
 *                       file after the most recent `update()`.
 *    - `quiescing`    — refusing new work; pending writes still flushing.
 *                       `update()` rejects.
 *    - `deactivating` — last flush resolved; handle about to be released.
 *                       Terminal from the caller's perspective.
 *    - `quarantined`  — save or load failure; supervisor filed a beads
 *                       issue and will not auto-reload. Only a human
 *                       (SO) clears this; see session-state-machine.md
 *                       §132-137.
 */
export type SessionState = 'activating' | 'active' | 'quiescing' | 'deactivating' | 'quarantined'

// ---------------------------------------------------------------------------
// SessionHandle — in-memory wrapper around one Session file
// ---------------------------------------------------------------------------

/** Live handle to one session. Returned by `SessionSupervisor.activate()`.
 *
 *  Callers treat the handle as opaque: read `session` for the current
 *  snapshot, call `update()` to persist a change. The handle enforces
 *  serialised writes through an internal mutex keyed on this session's
 *  path — two concurrent `update()` calls on the same handle run in
 *  strict order (see session-state-machine.md §210 invariant 1).
 *
 *  A handle is valid only while `state === 'active'`. Once quiesce has
 *  started, `update()` rejects; callers must re-activate to resume.
 */
export interface SessionHandle {
  /** Identity. Immutable for the lifetime of the handle. */
  readonly key: SessionKey

  /** Lifecycle state of this handle as observed by the supervisor.
   *  Consumers may read but must not assume state is stable between
   *  awaits — the reaper or a shutdown signal can transition the
   *  handle out from under them. Always re-check after an `await`. */
  readonly state: SessionState

  /** Most recent successfully persisted snapshot of this session. The
   *  reference may point to frozen / read-only data; callers must not
   *  mutate it in place. Produce the next version inside `update()`. */
  readonly session: Session

  /** Serialise an update through the per-session mutex, persist it via
   *  the atomic writer (`saveSession()`), and refresh `this.session`.
   *
   *  Contract:
   *    - `fn` receives the current session and returns the next one.
   *      It must be pure — no I/O, no sleeps, no throwing except to
   *      signal a validation failure that should abort the update.
   *    - The supervisor persists the returned value with the atomic
   *      writer. Partial state never lands on disk.
   *    - On save failure the handle transitions to `quarantined` and
   *      the returned promise rejects. In-memory `session` reverts to
   *      the pre-update value; no consumer ever sees the failed draft.
   *    - While `state !== 'active'` the promise rejects without
   *      calling `fn`. */
  update(fn: (prev: Session) => Session): Promise<void>
}

// ---------------------------------------------------------------------------
// SessionSupervisor — the actor contract
// ---------------------------------------------------------------------------

/** Supervisor for the per-thread session population. There is exactly one
 *  `SessionSupervisor` per MCP server process; it owns the
 *  `Map<SessionKey, SessionHandle>` named in session-state-machine.md
 *  §229 and is the only code permitted to drive state transitions on
 *  that map.
 *
 *  Armstrong-style shape: the supervisor is a long-lived actor that
 *  delegates work to short-lived per-session children (the handles).
 *  Crashes of a single session are isolated — quarantine a handle, keep
 *  serving every other key. Crashes of the supervisor itself restart
 *  the whole population from disk (see §239-247).
 *
 *  The supervisor is **not** responsible for deciding whether an inbound
 *  event reaches Claude (that is the inbound `gate()` in lib.ts), for
 *  deciding whether a tool call runs (policy evaluator, Epic 29), or
 *  for persisting the audit log (journal sink, Epic 30). It is a pure
 *  session-lifecycle authority.
 */
export interface SessionSupervisor {
  /** Activate the session for `key`: load the file if it exists, create
   *  an empty one if not, and return a live handle.
   *
   *  `initialOwnerId` is the Slack user ID to record as `ownerId` on a
   *  newly-created session file. It is consulted **only** on the create
   *  branch; if the session file already exists, the stored owner wins
   *  and the argument is ignored. A caller that knows the session
   *  already exists may omit it. A caller that cannot vouch for owner
   *  (supervisor rehydration on boot, internal bookkeeping) may omit it
   *  as well — activate() will then reject if the file is missing,
   *  rather than synthesize an owner.
   *
   *  Contract:
   *    - Idempotent per key. Two concurrent activate() calls for the
   *      same key return the same handle (single-flight, per
   *      session-state-machine.md §266).
   *    - While loading/creating the handle observes `state =
   *      'activating'`; the returned promise resolves only after the
   *      handle reaches `active`.
   *    - Load failure on an existing file transitions to `quarantined`
   *      and rejects the promise; the supervisor files a beads issue
   *      for the SO and never auto-retries.
   *    - Path-validation failure (realpath escape, bad SessionKey
   *      component) rejects before any on-disk work; no session is
   *      recorded for the key.
   *    - Does not enforce idle TTL. Reaper logic lives in the deactivate
   *      path, not here. */
  activate(key: SessionKey, initialOwnerId?: string): Promise<SessionHandle>

  /** Refuse new work on `key` and wait for pending writes to flush.
   *
   *  Contract:
   *    - After `quiesce()` begins, `update()` on the associated handle
   *      rejects. New `activate()` calls for the same key wait for
   *      quiesce to complete, then re-activate from disk.
   *    - A new inbound event may cancel the quiesce and return the
   *      handle to `active`, per session-state-machine.md §124 (the
   *      `Quiescing → Active` transition). That decision is the
   *      supervisor's; callers of `quiesce()` receive a promise that
   *      resolves in either terminal case.
   *    - Quiesce is idempotent: a second call during an in-flight
   *      quiesce joins the same promise. */
  quiesce(key: SessionKey): Promise<void>

  /** Release the in-memory handle. The on-disk file is left alone.
   *
   *  Contract:
   *    - Must be preceded by a completed `quiesce(key)`. Calling
   *      `deactivate` on an `active` key is a programmer error and
   *      rejects.
   *    - After deactivation, the supervisor's live map no longer
   *      contains `key`. Future inbound events for the same key
   *      re-enter `activate()` and reload the file from disk.
   *    - Quarantined handles are not deactivated through this path —
   *      they persist until a human clears the quarantine flag. */
  deactivate(key: SessionKey): Promise<void>

  /** Graceful shutdown. Quiesces every live session in parallel, awaits
   *  all flushes, then deactivates. Called from server.ts on SIGTERM /
   *  SIGINT and on stdin EOF from the Claude Code host.
   *
   *  After `shutdown()` resolves the supervisor is unusable; a second
   *  `activate()` call rejects. A new supervisor instance is required
   *  to resume, and it will rebuild state from disk. */
  shutdown(): Promise<void>

  /** Clear the quarantine flag for `key`, allowing a future `activate()`
   *  to succeed. This is the explicit operator-action path specified in
   *  session-state-machine.md §129 ("only a human (SO) clears this").
   *
   *  Contract:
   *    - If `key` is not quarantined this is a no-op; no error is thrown
   *      because the operator may have already cleared it.
   *    - After this call, a subsequent `activate()` will attempt to load
   *      the session file from disk as normal. If the file is still
   *      corrupted, the load will fail and the key will be quarantined
   *      again.
   *    - Does not perform any I/O; it only removes the in-memory
   *      quarantine entry. The audit journal event for this action lands
   *      in Epic 32-B. */
  clearQuarantine(key: SessionKey): void

  /** One pass of the idle reaper. Finds every `active` handle whose
   *  `session.lastActiveAt` is older than `idleMs` and has no in-flight
   *  work, then drives it through quiesce → deactivate.
   *
   *  Contract:
   *    - Never reaps a handle with `inFlight.size > 0` (session-state-
   *      machine.md §265 — the idle TTL check runs before quiesce and
   *      does not pre-empt in-flight work).
   *    - Never reaps a handle whose state is not `active`. Quiescing /
   *      deactivating / quarantined handles are on their own edge of
   *      the FSM; the reaper stays out of their way.
   *    - Errors on a single session do not stop the tick. The reaper
   *      logs the failure and moves on so one quarantined handle can't
   *      starve the rest of the population.
   *    - Pure relative to wall-clock — tests inject a `clock` to drive
   *      the threshold deterministically.
   *
   *  Timer wiring lives in `server.ts`: this function is the reapable
   *  unit so the server can decide tick frequency, or a test can call
   *  it directly. */
  reapIdle(): Promise<void>
}

// ---------------------------------------------------------------------------
// Factory — createSessionSupervisor
// ---------------------------------------------------------------------------

/** Structured log line emitted by the supervisor. `event` is a stable
 *  identifier (e.g. `session.activate`); `fields` carries the event's
 *  payload. Consumers are expected to inject their own writer; the
 *  default writes one newline-delimited JSON object per call to stdout
 *  so the journal sink (Epic 30-A) can tail the stream. */
export type SupervisorLog = (event: string, fields: Record<string, unknown>) => void

/** Injection points for a SessionSupervisor. All are optional; defaults
 *  give you a production-shaped supervisor that writes to stdout and
 *  reads real wall-clock time. Tests supply their own `log` and `clock`
 *  to keep assertions deterministic. */
export interface SupervisorOptions {
  /** State directory root, e.g. `~/.claude/channels/slack`. The same
   *  root passed to `sessionPath()` and `loadSession()` in lib.ts. */
  stateRoot: string
  /** Optional structured log sink. Defaults to a stdout JSON-line
   *  writer. */
  log?: SupervisorLog
  /** Optional wall-clock source, returning epoch-ms. Defaults to
   *  `Date.now`. Injected for deterministic tests of `createdAt` and
   *  `lastActiveAt`. */
  clock?: () => number
  /** Idle threshold for the reaper, in milliseconds. A session is
   *  eligible for reaping when `clock() - session.lastActiveAt >
   *  idleMs`. Default: 4 hours (14_400_000 ms). Matches the
   *  `SLACK_SESSION_IDLE_MS` env var documented in
   *  session-state-machine.md §119. */
  idleMs?: number
  /** Optional audit journal writer. When provided, the supervisor emits
   *  `session.activate`, `session.quiesce`, and `session.deactivate` events
   *  at the corresponding state transitions. Journal write failures are
   *  logged and swallowed — they must never interrupt message delivery or
   *  session lifecycle (audit-journal-architecture.md invariant: broken
   *  journal MUST NOT take down the hot path). */
  journal?: JournalWriter
}

/** Default idle threshold: 4 hours in ms. Documented in
 *  session-state-machine.md §119. */
export const DEFAULT_IDLE_MS = 4 * 60 * 60 * 1000

/** Parse `SLACK_SESSION_IDLE_MS` from an env record and return a valid
 *  idle threshold in ms. Falls back to `DEFAULT_IDLE_MS` when the var
 *  is unset, empty, non-numeric, negative, or non-finite.
 *
 *  Pure *relative to the `env` argument*: parsing the record is
 *  deterministic and side-effect-free. The default parameter value
 *  reads `process.env` as an ergonomic fallback so the call site in
 *  server.ts boot can write `resolveIdleMs()` without repeating the
 *  env lookup. Tests pass an explicit record to keep the function
 *  deterministic at the test boundary. */
export function resolveIdleMs(env: Record<string, string | undefined> = process.env): number {
  const raw = env.SLACK_SESSION_IDLE_MS
  if (raw === undefined || raw === '') return DEFAULT_IDLE_MS
  const parsed = Number(raw)
  if (!Number.isFinite(parsed) || parsed <= 0) return DEFAULT_IDLE_MS
  return Math.floor(parsed)
}

/** Default structured log writer: one newline-delimited JSON object per
 *  call, written to stdout. Matches the format the journal sink will
 *  tail. Keeping this internal means callers who want a different sink
 *  just pass their own `log` — no global config. */
function defaultLog(event: string, fields: Record<string, unknown>): void {
  const line = JSON.stringify({ event, ...fields })
  // process.stdout.write is sync for TTYs, async for pipes; either way
  // the supervisor does not await the flush. Structured logs are best-
  // effort; loss of a line is not a correctness issue.
  process.stdout.write(`${line}\n`)
}

/** Construct a SessionSupervisor bound to a state directory.
 *
 *  Build one of these at server boot per state root. The supervisor is
 *  long-lived; every inbound event flows through the same instance.
 *
 *  This factory currently returns a supervisor whose `activate()` is
 *  fully wired (ccsc-xa3.2) and whose `quiesce()`, `deactivate()`, and
 *  `shutdown()` throw `not yet implemented`. Those land in sibling
 *  beads (ccsc-xa3.3, ccsc-xa3.14). Handle `update()` is also staged
 *  for a later bead and currently rejects — callers of `activate()`
 *  can read state but not yet persist changes. See
 *  000-docs/session-state-machine.md §221-267 for the full target
 *  behaviour. */
export function createSessionSupervisor(opts: SupervisorOptions): SessionSupervisor {
  const log = opts.log ?? defaultLog
  const clock = opts.clock ?? Date.now
  const idleMs = opts.idleMs ?? DEFAULT_IDLE_MS
  const { stateRoot, journal } = opts

  /** Awaitable journal write for session lifecycle transitions. Never throws —
   *  a broken journal MUST NOT take down the session lifecycle path. Errors are
   *  forwarded to `log`. Returns a promise so callers in non-hot paths (quiesce,
   *  deactivate) can await completion before they return — this ensures that
   *  the journal file is durable before the supervisor's own state changes. */
  async function journalWrite(input: Parameters<JournalWriter['writeEvent']>[0]): Promise<void> {
    if (journal === undefined) return
    try {
      await journal.writeEvent(input)
    } catch (err: unknown) {
      log('journal.write_error', {
        kind: input.kind,
        error: err instanceof Error ? err.message : String(err),
      })
    }
  }

  // Live handles, keyed by the stringified SessionKey. Use a composite
  // string because `Map<object, ...>` keys by reference and two equal-
  // valued SessionKey literals would not collide.
  const live = new Map<string, ConcreteHandle>()

  // Quarantined keys: maps keyId → the Error that caused the quarantine.
  // Preserving the original failure reason allows activate() to surface
  // the first-failure context when it rejects. Quarantined is a sticky
  // terminal state per session-state-machine.md §129 — only an explicit
  // clearQuarantine() call removes an entry. A key in this map MUST NOT
  // also be in `live`; the two maps are disjoint by invariant.
  const quarantined = new Map<string, Error>()

  // Single-flight: concurrent activate() calls for the same key share
  // one load/create promise. Cleared after the promise settles so a
  // post-deactivate re-activation is not served a stale entry.
  const activating = new Map<string, Promise<SessionHandle>>()

  function keyId(k: SessionKey): string {
    // `\0` is not a legal character in a Slack channel/ts string, so it
    // is safe as a separator. Avoids the `"C1:T1" vs "C:1T1"` collision
    // you would get with a single-colon join.
    return `${k.channel}\0${k.thread}`
  }

  async function doActivate(
    key: SessionKey,
    initialOwnerId: string | undefined,
  ): Promise<SessionHandle> {
    // Path validation runs first — a malformed key never touches disk.
    // Any throw here propagates; no handle is recorded.
    const path = sessionPath(stateRoot, key)

    let session: Session
    try {
      session = await loadSession(stateRoot, path)
    } catch (err) {
      if (!isNotFound(err)) {
        // Real read failure: permissions, I/O, corrupt JSON, realpath
        // escape. Per session-state-machine.md §259-267 this is a
        // Quarantined transition — record in the quarantined map so
        // subsequent activate() calls reject rather than re-attempting
        // a load that is likely still broken. Bead-filing lands in
        // ccsc-xa3.8; the map entry is the in-process forensic trail.
        const errObj = err instanceof Error ? err : new Error(String(err))
        const id = keyId(key)
        quarantined.set(id, errObj)
        log('session.activate_error', {
          channel: key.channel,
          thread: key.thread,
          error: errorMessage(err),
        })
        throw err
      }
      // ENOENT branch: this key has never been activated. Require the
      // caller to name the initial owner; otherwise refuse rather than
      // synthesize identity. Aligned with session-state-machine.md §39
      // ("the identity primitive does not accept user-authored values").
      if (initialOwnerId === undefined) {
        throw new Error(
          `activate: session file missing and no initialOwnerId provided for ${JSON.stringify(
            key,
          )}`,
        )
      }
      const now = clock()
      session = {
        v: 1,
        key,
        createdAt: now,
        lastActiveAt: now,
        ownerId: initialOwnerId,
        data: {},
      }
      await saveSession(path, session)
    }

    const handle = new ConcreteHandle(key, session, path)
    // Wire the quarantine callback so update()'s failure arm can record
    // the error in the supervisor's quarantined map AND remove the handle
    // from live. Without this the supervisor's two maps would be out of
    // sync: live still carrying a quarantined handle that activate()
    // would return instead of rejecting.
    const id = keyId(key)
    handle.onQuarantine = (err: Error) => {
      quarantined.set(id, err)
      live.delete(id)
      log('session.update_error', {
        channel: key.channel,
        thread: key.thread,
        error: errorMessage(err),
      })
    }
    handle.markActive()
    live.set(id, handle)

    log('session.activate', {
      channel: key.channel,
      thread: key.thread,
      ownerId: session.ownerId,
    })
    await journalWrite({
      kind: 'session.activate',
      outcome: 'n/a',
      actor: 'system',
      sessionKey: key,
    })

    return handle
  }

  return {
    activate(key: SessionKey, initialOwnerId?: string): Promise<SessionHandle> {
      const id = keyId(key)

      // Quarantined keys are a sticky terminal state per session-state-
      // machine.md §129. Reject immediately with the original failure
      // reason so the caller surfaces the first-failure context rather
      // than silently re-loading a potentially-corrupted file from disk.
      // Only a human (SO) calling clearQuarantine() unblocks this key.
      const priorErr = quarantined.get(id)
      if (priorErr !== undefined) {
        return Promise.reject(
          new Error(`SessionSupervisor.activate: key is quarantined`, { cause: priorErr }),
        )
      }

      // Cached handle wins: subsequent activate() on a live key returns
      // the same handle without re-reading the file (session-state-
      // machine.md §266 invariant).
      const existing = live.get(id)
      if (existing !== undefined) {
        return Promise.resolve(existing)
      }

      // Single-flight: if a concurrent activation is already in
      // progress, join it. The initialOwnerId from the second caller is
      // discarded — the first caller won the race and their owner
      // (if any) is the authoritative first owner.
      const inflight = activating.get(id)
      if (inflight !== undefined) {
        return inflight
      }

      const promise = doActivate(key, initialOwnerId).finally(() => {
        activating.delete(id)
      })
      activating.set(id, promise)
      return promise
    },

    async quiesce(key: SessionKey): Promise<void> {
      const id = keyId(key)
      const handle = live.get(id)
      if (handle === undefined) {
        // Nothing to drain. Per session-state-machine.md §124 a
        // quiesce() on a Nonexistent key is a no-op — there is no
        // handle to transition and no work to flush. Do not emit a
        // log line for the empty case; it adds no information and
        // would confuse the journal sink's per-session correlation.
        return
      }

      log('session.quiesce', {
        channel: key.channel,
        thread: key.thread,
        inflight: handle.inFlight.size,
      })

      // beginQuiesce() transitions the state active → quiescing synchronously.
      // The journal write follows so the state is already visible to concurrent
      // callers when the event is persisted. Journal errors never abort the
      // quiesce path — beginQuiesce already began.
      const drainPromise = handle.beginQuiesce()
      await journalWrite({
        kind: 'session.quiesce',
        outcome: 'n/a',
        actor: 'system',
        sessionKey: key,
      })

      return drainPromise
    },

    async deactivate(key: SessionKey): Promise<void> {
      const id = keyId(key)
      const handle = live.get(id)
      if (handle === undefined) {
        // No live handle — nothing to release. Matches quiesce()'s
        // Nonexistent-key no-op per session-state-machine.md §124.
        // Do not log an empty-case line; a deactivate on an already-
        // dropped key is a recovery idempotency guarantee, not an
        // event worth correlating.
        return
      }

      // Quarantined handles are out of scope per the interface contract
      // (§197-198): only a human clears the quarantine flag. Fail loudly
      // rather than silently release a handle that the supervisor has
      // marked as needing SO attention.
      if (handle.state === 'quarantined') {
        throw new Error(
          `deactivate: handle for ${JSON.stringify(key)} is quarantined; human action required`,
        )
      }

      // Deactivation is only legal after a completed quiesce. Refusing
      // the active path is how the supervisor enforces the "work has
      // drained before release" invariant — session-state-machine.md
      // §210 invariant 2. An active-state deactivate would race with
      // in-flight update()/tool calls and violate the at-most-one-
      // writer rule.
      if (handle.state !== 'quiescing') {
        throw new Error(
          `deactivate: handle for ${JSON.stringify(key)} is in state '${handle.state}'; must be quiesced first`,
        )
      }

      handle.markDeactivating()

      // Defensive final persist. `saveSession` is atomic (tmp + rename
      // under `wx`). In the current supervisor shape `session` never
      // drifts from disk between update() calls (update() is still
      // unwired and the one field mutated by the supervisor itself is
      // `_state`, which is not persisted). Still, writing here makes
      // deactivate the single "this file is now stable on disk" fence
      // so future beads that add in-memory fields (e.g. lastActiveAt
      // refresh in the reaper) don't leak drift at shutdown.
      try {
        await saveSession(handle.path, handle.session)
      } catch (err) {
        // A write failure at the deactivation boundary is not something
        // we can recover from on this handle — the on-disk copy may or
        // may not be the last-known-good. Transition to quarantine so
        // that the NEXT activate() rejects instead of silently re-
        // loading a potentially-corrupted file. Recording the error in
        // the quarantined map BEFORE removing from live ensures the
        // signal is never lost between the two maps. Bead-filing for
        // quarantine lands with the reaper work (ccsc-xa3.8); for now
        // the quarantined map entry is the forensic trail.
        handle.markQuarantined()
        quarantined.set(id, err instanceof Error ? err : new Error(String(err)))
        live.delete(id)
        log('session.deactivate_error', {
          channel: key.channel,
          thread: key.thread,
          error: errorMessage(err),
        })
        throw err
      }

      live.delete(id)

      log('session.deactivate', {
        channel: key.channel,
        thread: key.thread,
      })
      await journalWrite({
        kind: 'session.deactivate',
        outcome: 'n/a',
        actor: 'system',
        sessionKey: key,
      })
    },

    clearQuarantine(key: SessionKey): void {
      const id = keyId(key)
      // No-op if not quarantined — idempotent so repeat operator calls
      // (e.g. a script that bulk-clears) do not error.
      quarantined.delete(id)
    },

    shutdown(): Promise<void> {
      // Under ccsc-xa3.14 (deactivate + reaper sub-epic).
      return Promise.reject(
        new Error('SessionSupervisor.shutdown: not yet implemented (ccsc-xa3.14)'),
      )
    },

    async reapIdle(): Promise<void> {
      const now = clock()
      const threshold = now - idleMs

      // Snapshot candidate keys first so we don't iterate the live map
      // while mutating it through deactivate(). Capture only what the
      // filter allows; the quiesce/deactivate pair per candidate runs
      // on the snapshot list.
      const candidates: SessionKey[] = []
      for (const handle of live.values()) {
        if (handle.state !== 'active') continue
        if (handle.inFlight.size > 0) continue
        if (handle.session.lastActiveAt > threshold) continue
        candidates.push(handle.key)
      }

      if (candidates.length === 0) return

      log('session.reap_tick', {
        idleMs,
        threshold,
        candidates: candidates.length,
      })

      // Sequential rather than parallel: keeps log ordering predictable
      // and keeps contention on the filesystem (one atomic rename at a
      // time) down on reapers that drain dozens of sessions at once.
      // For a developer install the population is small; the parallel
      // win is not worth the log-interleaving loss.
      for (const key of candidates) {
        try {
          await this.quiesce(key)
          await this.deactivate(key)
        } catch (err) {
          // One quarantined or racing handle must not starve the rest
          // of the tick. Log and continue.
          log('session.reap_error', {
            channel: key.channel,
            thread: key.thread,
            error: errorMessage(err),
          })
        }
      }
    },
  }
}

// ---------------------------------------------------------------------------
// Internal — ConcreteHandle
// ---------------------------------------------------------------------------

/** In-process implementation of SessionHandle.
 *
 *  Not exported: callers consume the `SessionHandle` interface. Keeping
 *  the class private lets later beads (update(), deactivate()) grow its
 *  internals without widening the public surface.
 *
 *  Current scope:
 *    - ccsc-xa3.2 — identity, state, snapshot, in-flight map allocation,
 *      markActive() transition.
 *    - ccsc-xa3.3 — beginQuiesce()/beginWork()/endWork() drain mechanics
 *      and the active → quiescing transition.
 *    - update() body and Quiescing → Deactivating / cancellation edges
 *      land in later beads. */
class ConcreteHandle implements SessionHandle {
  readonly key: SessionKey
  session: Session

  // Backing field for the public `state` accessor. Starts in
  // 'activating' so a consumer who somehow observes the handle before
  // markActive() runs sees the honest transient state rather than a
  // false 'active'.
  private _state: SessionState = 'activating'

  /** Per-request AbortControllers for tool calls dispatched against
   *  this session. Populated by `beginWork()` (called from server.ts's
   *  tool-call path in ccsc-xa3.15); cleared by `endWork()` when the
   *  call settles. Quiesce waits for this map to drain; shutdown will
   *  abort every entry before deactivating (ccsc-xa3.14). */
  readonly inFlight: Map<string, AbortController> = new Map()

  /** Resolved path this session's file lives at. Kept on the handle so
   *  later beads' `update()` and deactivate paths do not re-run
   *  `sessionPath()` (which would re-mkdir the parent). */
  readonly path: string

  /** Mutex tail for serialised `update()` calls. Each call chains its
   *  work onto this promise so concurrent updates run in strict call
   *  order without interleaving. Initialized to a resolved promise so
   *  the first update starts immediately. The chain carries
   *  `Promise<void>` throughout; individual links catch their own errors
   *  to prevent a rejected link from collapsing the whole chain. */
  private writeQueue: Promise<void> = Promise.resolve()

  /** In-flight drain promise allocated by `beginQuiesce()`. Null when
   *  the handle is Active (nothing to drain). Callers of quiesce share
   *  this promise so concurrent quiesce() requests do not allocate
   *  multiple drains. */
  private quiescePromise: Promise<void> | null = null

  /** Resolver for `quiescePromise`. Called by `endWork()` when the
   *  last in-flight entry drains, or directly by `beginQuiesce()` when
   *  the map is already empty at quiesce time. */
  private resolveQuiesce: (() => void) | null = null

  /** Callback invoked when `update()` transitions the handle to
   *  `quarantined`. The supervisor injects this so its `quarantined` map
   *  stays consistent: a quarantine triggered inside the write queue
   *  must be recorded in the same map that `activate()` checks, or a
   *  subsequent activate() would silently reload a potentially-corrupt
   *  file instead of rejecting. Set once by the supervisor after
   *  construction; never null after `markActive()`. */
  onQuarantine: ((err: Error) => void) | null = null

  constructor(key: SessionKey, session: Session, path: string) {
    this.key = key
    this.session = session
    this.path = path
  }

  get state(): SessionState {
    return this._state
  }

  /** Transition from `activating` → `active`. Called by the supervisor
   *  once the handle is fully wired and live in the map. Package-
   *  private by convention; callers outside this file must not invoke
   *  it. Later beads replace this with a proper state-transition method
   *  that accepts the full FSM. */
  markActive(): void {
    this._state = 'active'
  }

  /** Transition from `quiescing` → `deactivating`. Only the supervisor
   *  invokes this, and only after the drain promise has resolved.
   *  Package-private by convention; external callers must go through
   *  `SessionSupervisor.deactivate()`. */
  markDeactivating(): void {
    this._state = 'deactivating'
  }

  /** Transition to `quarantined`. Terminal from the supervisor's
   *  perspective — only a human clears it. Called on save-path
   *  failures that leave the on-disk state uncertain. */
  markQuarantined(): void {
    this._state = 'quarantined'
  }

  /** Begin a graceful drain. Transitions state `active` → `quiescing`
   *  and returns a promise that resolves when the in-flight map reaches
   *  zero entries. Contract:
   *
   *    - Idempotent when already quiescing: returns the existing drain
   *      promise so two concurrent callers share one drain.
   *    - Idempotent no-op when the in-flight map is already empty:
   *      resolves on the next microtask to preserve the promise
   *      ordering callers expect.
   *    - Rejects if called from any state other than `active` or
   *      `quiescing` — the FSM has no edge there.
   *
   *  Called by `SessionSupervisor.quiesce()`. Not a SessionHandle
   *  interface method; consumers use the supervisor's quiesce() entry
   *  point which emits the `session.quiesce` log line. */
  beginQuiesce(): Promise<void> {
    if (this._state === 'quiescing') {
      // Join the already-running drain (session-state-machine.md §266
      // documents quiesce() as idempotent — a second call receives the
      // first's promise).
      if (this.quiescePromise === null) {
        // Defensive: state is quiescing but no promise was recorded.
        // That's a programmer error (markActive / beginQuiesce sequence
        // violated). Fail loudly rather than silently synthesize. The
        // key is included so the journal sink can correlate the bug
        // back to the offending session without grepping the running
        // process.
        return Promise.reject(
          new Error(
            `beginQuiesce: quiescing state without drain promise for ${JSON.stringify(this.key)}`,
          ),
        )
      }
      return this.quiescePromise
    }

    if (this._state !== 'active') {
      return Promise.reject(new Error(`beginQuiesce: cannot quiesce from state '${this._state}'`))
    }

    this._state = 'quiescing'

    this.quiescePromise = new Promise<void>((resolve) => {
      this.resolveQuiesce = resolve
    })

    // If nothing is in flight at quiesce time, resolve on the next
    // microtask. Queueing (rather than resolving inline) keeps the
    // promise-returns-before-handler semantic consistent with the
    // drain-via-endWork() path, so callers cannot accidentally depend
    // on synchronous resolution.
    if (this.inFlight.size === 0) {
      queueMicrotask(() => {
        this.resolveQuiesce?.()
      })
    }

    return this.quiescePromise
  }

  /** Register an AbortController for an in-flight tool call and return
   *  it to the caller. The caller's responsibility is to invoke
   *  `endWork(requestId)` when the call settles. On shutdown (ccsc-
   *  xa3.14) the supervisor will call `.abort()` on every entry still
   *  in the map.
   *
   *  Not used in this bead — xa3.15 wires it into the tool-call path.
   *  Published here so `beginQuiesce()` has a real drain contract to
   *  honour and tests can exercise the drain path. */
  beginWork(requestId: string): AbortController {
    if (this.inFlight.has(requestId)) {
      throw new Error(`beginWork: requestId already in flight: '${requestId}'`)
    }
    const ctrl = new AbortController()
    this.inFlight.set(requestId, ctrl)
    return ctrl
  }

  /** Mark a tool call complete. Removes the controller from the in-
   *  flight map and, if the handle is quiescing and the map is now
   *  empty, resolves the drain promise. Safe to call with an unknown
   *  requestId — treated as a no-op so crash-recovery bookkeeping
   *  that double-ends is not a fatal error. */
  endWork(requestId: string): void {
    const had = this.inFlight.delete(requestId)
    if (!had) return

    if (this._state === 'quiescing' && this.inFlight.size === 0) {
      this.resolveQuiesce?.()
    }
  }

  /** Serialise a state mutation through the per-session write mutex,
   *  persist it atomically, and refresh `this.session` on success.
   *
   *  The write queue is a promise chain: each call appends a new link
   *  and returns a promise that resolves only after the previous link
   *  settles. Links catch their own errors so a failed update does not
   *  prevent subsequent calls from running — the handle quarantines
   *  itself and further calls will immediately reject at the state check.
   *
   *  Implementation mirrors the `deactivate()` save path: both use
   *  `saveSession()` (tmp + chmod + rename from lib.ts) and both
   *  transition to `quarantined` on save failure. */
  update(fn: (prev: Session) => Session): Promise<void> {
    // Capture state at enqueue time for the early-exit checks below.
    // We re-check after acquiring the mutex because state can change
    // while waiting in the queue (a concurrent quiesce, for example).
    const enqueueTimeState = this._state

    if (enqueueTimeState === 'quarantined') {
      return Promise.reject(new Error(`SessionHandle.update: handle is quarantined`))
    }
    if (enqueueTimeState !== 'active') {
      // Covers 'quiescing', 'deactivating', and 'activating'. Include the
      // actual state so callers can distinguish the cases without inspecting
      // `handle.state` separately.
      return Promise.reject(
        new Error(`SessionHandle.update: handle is not active (state: ${enqueueTimeState})`),
      )
    }

    // Expose a stable Promise<void> to the caller that resolves/rejects
    // based solely on this link's outcome.
    let resolve!: () => void
    let reject!: (err: unknown) => void
    const callerPromise = new Promise<void>((res, rej) => {
      resolve = res
      reject = rej
    })

    // Chain the work unit onto the write queue. The link must catch all
    // errors to avoid collapsing the chain — the original rejection is
    // forwarded to the caller via `callerPromise`.
    this.writeQueue = this.writeQueue.then(async () => {
      // Re-check state now that we hold the mutex. A concurrent quiesce
      // or a previous update's quarantine may have changed things.
      if (this._state === 'quarantined') {
        reject(new Error(`SessionHandle.update: handle is quarantined`))
        return
      }
      if (this._state !== 'active') {
        reject(new Error(`SessionHandle.update: handle is not active (state: ${this._state})`))
        return
      }

      const prev = this.session
      const next = fn(prev)

      try {
        await saveSession(this.path, next)
        this.session = next
        resolve()
      } catch (err) {
        // Save failure: quarantine the handle so future update() and
        // activate() calls fail fast. In-memory session reverts to
        // `prev` (it was never reassigned). This mirrors the deactivate()
        // failure arm exactly (session-state-machine.md §132-137).
        this._state = 'quarantined'
        const errObj = err instanceof Error ? err : new Error(String(err))
        // Notify the supervisor so its quarantined map and live map stay
        // in sync. Without this, a subsequent activate() would return the
        // cached live handle (which is now quarantined) instead of
        // rejecting — violating the sticky-quarantine invariant.
        this.onQuarantine?.(errObj)
        reject(
          new Error(`SessionHandle.update: save failed; handle quarantined`, {
            cause: errObj,
          }),
        )
      }
    })

    return callerPromise
  }
}

// ---------------------------------------------------------------------------
// Internal — error helpers
// ---------------------------------------------------------------------------

/** True for errors thrown by `loadSession` when the session file does
 *  not exist yet. `realpathSync.native` surfaces a NodeJS.ErrnoException
 *  with `code === 'ENOENT'`; we check `code` defensively in case the
 *  error was wrapped. */
function isNotFound(err: unknown): boolean {
  if (typeof err !== 'object' || err === null) return false
  const e = err as { code?: unknown }
  return e.code === 'ENOENT'
}

/** Best-effort error message extractor for structured logs. Uses
 *  `Error.message` when available; falls back to the stringified value
 *  so non-Error throws (string, number) still log something. */
function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message
  return String(err)
}
