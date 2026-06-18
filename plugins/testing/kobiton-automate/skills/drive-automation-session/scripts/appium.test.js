import {describe, it, expect, beforeAll, afterAll} from 'vitest'
import {execFile} from 'node:child_process'
import {createServer} from 'node:http'
import {createHash} from 'node:crypto'
import {writeFileSync, mkdtempSync, readFileSync, existsSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join, resolve} from 'node:path'

const SCRIPT = resolve(import.meta.dirname, 'appium.js')

const state = {hits: [], handler: () => ({status: 200, body: {value: {}}})}
let server, port

beforeAll(() => new Promise((res) => {
  server = createServer((req, resp) => {
    const chunks = []
    req.on('data', (c) => chunks.push(c))
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8')
      let parsedBody = null
      if (raw) {
        try { parsedBody = JSON.parse(raw) } catch { parsedBody = raw }
      }
      state.hits.push({method: req.method, path: req.url, body: parsedBody, headers: req.headers})
      const out = state.handler(state.hits[state.hits.length - 1])
      resp.writeHead(out.status, out.headers || {'Content-Type': 'application/json'})
      resp.end(typeof out.body === 'string' ? out.body : JSON.stringify(out.body))
    })
  })
  server.listen(0, '127.0.0.1', () => {
    port = server.address().port
    res()
  })
}))

afterAll(() => new Promise((res) => server.close(res)))

function reset(handler) {
  state.hits.length = 0
  state.handler = handler || (() => ({status: 200, body: {value: {}}}))
}

function run(args, env) {
  return new Promise((res) => {
    const childEnv = env ? {...process.env, ...env} : undefined
    execFile('node', [SCRIPT, ...args], {timeout: 5000, env: childEnv}, (err, stdout, stderr) => {
      if (err) res({ok: false, code: err.code, stdout: stdout || '', stderr: stderr || ''})
      else res({ok: true, code: 0, stdout, stderr})
    })
  })
}

function writeTemp(name, content) {
  const dir = mkdtempSync(join(tmpdir(), 'drive-automation-session-'))
  const path = join(dir, name)
  writeFileSync(path, typeof content === 'string' ? content : JSON.stringify(content))
  return path
}

function makeSessionDir() {
  return mkdtempSync(join(tmpdir(), 'drive-automation-session-sess-'))
}

let credsFilePath
function makeCredsFile({portal = `http://127.0.0.1:${port}`, user = 'u', apiKey = 'k'} = {}) {
  credsFilePath = writeTemp('.credentials', [
    `KOBITON_USER=${user}`,
    `KOBITON_API_KEY=${apiKey}`,
    `KOBITON_PORTAL=${portal}`
  ].join('\n') + '\n')
  return credsFilePath
}
function credEnv(overrides = {}) {
  return {KOBITON_CREDENTIALS_FILE: makeCredsFile(overrides)}
}
function runWithCreds(args, env) {
  return run(args, {...credEnv(), ...(env || {})})
}

describe('appium.js generic mode', () => {
  it('GET prepends /wd/hub to --url automatically', async () => {
    reset(() => ({status: 200, body: {value: '<hierarchy />'}}))
    const r = await runWithCreds(['--method', 'GET', '--url', '/session/sess-1/source'])
    expect(r.ok).toBe(true)
    expect(state.hits[0].method).toBe('GET')
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-1/source')
    expect(JSON.parse(r.stdout).value).toBe('<hierarchy />')
  })

  it('accepts --url with /wd/hub already present', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const r = await runWithCreds(['--method', 'GET', '--url', '/wd/hub/session/sess-2/source'])
    expect(r.ok).toBe(true)
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-2/source')
  })

  it('POST with inline --req-body sends correct body', async () => {
    reset(() => ({status: 200, body: {value: {ELEMENT: 'el-1'}}}))
    await runWithCreds(['--method', 'POST', '--url', '/session/sess-3/element', '--req-body', '{"using":"xpath","value":"//Button"}'])
    expect(state.hits[0].body).toEqual({using: 'xpath', value: '//Button'})
  })

  it('POST with @file --req-body reads from disk', async () => {
    reset(() => ({status: 200, body: {value: {sessionId: 'sess-new'}}}))
    const capsFile = writeTemp('caps.json', {capabilities: {alwaysMatch: {platformName: 'Android'}}})
    await runWithCreds(['--method', 'POST', '--url', '/session', '--req-body', `@${capsFile}`])
    expect(state.hits[0].body).toEqual({capabilities: {alwaysMatch: {platformName: 'Android'}}})
  })

  it('POST /session auto-wraps a flat caps body in the W3C envelope', async () => {
    // render-capabilities.js emits flat caps; the host passes them through
    // without manual wrapping. appium.js wraps them on the fly so the host
    // doesn't have to remember the W3C shape.
    reset(() => ({status: 200, body: {value: {sessionId: 'sess-w3c'}}}))
    const flatCaps = {platformName: 'Android', 'appium:udid': '21161FDF60051K'}
    await runWithCreds(['--method', 'POST', '--url', '/session', '--req-body', JSON.stringify(flatCaps)])
    expect(state.hits[0].body).toEqual({capabilities: {alwaysMatch: flatCaps}})
  })

  it('POST /session leaves an already-wrapped body alone', async () => {
    reset(() => ({status: 200, body: {value: {sessionId: 'sess-pre'}}}))
    const wrapped = {capabilities: {alwaysMatch: {platformName: 'iOS'}}}
    await runWithCreds(['--method', 'POST', '--url', '/session', '--req-body', JSON.stringify(wrapped)])
    expect(state.hits[0].body).toEqual(wrapped)
  })

  it('POST to a non-session URL does NOT auto-wrap (no false positives)', async () => {
    reset(() => ({status: 200, body: {value: 'el-1'}}))
    const elemBody = {using: 'xpath', value: '//Button'}
    await runWithCreds(['--method', 'POST', '--url', '/session/sX/element', '--req-body', JSON.stringify(elemBody)])
    // element-find body has no `capabilities` key but it's NOT /session — must not be wrapped
    expect(state.hits[0].body).toEqual(elemBody)
  })

  it('DELETE /session/{id} treats 404 as success', async () => {
    reset(() => ({status: 404, body: {value: {error: 'invalid session id'}}}))
    const r = await runWithCreds(['--method', 'DELETE', '--url', '/session/gone'])
    expect(r.ok).toBe(true)
  })

  it('Appium error → exit 0; stderr = {status} + raw body (host classifies)', async () => {
    reset(() => ({status: 404, body: {value: {error: 'no such element', message: 'not found'}}}))
    const r = await runWithCreds(['--method', 'POST', '--url', '/session/x/element', '--req-body', '{"using":"xpath","value":"//Missing"}'])
    // Script exits 0 — host reads the stderr (or iter-N.error.json) to classify.
    expect(r.ok).toBe(true)
    const [summary, ...bodyLines] = r.stderr.trim().split('\n')
    expect(JSON.parse(summary).status).toBe(404)
    expect(JSON.parse(bodyLines.join('\n'))).toEqual({value: {error: 'no such element', message: 'not found'}})
  })

  it('invalid session id (non-DELETE) → exit 0; raw body lets host detect "session gone"', async () => {
    reset(() => ({status: 404, body: {value: {error: 'invalid session id'}}}))
    const r = await runWithCreds(['--method', 'POST', '--url', '/session/x/element', '--req-body', '{}'])
    expect(r.ok).toBe(true)
    expect(JSON.parse(r.stderr.trim().split('\n')[0]).status).toBe(404)
  })

  it('5xx server error → exit 0; raw body preserved', async () => {
    reset(() => ({status: 500, body: {value: {error: 'unknown', message: 'server down'}}}))
    const r = await runWithCreds(['--method', 'GET', '--url', '/session/x/source'])
    expect(r.ok).toBe(true)
    expect(JSON.parse(r.stderr.trim().split('\n')[0]).status).toBe(500)
  })

  it('response exceeding the size cap is aborted (exit 0; error surfaced)', async () => {
    // Return a body larger than the test cap (set via env below).
    reset(() => ({status: 200, body: {value: 'x'.repeat(5000)}}))
    const r = await runWithCreds(
      ['--method', 'GET', '--url', '/session/x/source'],
      {KOBITON_MAX_RESPONSE_BYTES: '1024'}
    )
    expect(r.ok).toBe(true) // single exit-code policy
    expect(r.stderr).toMatch(/exceeded 1024 bytes|request/i)
  })
})

describe('appium.js credentials', () => {
  it('reads ~/.kobiton/.credentials and builds the Basic Auth header from it', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    await runWithCreds(['--method', 'GET', '--url', '/session/s/source'])
    expect(state.hits[0].headers['authorization']).toBe('Basic ' + Buffer.from('u:k').toString('base64'))
  })

  it('missing credentials file → exit 0; stderr says to run /automate:setup', async () => {
    const r = await run(
      ['--method', 'GET', '--url', '/session/s/source'],
      {KOBITON_CREDENTIALS_FILE: '/nonexistent/path/.credentials'}
    )
    expect(r.ok).toBe(true)
    expect(r.stderr).toMatch(/not found/)
    expect(r.stderr).toContain('/automate:setup')
  })

  it('partial credentials file (missing KOBITON_API_KEY) → exit 0; stderr names the missing key family', async () => {
    const partial = writeTemp('.credentials', 'KOBITON_USER=u\nKOBITON_PORTAL=http://x\n')
    const r = await run(
      ['--method', 'GET', '--url', '/session/s/source'],
      {KOBITON_CREDENTIALS_FILE: partial}
    )
    expect(r.ok).toBe(true)
    expect(r.stderr).toMatch(/missing one or more/)
    expect(r.stderr).toContain('KOBITON_API_KEY')
  })

  it('credentials with shell metacharacters are read as LITERAL strings (no eval)', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const tampered = writeTemp('.credentials',
      'KOBITON_USER=alice; rm -rf /tmp/should-not-execute\n' +
      'KOBITON_API_KEY=secret`whoami`\n' +
      `KOBITON_PORTAL=http://127.0.0.1:${port}\n`
    )
    await run(
      ['--method', 'GET', '--url', '/session/s/source'],
      {KOBITON_CREDENTIALS_FILE: tampered}
    )
    const expected = 'Basic ' + Buffer.from('alice; rm -rf /tmp/should-not-execute:secret`whoami`').toString('base64')
    expect(state.hits[0].headers['authorization']).toBe(expected)
  })

  it('--hub-url overrides the credentials file (legacy / debugging escape hatch)', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const url = `http://${encodeURIComponent('u@x')}:${encodeURIComponent('k:z')}@127.0.0.1:${port}/wd/hub`
    await run(['--hub-url', url, '--method', 'GET', '--url', '/session/s/source'])
    expect(state.hits[0].headers['authorization']).toBe('Basic ' + Buffer.from('u@x:k:z').toString('base64'))
  })

})

describe('appium.js screen helper', () => {
  it('default: captures BOTH XML and PNG (so native overlays show up)', async () => {
    const xml = '<hierarchy><node/></hierarchy>'
    const pngB64 = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).toString('base64')
    let callIdx = 0
    reset(() => {
      callIdx += 1
      if (callIdx === 1) return {status: 200, body: {value: xml}}
      return {status: 200, body: {value: pngB64}}
    })
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'sess-s', '--session-dir', dir, '--iter', '1'])
    expect(r.ok).toBe(true)
    expect(state.hits).toHaveLength(2)
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-s/source')
    expect(state.hits[1].path).toBe('/wd/hub/session/sess-s/screenshot')
    expect(existsSync(join(dir, 'iter-001.xml'))).toBe(true)
    expect(existsSync(join(dir, 'iter-001.png'))).toBe(true)
    expect(readFileSync(join(dir, 'iter-001.xml'), 'utf8')).toBe(xml)
    const stdout = JSON.parse(r.stdout)
    const expected = createHash('sha256').update(xml).update(Buffer.from(pngB64, 'base64')).digest('hex')
    expect(stdout.hash).toBe(expected)
    expect(stdout.xmlBytes).toBeGreaterThan(0)
    expect(stdout.pngBytes).toBeGreaterThan(0)
  })

  it('--xml-only: skips screenshot; only /source is hit', async () => {
    const xml = '<hierarchy/>'
    reset(() => ({status: 200, body: {value: xml}}))
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'sess-x', '--session-dir', dir, '--iter', '2', '--xml-only'])
    expect(r.ok).toBe(true)
    expect(state.hits).toHaveLength(1)
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-x/source')
    expect(existsSync(join(dir, 'iter-002.xml'))).toBe(true)
    expect(existsSync(join(dir, 'iter-002.png'))).toBe(false)
    const stdout = JSON.parse(r.stdout)
    expect(stdout.pngBytes).toBe(0)
    expect(stdout.hash).toBe(createHash('sha256').update(xml).digest('hex'))
  })

  it('--png-only: skips source; only /screenshot is hit', async () => {
    const pngB64 = Buffer.from([0x89, 0x50, 0x4e, 0x47]).toString('base64')
    reset(() => ({status: 200, body: {value: pngB64}}))
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'sess-p', '--session-dir', dir, '--iter', '3', '--png-only'])
    expect(r.ok).toBe(true)
    expect(state.hits).toHaveLength(1)
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-p/screenshot')
    expect(existsSync(join(dir, 'iter-003.xml'))).toBe(false)
    expect(existsSync(join(dir, 'iter-003.png'))).toBe(true)
    const stdout = JSON.parse(r.stdout)
    expect(stdout.xmlBytes).toBe(0)
    expect(stdout.pngBytes).toBeGreaterThan(0)
  })

  it('--xml-only AND --png-only is a usage error', async () => {
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'x', '--session-dir', dir, '--iter', '4', '--xml-only', '--png-only'])
    expect(r.ok).toBe(true) // exit 0 always
    expect(r.stderr).toContain('mutually exclusive')
  })

  it('persists iter-N.request.json with the audit argv', async () => {
    reset(() => ({status: 200, body: {value: '<y/>'}}))
    const dir = makeSessionDir()
    await runWithCreds(['screen', '--session-id', 'sess-rq', '--session-dir', dir, '--iter', '2'])
    const req = JSON.parse(readFileSync(join(dir, 'iter-002.request.json'), 'utf8'))
    expect(req.argv).toContain('screen')
    expect(req.argv).toContain('sess-rq')
  })

  it('requires --session-dir AND ITER (stderr names --session-dir; exit 0)', async () => {
    const r = await runWithCreds(['screen', '--session-id', 'x'])
    expect(r.ok).toBe(true)
    expect(r.stderr).toContain('--session-dir')
  })

  it('webview source: writes stripped iter-N.xml AND raw iter-N.full.xml', async () => {
    const raw = '<html><head><script>noise()</script></head><body><div role="button" aria-label="Search YouTube" jsdata="x">icon</div></body></html>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'sess-wv', '--session-dir', dir, '--iter', '5', '--xml-only'])
    expect(r.ok).toBe(true)
    expect(existsSync(join(dir, 'iter-005.xml'))).toBe(true)
    expect(existsSync(join(dir, 'iter-005.full.xml'))).toBe(true)
    const stripped = readFileSync(join(dir, 'iter-005.xml'), 'utf8')
    const full = readFileSync(join(dir, 'iter-005.full.xml'), 'utf8')
    expect(full).toBe(raw)
    expect(stripped).not.toContain('<script')
    expect(stripped).not.toContain('jsdata=')
    expect(stripped).toContain('aria-label="Search YouTube"')
    // Hash is computed on the stripped XML, not the raw, so screen-hash
    // equality reflects what the host actually reads.
    const stdout = JSON.parse(r.stdout)
    expect(stdout.hash).toBe(createHash('sha256').update(stripped).digest('hex'))
    expect(stdout.xmlBytes).toBe(Buffer.byteLength(stripped))
  })

  it('native source: writes iter-N.xml only (raw); no iter-N.full.xml', async () => {
    const raw = '<hierarchy><android.widget.Button text="OK" content-desc="confirm"/></hierarchy>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'sess-nv', '--session-dir', dir, '--iter', '6', '--xml-only'])
    expect(r.ok).toBe(true)
    expect(existsSync(join(dir, 'iter-006.xml'))).toBe(true)
    expect(existsSync(join(dir, 'iter-006.full.xml'))).toBe(false)
    expect(readFileSync(join(dir, 'iter-006.xml'), 'utf8')).toBe(raw)
    const stdout = JSON.parse(r.stdout)
    expect(stdout.hash).toBe(createHash('sha256').update(raw).digest('hex'))
  })

  it('webview detection is leading-whitespace tolerant and case-insensitive', async () => {
    const raw = '\n  <HTML><body><div>hi</div></body></HTML>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    await runWithCreds(['screen', '--session-id', 'sess-ws', '--session-dir', dir, '--iter', '7', '--xml-only'])
    expect(existsSync(join(dir, 'iter-007.full.xml'))).toBe(true)
  })

  it('webview detection accepts an XML declaration before <html (chromedriver path)', async () => {
    // UiAutomator2 chromedriver commonly prepends <?xml version="1.0"?> to
    // webview /source responses. The first 200 bytes still carry <html, so
    // the strip should fire.
    const raw = '<?xml version="1.0" encoding="UTF-8"?><html><body><div jsdata="x">hi</div></body></html>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    const r = await runWithCreds(['screen', '--session-id', 'sess-xml', '--session-dir', dir, '--iter', '8', '--xml-only'])
    expect(r.ok).toBe(true)
    expect(existsSync(join(dir, 'iter-008.full.xml'))).toBe(true)
    const stripped = readFileSync(join(dir, 'iter-008.xml'), 'utf8')
    expect(stripped).not.toContain('jsdata=') // strip actually ran
  })

  it('webview detection accepts a DOCTYPE before <html', async () => {
    const raw = '<!DOCTYPE html><html><body><span jsdata="x">hi</span></body></html>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    await runWithCreds(['screen', '--session-id', 'sess-dt', '--session-dir', dir, '--iter', '9', '--xml-only'])
    expect(existsSync(join(dir, 'iter-009.full.xml'))).toBe(true)
    expect(readFileSync(join(dir, 'iter-009.xml'), 'utf8')).not.toContain('jsdata=')
  })

  it('webview detection accepts a UTF-8 BOM before <html', async () => {
    const raw = '﻿<html><body><i jsdata="x">hi</i></body></html>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    await runWithCreds(['screen', '--session-id', 'sess-bom', '--session-dir', dir, '--iter', '10', '--xml-only'])
    expect(existsSync(join(dir, 'iter-010.full.xml'))).toBe(true)
  })

  it('native UiAutomator2 source is NOT misclassified as webview', async () => {
    const raw = '<hierarchy><android.widget.FrameLayout text=""><android.widget.Button text="OK"/></android.widget.FrameLayout></hierarchy>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    await runWithCreds(['screen', '--session-id', 'sess-ua2', '--session-dir', dir, '--iter', '11', '--xml-only'])
    expect(existsSync(join(dir, 'iter-011.xml'))).toBe(true)
    expect(existsSync(join(dir, 'iter-011.full.xml'))).toBe(false)
  })

  it('native XCUITest source is NOT misclassified as webview', async () => {
    const raw = '<SCREEN><XCUIElementTypeApplication name="App"><XCUIElementTypeButton name="OK"/></XCUIElementTypeApplication></SCREEN>'
    reset(() => ({status: 200, body: {value: raw}}))
    const dir = makeSessionDir()
    await runWithCreds(['screen', '--session-id', 'sess-xc', '--session-dir', dir, '--iter', '12', '--xml-only'])
    expect(existsSync(join(dir, 'iter-012.xml'))).toBe(true)
    expect(existsSync(join(dir, 'iter-012.full.xml'))).toBe(false)
  })
})

describe('appium.js persistence (--session-dir / --iter)', () => {
  it('generic call persists iter-N.request.json + iter-N.response.json on success', async () => {
    reset(() => ({status: 200, body: {value: {ELEMENT: 'el-x'}}}))
    const dir = makeSessionDir()
    await runWithCreds(['--method', 'POST', '--url', '/session/s/element', '--req-body', '{"using":"xpath","value":"//B"}', '--session-dir', dir, '--iter', '3'])
    const req = JSON.parse(readFileSync(join(dir, 'iter-003.request.json'), 'utf8'))
    expect(req.argv).toContain('--method')
    expect(req.argv).toContain('POST')
    const resp = JSON.parse(readFileSync(join(dir, 'iter-003.response.json'), 'utf8'))
    expect(resp).toEqual({value: {ELEMENT: 'el-x'}})
    expect(existsSync(join(dir, 'iter-003.error.json'))).toBe(false)
  })

  it('generic call persists iter-N.error.json on failure (exit 0, host classifies)', async () => {
    reset(() => ({status: 404, body: {value: {error: 'no such element'}}}))
    const dir = makeSessionDir()
    const r = await runWithCreds(['--method', 'POST', '--url', '/session/s/element', '--req-body', '{"using":"xpath","value":"//Missing"}', '--session-dir', dir, '--iter', '4'])
    // Script exits 0 in all Appium-response cases; the host detects failure
    // by iter-N.error.json existence on the next turn.
    expect(r.ok).toBe(true)
    const err = readFileSync(join(dir, 'iter-004.error.json'), 'utf8')
    const [summary, ...bodyLines] = err.trim().split('\n')
    expect(JSON.parse(summary).status).toBe(404)
    expect(JSON.parse(bodyLines.join('\n'))).toEqual({value: {error: 'no such element'}})
    expect(existsSync(join(dir, 'iter-004.response.json'))).toBe(false)
  })

  it('no --session-dir / --iter → no files written', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const dir = makeSessionDir()
    await runWithCreds(['--method', 'GET', '--url', '/session/s/source'])
    // dir is empty; nothing should land there
    expect(existsSync(join(dir, 'iter-001.request.json'))).toBe(false)
  })

  it('pads iter to 3 digits', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const dir = makeSessionDir()
    await runWithCreds(['--method', 'GET', '--url', '/session/s/source', '--session-dir', dir, '--iter', '42'])
    expect(existsSync(join(dir, 'iter-042.request.json'))).toBe(true)
  })

  it('reads ITER from env when --iter flag is omitted', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const dir = makeSessionDir()
    await runWithCreds(
      ['--method', 'GET', '--url', '/session/s/source', '--session-dir', dir],
      {ITER: '7'}
    )
    expect(existsSync(join(dir, 'iter-007.request.json'))).toBe(true)
  })

  it('explicit --iter overrides ITER env', async () => {
    reset(() => ({status: 200, body: {value: '<x/>'}}))
    const dir = makeSessionDir()
    await runWithCreds(
      ['--method', 'GET', '--url', '/session/s/source', '--session-dir', dir, '--iter', '99'],
      {ITER: '7'}
    )
    expect(existsSync(join(dir, 'iter-099.request.json'))).toBe(true)
    expect(existsSync(join(dir, 'iter-007.request.json'))).toBe(false)
  })
})

describe('appium.js actions helper', () => {
  it('--type touch builds W3C pointer sequence', async () => {
    reset(() => ({status: 200, body: {value: null}}))
    await runWithCreds(['actions', '--session-id', 'sess-t', '--type', 'touch', '--x', '100', '--y', '200'])
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-t/actions')
    const seq = state.hits[0].body.actions[0]
    expect(seq.actions.map(a => a.type)).toEqual(['pointerMove', 'pointerDown', 'pause', 'pointerUp'])
    expect(seq.actions[0]).toMatchObject({x: 100, y: 200})
    expect(seq.actions[2]).toMatchObject({duration: 50})
  })

  it('--type touch --hold-ms 1000 long-tap pause', async () => {
    reset(() => ({status: 200, body: {value: null}}))
    await runWithCreds(['actions', '--session-id', 'sess-lp', '--type', 'touch', '--x', '50', '--y', '60', '--hold-ms', '1000'])
    expect(state.hits[0].body.actions[0].actions[2]).toMatchObject({duration: 1000})
  })

  it('--type swipe builds 4-step sequence', async () => {
    reset(() => ({status: 200, body: {value: null}}))
    await runWithCreds(['actions', '--session-id', 'sess-sw', '--type', 'swipe', '--from-x', '1', '--from-y', '2', '--to-x', '3', '--to-y', '4', '--duration', '350'])
    const seq = state.hits[0].body.actions[0].actions
    expect(seq.map(a => a.type)).toEqual(['pointerMove', 'pointerDown', 'pointerMove', 'pointerUp'])
    expect(seq[2]).toMatchObject({duration: 350, x: 3, y: 4})
  })

  it('--type key builds keyDown/keyUp', async () => {
    reset(() => ({status: 200, body: {value: null}}))
    await runWithCreds(['actions', '--session-id', 'sess-k', '--type', 'key', '--key', 'Enter'])
    expect(state.hits[0].body.actions[0].actions).toEqual([
      {type: 'keyDown', value: 'Enter'},
      {type: 'keyUp', value: 'Enter'}
    ])
  })

  it('unknown --type exits 1', async () => {
    const r = await runWithCreds(['actions', '--session-id', 'x', '--type', 'noop'])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
  })

  it('non-numeric swipe coord exits 1', async () => {
    const r = await runWithCreds(['actions', '--session-id', 'x', '--type', 'swipe', '--from-x', 'abc', '--from-y', '0', '--to-x', '0', '--to-y', '0'])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
  })
})

describe('appium.js touch-perform helper', () => {
  it('wraps steps into /touch/perform body', async () => {
    reset(() => ({status: 200, body: {value: null}}))
    const stepsFile = writeTemp('steps.json', [{action: 'press', options: {x: 1, y: 2}}, {action: 'release'}])
    await runWithCreds(['touch-perform', '--session-id', 'sess-tp', '--steps', `@${stepsFile}`])
    expect(state.hits[0].path).toBe('/wd/hub/session/sess-tp/touch/perform')
    expect(state.hits[0].body).toEqual({actions: [{action: 'press', options: {x: 1, y: 2}}, {action: 'release'}]})
  })

  it('--steps not an array exits 1', async () => {
    const f = writeTemp('steps.json', {action: 'press'})
    const r = await runWithCreds(['touch-perform', '--session-id', 'x', '--steps', `@${f}`])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
  })
})

describe('appium.js control helper', () => {
  it('--done writes iter-N.control.json with {control: DONE, reason}', async () => {
    reset()
    const dir = makeSessionDir()
    const r = await runWithCreds(['control', '--done', '--reason', 'all good', '--session-dir', dir, '--iter', '5'])
    expect(r.ok).toBe(true)
    const ctl = JSON.parse(readFileSync(join(dir, 'iter-005.control.json'), 'utf8'))
    expect(ctl).toEqual({control: 'DONE', reason: 'all good'})
    // No HTTP request issued
    expect(state.hits).toHaveLength(0)
  })

  it('--blocked writes iter-N.control.json with {control: BLOCKED, reason}', async () => {
    const dir = makeSessionDir()
    await runWithCreds(['control', '--blocked', '--reason', 'stuck', '--session-dir', dir, '--iter', '6'])
    const ctl = JSON.parse(readFileSync(join(dir, 'iter-006.control.json'), 'utf8'))
    expect(ctl).toEqual({control: 'BLOCKED', reason: 'stuck'})
  })

  it('control without --done or --blocked exits 1', async () => {
    const dir = makeSessionDir()
    const r = await runWithCreds(['control', '--reason', 'x', '--session-dir', dir, '--iter', '7'])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
  })

  it('control without --session-dir/--iter exits 1', async () => {
    const r = await runWithCreds(['control', '--done', '--reason', 'x'])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
  })
})

describe('appium.js usage errors', () => {
  it('unknown helper exits 1', async () => {
    const r = await runWithCreds(['cuddle', '--session-id', 'x'])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
    expect(r.stderr).toContain('unknown helper')
  })

  it('generic without --method exits 1', async () => {
    const r = await runWithCreds(['--url', '/session/x/source'])
    expect(r.ok).toBe(true)  // exit 0 always; host detects error via stderr / iter-N.error.json
  })

  it('--req-body invalid JSON exits 0; stderr names bad-input', async () => {
    const r = await runWithCreds(['--method', 'POST', '--url', '/session', '--req-body', 'not json {'])
    expect(r.ok).toBe(true)
    expect(r.stderr).toContain('bad-input')
  })

  it('bad-input with --session-dir writes iter-N.error.json (exit 0)', async () => {
    const dir = makeSessionDir()
    const r = await runWithCreds(['--method', 'POST', '--url', '/session', '--req-body', 'not json {', '--session-dir', dir, '--iter', '7'])
    expect(r.ok).toBe(true)
    expect(existsSync(join(dir, 'iter-007.error.json'))).toBe(true)
    const err = readFileSync(join(dir, 'iter-007.error.json'), 'utf8')
    expect(err).toContain('bad-input')
  })
})
