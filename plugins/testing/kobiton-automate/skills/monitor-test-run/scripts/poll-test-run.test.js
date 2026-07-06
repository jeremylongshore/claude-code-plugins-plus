import {describe, it, expect, beforeAll, afterAll} from 'vitest'
import {execFile} from 'node:child_process'
import {createServer} from 'node:http'
import {writeFileSync, mkdtempSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join, resolve} from 'node:path'

const SCRIPT = resolve(import.meta.dirname, 'poll-test-run.js')

// Mock /v2/test-runs/:id server. `state.sequence` is an array of response
// bodies; each GET returns the next one, repeating the last forever.
const state = {sequence: [], idx: 0}
let server, port

beforeAll(() => new Promise((res) => {
  server = createServer((req, resp) => {
    req.on('data', () => {})
    req.on('end', () => {
      const i = Math.min(state.idx, state.sequence.length - 1)
      const out = state.sequence[i]
      state.idx++
      resp.writeHead(out.status || 200, {'Content-Type': 'application/json'})
      resp.end(JSON.stringify(out.body))
    })
  })
  server.listen(0, '127.0.0.1', () => { port = server.address().port; res() })
}))

afterAll(() => new Promise((res) => server.close(res)))

function setSequence(seq) { state.sequence = seq; state.idx = 0 }

function credsFile() {
  const dir = mkdtempSync(join(tmpdir(), 'monitor-test-run-'))
  const path = join(dir, '.credentials')
  writeFileSync(path, [
    'KOBITON_USER=u',
    'KOBITON_API_KEY=k',
    `KOBITON_PORTAL=http://127.0.0.1:${port}`
  ].join('\n') + '\n')
  return path
}

function run(args, env) {
  return new Promise((res) => {
    execFile('node', [SCRIPT, ...args],
      {timeout: 18000, env: {...process.env, ...env}},
      (err, stdout, stderr) => res({code: err ? err.code : 0, stdout: stdout || '', stderr: stderr || ''}))
  })
}

// Fast intervals so the test doesn't wait real seconds.
const FAST = ['--interval', '1', '--max-interval', '1']

const exec = (over = {}) => ({
  id: 'e1', test_case_id: 10, status: 'NEW', failure_type: null,
  execution_session_id: 500, assigned_device_id: 111, ...over
})

describe('poll-test-run.js', () => {
  it('emits READY with the env-mapped portal base, then DONE, exit 0', async () => {
    setSequence([
      {body: {id: 'run1', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'NONE'})]}}
    ])
    const r = await run(['--run-id', 'run1', ...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(0)
    // 127.0.0.1 host doesn't match the api-*.kobiton.com pattern → production fallback.
    expect(r.stdout).toMatch(/^READY portal=https:\/\/portal\.kobiton\.com/m)
    expect(r.stdout).toMatch(/EVENT terminal_passed exec=e1/)
    expect(r.stdout).toMatch(/DONE/)
  })

  it('stays SILENT across no-change polls (only one EVENT for a stable blocked exec)', async () => {
    const blocked = exec({status: 'BLOCKED_WAITING'})
    setSequence([
      {body: {id: 'r', revisit_executions: [blocked]}},   // blocked → emit once
      {body: {id: 'r', revisit_executions: [blocked]}},   // no change → silent
      {body: {id: 'r', revisit_executions: [blocked]}},   // no change → silent
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'BLOCKER_ENCOUNTERED'})]}}
    ])
    const r = await run(['--run-id', 'r', ...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(0)
    const blockedLines = r.stdout.split('\n').filter((l) => l.startsWith('EVENT blocked'))
    expect(blockedLines).toHaveLength(1)  // exactly one — not one per poll
    expect(r.stdout).toMatch(/EVENT terminal_blocker_encountered exec=e1 device=111/)
  })

  it('emits dispatched → blocked → resumed → terminal_passed transitions in order', async () => {
    // Start in a queue state (NEW), as the real API does — dispatched must still
    // fire when the execution first reaches RUNNING, not only when the first poll
    // already shows RUNNING.
    setSequence([
      {body: {id: 'r', revisit_executions: [exec({status: 'NEW'})]}},            // queued → silent
      {body: {id: 'r', revisit_executions: [exec({status: 'SCHEDULED'})]}},      // queued → silent
      {body: {id: 'r', revisit_executions: [exec({status: 'RUNNING'})]}},        // dispatched
      {body: {id: 'r', revisit_executions: [exec({status: 'BLOCKED_WAITING'})]}}, // blocked
      {body: {id: 'r', revisit_executions: [exec({status: 'RUNNING'})]}},        // resumed
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'NONE'})]}}
    ])
    const r = await run(['--run-id', 'r', ...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    const kinds = r.stdout.split('\n')
      .filter((l) => l.startsWith('EVENT'))
      .map((l) => l.split(' ')[1])
    expect(kinds).toEqual(['dispatched', 'blocked', 'resumed', 'terminal_passed'])
  }, 20000)

  it('emits dispatched then the terminal for a fast NEW→COMPLETED execution', async () => {
    setSequence([
      {body: {id: 'r', revisit_executions: [exec({status: 'NEW'})]}},
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'NONE'})]}}
    ])
    const r = await run(['--run-id', 'r', ...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    const kinds = r.stdout.split('\n').filter((l) => l.startsWith('EVENT')).map((l) => l.split(' ')[1])
    expect(kinds).toEqual(['dispatched', 'terminal_passed'])
  })

  it('does NOT declare DONE on an empty execution list, then completes once populated', async () => {
    setSequence([
      {body: {id: 'r', revisit_executions: []}},                                  // not scheduled yet
      {body: {id: 'r', revisit_executions: []}},                                  // still empty
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'NONE'})]}}
    ])
    const r = await run(['--run-id', 'r', '--interval', '1', '--max-interval', '1', '--waiting-heartbeat', '1'],
      {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(0)
    // a WAITING "no executions yet" heartbeat appears before any DONE
    const lines = r.stdout.split('\n')
    const firstDone = lines.findIndex((l) => l.startsWith('DONE'))
    const firstEmptyWait = lines.findIndex((l) => l.includes('no executions yet'))
    expect(firstEmptyWait).toBeGreaterThanOrEqual(0)
    expect(firstEmptyWait).toBeLessThan(firstDone)
    expect(r.stdout).toMatch(/EVENT terminal_passed/)
    expect(r.stdout).toMatch(/DONE/)
  })

  it('emits a WAITING heartbeat while an execution stays blocked', async () => {
    const blocked = exec({status: 'BLOCKED_WAITING'})
    setSequence([
      {body: {id: 'r', revisit_executions: [blocked]}},   // blocked → EVENT blocked
      {body: {id: 'r', revisit_executions: [blocked]}},   // no change → WAITING (heartbeat=1s)
      {body: {id: 'r', revisit_executions: [blocked]}},   // no change → WAITING
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'BLOCKER_ENCOUNTERED'})]}}
    ])
    const r = await run(['--run-id', 'r', '--interval', '1', '--max-interval', '1', '--waiting-heartbeat', '1'],
      {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(0)
    expect(r.stdout).toMatch(/EVENT blocked exec=e1/)
    expect(r.stdout.split('\n').filter((l) => l.startsWith('WAITING blocked=')).length).toBeGreaterThanOrEqual(1)
  })

  it('emits NO WAITING heartbeat when --waiting-heartbeat 0', async () => {
    const blocked = exec({status: 'BLOCKED_WAITING'})
    setSequence([
      {body: {id: 'r', revisit_executions: [blocked]}},
      {body: {id: 'r', revisit_executions: [blocked]}},
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'NONE'})]}}
    ])
    const r = await run(['--run-id', 'r', ...FAST, '--waiting-heartbeat', '0'], {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(0)
    expect(r.stdout).not.toMatch(/WAITING/)
  })

  it('classifies a non-blocker failure as terminal_failed', async () => {
    setSequence([
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'APP_CRASHED'})]}}
    ])
    const r = await run(['--run-id', 'r', ...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.stdout).toMatch(/EVENT terminal_failed exec=e1 .*failure=APP_CRASHED/)
  })

  it('fatal on 404 (NOT_FOUND), exit 1', async () => {
    setSequence([{status: 404, body: {message: 'not found'}}])
    const r = await run(['--run-id', 'missing', ...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(1)
    expect(r.stdout).toMatch(/ERROR NOT_FOUND/)
  })

  it('errors without --run-id, exit 1', async () => {
    const r = await run([...FAST], {KOBITON_CREDENTIALS_FILE: credsFile()})
    expect(r.code).toBe(1)
    expect(r.stdout).toMatch(/ERROR bad-input/)
  })

  it('ignores commented-out credential lines (env-toggle layout) and uses the active block', async () => {
    setSequence([
      {body: {id: 'r', revisit_executions: [exec({status: 'COMPLETED', failure_type: 'NONE'})]}}
    ])
    // INI with a commented-out production block above the active mock-server block.
    // The flat parser must skip the '#' lines, not let them shadow the active values.
    const dir = mkdtempSync(join(tmpdir(), 'monitor-test-run-ini-'))
    const path = join(dir, '.credentials')
    writeFileSync(path, [
      '[default]',
      '# KOBITON_USER=prod',
      '# KOBITON_API_KEY=prodkey',
      '# KOBITON_PORTAL=https://api.kobiton.com',
      'KOBITON_USER=u',
      'KOBITON_API_KEY=k',
      `KOBITON_PORTAL=http://127.0.0.1:${port}`
    ].join('\n') + '\n')
    const r = await run(['--run-id', 'r', ...FAST], {KOBITON_CREDENTIALS_FILE: path})
    expect(r.code).toBe(0)  // would 404/err if it picked the commented production host
    expect(r.stdout).toMatch(/EVENT terminal_passed/)
    expect(r.stdout).toMatch(/DONE/)
  })

  it('errors with a clear message when the credentials file is missing', async () => {
    const r = await run(['--run-id', 'r', ...FAST], {KOBITON_CREDENTIALS_FILE: '/nonexistent/.credentials'})
    expect(r.code).toBe(1)
    expect(r.stdout).toMatch(/ERROR no-credentials/)
  })
})
