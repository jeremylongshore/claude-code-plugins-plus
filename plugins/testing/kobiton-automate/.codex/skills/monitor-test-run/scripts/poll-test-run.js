// Silent emit-on-change poller for the monitor-test-run skill.
//
// Polls GET /v2/test-runs/<id> in a loop and prints ONE line to stdout only
// when a revisit execution changes state (dispatched / blocked / resumed /
// terminal) — never on a no-change poll. The AI host runs this in the
// background and relays each emitted line; quiet stretches produce no output,
// which is the whole point (the pilot's noise came from per-poll narration).
//
// Why a script and not the MCP getTestRun tool: a background process can't call
// MCP tools, so this reads run state via the public REST API using
// ~/.kobiton/.credentials (same credentials-file pattern as appium.js — creds
// never appear in argv/env/transcript). The skill still uses the MCP tools for
// getOrgSettings (up front) and terminateTestRun (actions).
//
// Output protocol (one space-separated line per event; parse-friendly):
//   READY portal=<portal-base>                         once, at start
//   EVENT <kind> exec=<id> device=<assigned_device_id|-> session=<sid|-> tc=<test_case_id|-> failure=<failure_type|->
//     <kind> ∈ dispatched | blocked | resumed | terminal_passed |
//             terminal_blocker_encountered | terminal_failed | terminal_terminated
//   WAITING blocked=<n> …                               throttled heartbeat while executions sit blocked-waiting
//   DONE all executions terminal                        once, before exit 0
//   ERROR <code> <message>                              non-fatal poll issues (keeps going) / fatal (then exit)
//
// Always exits 0 on a clean DONE; exits 1 only on unrecoverable setup/credential
// errors. Run state is never mutated.

import {readFileSync, existsSync} from 'node:fs'
import {parseArgs} from 'node:util'
import {request as httpsRequest} from 'node:https'
import {request as httpRequest} from 'node:http'
import {join} from 'node:path'
import {homedir} from 'node:os'
import {URL} from 'node:url'

const CREDENTIALS_FILE = process.env.KOBITON_CREDENTIALS_FILE
  || join(homedir(), '.kobiton', '.credentials')

function emit(line) { process.stdout.write(line + '\n') }
function fatal(code, message) { emit(`ERROR ${code} ${message}`); process.exit(1) }

// KOBITON_PORTAL in the credentials file is actually the API base URL (e.g.
// https://api.kobiton.com) — a misnomer kept for backward compat. We poll REST
// against it and derive the human portal host from it for the launch URL.
function loadCredentials() {
  if (!existsSync(CREDENTIALS_FILE)) {
    fatal('no-credentials',
      `${CREDENTIALS_FILE} not found — run /automate:setup first`)
  }
  // The file is INI-ish: an optional [profile] header, KEY=val lines, and
  // possibly commented (#/;) lines — e.g. a user who toggled envs by commenting
  // out one block and adding another. Skip blank/comment/section lines so a
  // commented KOBITON_PORTAL never shadows the active one (last active wins).
  const out = {apiBase: '', user: '', apiKey: ''}
  for (const raw of readFileSync(CREDENTIALS_FILE, 'utf8').split('\n')) {
    const line = raw.trim()
    if (!line || line.startsWith('#') || line.startsWith(';') || line.startsWith('[')) continue
    const eq = line.indexOf('=')
    if (eq < 0) continue
    const key = line.slice(0, eq).trim()
    const val = line.slice(eq + 1).trim()
    if (key === 'KOBITON_USER') out.user = val
    else if (key === 'KOBITON_API_KEY') out.apiKey = val
    else if (key === 'KOBITON_PORTAL') out.apiBase = val
  }
  if (!out.apiBase || !out.user || !out.apiKey) {
    fatal('no-credentials',
      `${CREDENTIALS_FILE} is missing KOBITON_USER / KOBITON_API_KEY / KOBITON_PORTAL — re-run /automate:setup`)
  }
  return out
}

// api[-env].kobiton.com -> portal[-env].kobiton.com (drop trailing /mcp or path).
// Fallback: production portal host if the api host doesn't match the pattern.
function derivePortalBase(apiBase) {
  const scheme = apiBase.match(/^(https?:\/\/)/)?.[1] || 'https://'
  const host = apiBase.replace(/^https?:\/\//, '').replace(/\/.*$/, '')
  if (host === 'api.kobiton.com') return 'https://portal.kobiton.com'
  const m = host.match(/^api(-[a-z0-9-]+)?\.kobiton\.com$/i)
  if (m) return `${scheme}portal${m[1] || ''}.kobiton.com`
  return 'https://portal.kobiton.com'
}

function getJson(apiBase, authHeader, path) {
  return new Promise((resolve) => {
    let u
    try { u = new URL(apiBase.replace(/\/+$/, '') + path) }
    catch (err) { return resolve({error: `bad-url ${err.message}`}) }
    const isHttps = u.protocol === 'https:'
    const req = (isHttps ? httpsRequest : httpRequest)({
      protocol: u.protocol, hostname: u.hostname,
      port: u.port || (isHttps ? 443 : 80),
      method: 'GET', path: u.pathname + u.search,
      headers: {Accept: 'application/json', Authorization: authHeader},
      timeout: 60_000
    }, (res) => {
      const chunks = []
      res.on('data', (c) => chunks.push(c))
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8')
        if (res.statusCode < 200 || res.statusCode >= 300) {
          return resolve({status: res.statusCode, error: `http-${res.statusCode}`, text})
        }
        try { resolve({status: res.statusCode, data: JSON.parse(text)}) }
        catch { resolve({status: res.statusCode, error: 'bad-json', text}) }
      })
    })
    req.on('timeout', () => { req.destroy(); resolve({error: 'timeout'}) })
    req.on('error', (err) => resolve({error: err.message}))
    req.end()
  })
}

// Tolerate both snake_case (public REST) and camelCase shapes.
const pick = (o, ...keys) => { for (const k of keys) if (o && o[k] != null) return o[k]; return undefined }

function executionsOf(run) {
  return pick(run, 'revisit_executions', 'revisitExecutions') || []
}

// Map a raw execution to a stable event kind, or null if non-terminal & non-blocked.
function classify(e) {
  const status = pick(e, 'status')
  const failure = pick(e, 'failure_type', 'failureType')
  if (status === 'COMPLETED') {
    if (failure === 'BLOCKER_ENCOUNTERED') return 'terminal_blocker_encountered'
    if (failure === 'TERMINATED_BY_USER' || failure === 'TERMINATED_BY_SYSTEM') return 'terminal_terminated'
    if (!failure || failure === 'NONE') return 'terminal_passed'
    return 'terminal_failed'
  }
  // Non-terminal. The live blocked-waiting state is what we surface in-flight.
  if (status === 'BLOCKED_WAITING') return 'blocked'
  if (status === 'BLOCKED_RESUMING' || status === 'RUNNING') return 'running'
  return status || 'unknown'  // NEW / SCHEDULED / UPLOADING_IMAGE / TERMINATING / ...
}

const isTerminal = (kind) => kind.startsWith('terminal_')

function eventLine(kind, e) {
  return `EVENT ${kind}` +
    ` exec=${pick(e, 'id') ?? '-'}` +
    ` device=${pick(e, 'assigned_device_id', 'assignedDeviceId') ?? '-'}` +
    ` session=${pick(e, 'execution_session_id', 'executionSessionId') ?? '-'}` +
    ` tc=${pick(e, 'test_case_id', 'testCaseId') ?? '-'}` +
    ` failure=${pick(e, 'failure_type', 'failureType') ?? '-'}`
}

async function main() {
  const {values: flags} = parseArgs({
    options: {
      'run-id': {type: 'string'},
      'interval': {type: 'string'},   // base seconds, default 3
      'max-interval': {type: 'string'}, // backoff cap seconds, default 30
      'max-errors': {type: 'string'},  // consecutive poll errors before giving up, default 5
      'waiting-heartbeat': {type: 'string'} // seconds between WAITING heartbeats while blocked; 0 disables; default 60
    }
  })
  const runId = flags['run-id']
  if (!runId) fatal('bad-input', '--run-id is required')
  const base = Math.max(1, Number(flags['interval']) || 3)
  const cap = Math.max(base, Number(flags['max-interval']) || 30)
  const maxErrors = Math.max(1, Number(flags['max-errors']) || 5)
  // 0 (explicitly) disables the heartbeat; absent → default 60s.
  const waitingHeartbeat = flags['waiting-heartbeat'] != null
    ? Math.max(0, Number(flags['waiting-heartbeat']) || 0) : 60

  const {apiBase, user, apiKey} = loadCredentials()
  const authHeader = 'Basic ' + Buffer.from(`${user}:${apiKey}`).toString('base64')
  const portal = derivePortalBase(apiBase)
  emit(`READY portal=${portal}`)

  const lastKind = new Map()  // executionId -> last classified kind
  const announced = new Set() // executionIds we've already emitted a "started" (dispatched) line for
  let interval = base
  let consecutiveErrors = 0
  let lastWaitingAt = 0   // ms timestamp of the last WAITING (blocked) heartbeat
  let lastEmptyAt = 0     // ms timestamp of the last "waiting for executions" heartbeat
  let sawExecutions = false
  const sleep = (s) => new Promise((r) => setTimeout(r, s * 1000))

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const res = await getJson(apiBase, authHeader, `/v2/test-runs/${runId}`)
    if (res.error) {
      consecutiveErrors++
      if (res.status === 404 || res.status === 403) fatal(res.status === 404 ? 'NOT_FOUND' : 'FORBIDDEN', `run ${runId}: ${res.error}`)
      emit(`ERROR poll ${res.error} (attempt ${consecutiveErrors}/${maxErrors})`)
      if (consecutiveErrors >= maxErrors) fatal('UNRECOVERABLE', `gave up after ${maxErrors} consecutive poll errors`)
      await sleep(Math.min(cap, interval * 2))
      interval = Math.min(cap, interval * 2)
      continue
    }
    consecutiveErrors = 0

    const execs = executionsOf(res.data)
    if (execs.length > 0) sawExecutions = true
    let changed = false
    // Only declare DONE once we've actually seen executions AND they're all
    // terminal — an empty list means "not scheduled yet", not "all done"
    // (the create→monitor handoff can poll before executions exist).
    let allTerminal = execs.length > 0
    let blockedCount = 0
    for (const e of execs) {
      const id = pick(e, 'id')
      const kind = classify(e)
      if (!isTerminal(kind)) allTerminal = false
      if (kind === 'blocked') blockedCount++
      const prev = lastKind.get(id)
      lastKind.set(id, kind)
      if (prev === kind) continue  // no change for this execution → silent

      // "dispatched" announces an execution has started working — emit it the
      // FIRST time we see it running/blocked/terminal, regardless of which queue
      // states (NEW/SCHEDULED/UPLOADING_IMAGE) we saw it pass through first.
      // (Gating on prev==null missed it whenever the first poll caught the
      // execution still queued.)
      if (kind === 'blocked') { emit(eventLine('blocked', e)); changed = true }
      else if (kind === 'running') {
        if (prev === 'blocked') { emit(eventLine('resumed', e)); changed = true }
        else if (!announced.has(id)) { emit(eventLine('dispatched', e)); changed = true }
      }
      else if (isTerminal(kind)) {
        // Surface a terminal that we never announced as started (e.g. a fast
        // NEW→COMPLETED) so it isn't reported out of nowhere.
        if (!announced.has(id) && kind !== 'terminal_terminated') { emit(eventLine('dispatched', e)) }
        emit(eventLine(kind, e)); changed = true
      }
      // queue states (NEW/SCHEDULED/UPLOADING_IMAGE/TERMINATING) emit nothing,
      // but their kind is recorded above so the next real transition is detected.
      if (kind === 'running' || kind === 'blocked' || isTerminal(kind)) announced.add(id)
    }

    if (allTerminal) { emit('DONE all executions terminal'); process.exit(0) }

    // Heartbeat while executions sit blocked-waiting (flag-ON live remediation):
    // they're on a resolution countdown, so a silent stretch is NOT "nothing to
    // do" — it's the user's window to act. Emit a throttled WAITING line so the
    // host re-engages and nudges the user, rather than going dark until timeout.
    // Disabled with --waiting-heartbeat 0.
    if (!changed && blockedCount > 0 && waitingHeartbeat > 0) {
      const now = Date.now()
      if (now - lastWaitingAt >= waitingHeartbeat * 1000) {
        emit(`WAITING blocked=${blockedCount} (executions paused on a blocker, awaiting remediation before timeout)`)
        lastWaitingAt = now
      }
    }

    // Run exists but has no executions yet (create→monitor handoff polled before
    // scheduling). Keep polling, but don't go dark — heartbeat so the host knows
    // we're alive and waiting, not stuck. (The host's stream timeout is the hard
    // bound on a run that never schedules.)
    if (execs.length === 0 && !sawExecutions && waitingHeartbeat > 0) {
      const now = Date.now()
      if (now - lastEmptyAt >= waitingHeartbeat * 1000) {
        emit('WAITING blocked=0 (run has no executions yet — waiting for scheduling)')
        lastEmptyAt = now
      }
    }

    // Backoff: reset to base whenever something changed (run is active), else
    // grow toward the cap during quiet stretches (e.g. all BLOCKED_WAITING).
    interval = changed ? base : Math.min(cap, interval * 2)
    await sleep(interval)
  }
}

main().catch((err) => fatal('UNRECOVERABLE', err.message))
