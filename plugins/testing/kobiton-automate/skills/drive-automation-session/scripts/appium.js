// Appium / WebDriver HTTP client for the drive-automation-session skill.
// One script, generic mode + four helpers (`screen`, `actions`, `touch-perform`,
// `control`). Always exits 0; failures are surfaced via stderr and (when
// --session-dir is set) iter-NNN.error.json. Full subcommand catalog and the
// host's error-handling contract live in SKILL.md and references/.

import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs'
import {parseArgs} from 'node:util'
import {createHash} from 'node:crypto'
import {request as httpsRequest} from 'node:https'
import {request as httpRequest} from 'node:http'
import {join} from 'node:path'
import {homedir} from 'node:os'
import {URL} from 'node:url'
import {stripWebviewDom} from './strip-webview-dom.js'

// Stashed by main() so fail() can find the artifact base without re-parsing argv.
let currentFlags = null

// `explicitBase`, when provided, wins over the currentFlags-derived path — so a
// caller that already resolved the artifact base (e.g. softFail in cmdScreen)
// still writes the error file even if currentFlags isn't set yet.
function fail(_unusedCode, error, message, explicitBase) {
  process.stderr.write(JSON.stringify({error, message}) + '\n')
  const base = explicitBase ?? (currentFlags ? artifactBase(currentFlags) : null)
  if (base) persistError(base, 0, JSON.stringify({error, message}))
  process.exit(0)
}

const softFail = (base, error, message) => fail(0, error, message, base)

function getFlag(flags, name) {
  if (flags[name] == null) fail(1, 'bad-input', `--${name} is required`)
  return flags[name]
}

function readBodyArg(arg) {
  if (arg == null) return null
  if (typeof arg === 'string' && arg.startsWith('@')) {
    const path = arg.slice(1)
    try { return JSON.parse(readFileSync(path, 'utf8')) }
    catch (err) { fail(1, 'bad-input', `cannot read JSON from ${path}: ${err.message}`) }
  }
  try { return JSON.parse(arg) }
  catch (err) { fail(1, 'bad-input', `--req-body is not valid JSON: ${err.message}`) }
}

// File written by /automate:setup. Reading it here (not from argv or env)
// keeps credentials out of the AI host's transcript.
const CREDENTIALS_FILE = process.env.KOBITON_CREDENTIALS_FILE
  || join(homedir(), '.kobiton', '.credentials')

function loadCredentialsFromFile() {
  if (!existsSync(CREDENTIALS_FILE)) {
    fail(1, 'no-credentials',
      `${CREDENTIALS_FILE} not found — run /automate:setup first to fetch credentials from the Kobiton MCP server`)
  }
  const out = {portal: '', user: '', apiKey: ''}
  for (const line of readFileSync(CREDENTIALS_FILE, 'utf8').split('\n')) {
    const eq = line.indexOf('=')
    if (eq < 0) continue
    const key = line.slice(0, eq).trim()
    const val = line.slice(eq + 1)  // raw — no eval; metacharacters are literal
    if (key === 'KOBITON_USER')    out.user = val
    else if (key === 'KOBITON_API_KEY') out.apiKey = val
    else if (key === 'KOBITON_PORTAL')  out.portal = val
  }
  if (!out.portal || !out.user || !out.apiKey) {
    fail(1, 'no-credentials',
      `${CREDENTIALS_FILE} is missing one or more of KOBITON_USER / KOBITON_API_KEY / KOBITON_PORTAL — re-run /automate:setup`)
  }
  return out
}

function resolveTarget(flags) {
  if (flags['hub-url']) {
    const u = new URL(flags['hub-url'])
    const user = u.username ? decodeURIComponent(u.username) : ''
    const apiKey = u.password ? decodeURIComponent(u.password) : ''
    const authHeader = (user || apiKey)
      ? 'Basic ' + Buffer.from(`${user}:${apiKey}`).toString('base64')
      : null
    return {origin: `${u.protocol}//${u.host}`, hubPrefix: u.pathname.replace(/\/+$/, ''), authHeader}
  }
  const {portal, user, apiKey} = loadCredentialsFromFile()
  const scheme = portal.match(/^(https?:\/\/)/)?.[1] || 'https://'
  const host = portal.replace(/^https?:\/\//, '').replace(/\/+$/, '')
  return {
    origin: `${scheme}${host}`,
    hubPrefix: '/wd/hub',
    authHeader: 'Basic ' + Buffer.from(`${user}:${apiKey}`).toString('base64')
  }
}

function buildPath(target, url) {
  let p = url.startsWith('/') ? url : `/${url}`
  if (!p.startsWith(target.hubPrefix + '/') && p !== target.hubPrefix) {
    p = `${target.hubPrefix}${p}`
  }
  return p
}

// Cap the buffered response. A high-DPI /screenshot (base64 PNG in a JSON
// wrapper) is the largest legitimate payload and stays well under this; the cap
// only bites on a rogue or misconfigured hub returning an unbounded body.
// Overridable via env for tests.
const MAX_RESPONSE_BYTES = Number(process.env.KOBITON_MAX_RESPONSE_BYTES) || 64 * 1024 * 1024

function hubFetch(target, method, url, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(target.origin + buildPath(target, url))
    const isHttps = u.protocol === 'https:'
    const bodyStr = body == null ? '' : JSON.stringify(body)
    const headers = {Accept: 'application/json'}
    if (bodyStr) {
      headers['Content-Type'] = 'application/json; charset=utf-8'
      headers['Content-Length'] = Buffer.byteLength(bodyStr)
    }
    if (target.authHeader) headers.Authorization = target.authHeader

    const req = (isHttps ? httpsRequest : httpRequest)({
      protocol: u.protocol,
      hostname: u.hostname,
      port: u.port || (isHttps ? 443 : 80),
      method,
      path: u.pathname + u.search,
      headers,
      timeout: 60_000
    }, (res) => {
      const chunks = []
      let total = 0
      let aborted = false
      res.on('data', (c) => {
        if (aborted) return
        total += c.length
        if (total > MAX_RESPONSE_BYTES) {
          aborted = true
          req.destroy()  // no error arg — avoids an unhandled 'error' on the socket
          reject(new Error(`response exceeded ${MAX_RESPONSE_BYTES} bytes`))
          return
        }
        chunks.push(c)
      })
      res.on('end', () => { if (!aborted) resolve({status: res.statusCode, body: Buffer.concat(chunks)}) })
    })
    req.on('timeout', () => req.destroy(new Error('request timeout')))
    req.on('error', reject)
    if (bodyStr) req.write(bodyStr)
    req.end()
  })
}

// Iter value comes from --iter or the ITER env var the SKILL.md loop exports.
function artifactBase(flags) {
  if (!flags['session-dir']) return null
  const iterRaw = flags['iter'] ?? process.env.ITER
  if (iterRaw == null || iterRaw === '') return null
  const iterStr = String(iterRaw).padStart(3, '0')
  mkdirSync(flags['session-dir'], {recursive: true})
  return join(flags['session-dir'], `iter-${iterStr}`)
}

function persistRequest(base, argv) {
  if (!base) return
  writeFileSync(`${base}.request.json`, JSON.stringify({argv}, null, 2) + '\n')
}

function persistResponse(base, bodyStr) {
  if (!base) return
  writeFileSync(`${base}.response.json`, bodyStr.endsWith('\n') ? bodyStr : bodyStr + '\n')
}

function persistError(base, status, bodyStr) {
  if (!base) return
  const content = JSON.stringify({status}) + '\n' + (bodyStr || '')
  writeFileSync(`${base}.error.json`, content.endsWith('\n') ? content : content + '\n')
}

function emitResponse(res, base, {treat404AsSuccess = false} = {}) {
  if (treat404AsSuccess && res.status === 404) {
    // DELETE /session/{id} → 404 is idempotent success (session already ended).
    process.stdout.write('\n')
    persistResponse(base, '')
    return
  }
  const raw = res.body.toString('utf8')
  if (res.status >= 400) {
    process.stderr.write(JSON.stringify({status: res.status}) + '\n')
    if (raw) process.stderr.write(raw + (raw.endsWith('\n') ? '' : '\n'))
    persistError(base, res.status, raw)
    return
  }
  process.stdout.write(raw + '\n')
  persistResponse(base, raw)
}

// ---- Generic mode ----------------------------------------------------------

async function cmdGeneric(target, flags) {
  const method = getFlag(flags, 'method').toUpperCase()
  const url = getFlag(flags, 'url')
  let body = readBodyArg(flags['req-body'])
  const base = artifactBase(flags)
  persistRequest(base, ['--method', method, '--url', url, ...(flags['req-body'] != null ? ['--req-body', flags['req-body']] : [])])
  // POST /session: auto-wrap a flat caps body (the shape render-capabilities.js
  // emits) into the W3C envelope the hub requires. Pre-wrapped bodies are
  // left alone.
  if (method === 'POST' && /(^|\/)session\/?$/.test(url) && body && typeof body === 'object' && !Array.isArray(body) && !('capabilities' in body)) {
    body = {capabilities: {alwaysMatch: body}}
  }
  const treat404AsSuccess = method === 'DELETE' && /\/session\/[^/]+\/?$/.test(url)
  const res = await hubFetch(target, method, url, body)
  emitResponse(res, base, {treat404AsSuccess})
}

// ---- `screen` helper -------------------------------------------------------

async function cmdScreen(target, flags) {
  const sessionId = getFlag(flags, 'session-id')
  const xmlOnly = Boolean(flags['xml-only'])
  const pngOnly = Boolean(flags['png-only'])
  if (xmlOnly && pngOnly) fail(1, 'bad-input', '--xml-only and --png-only are mutually exclusive')
  const captureXml = !pngOnly
  const capturePng = !xmlOnly  // default: capture BOTH; native overlays / dialogs (e.g. Chrome's "notifications" welcome) only show in the screenshot

  const base = artifactBase(flags)
  if (!base) fail(1, 'bad-input', 'screen requires --session-dir and ITER (it writes iter-N.xml / iter-N.png)')

  const auditArgs = ['screen', '--session-id', sessionId]
  if (xmlOnly) auditArgs.push('--xml-only')
  if (pngOnly) auditArgs.push('--png-only')
  persistRequest(base, auditArgs)

  const hash = createHash('sha256')
  let xmlSize = 0
  let pngSize = 0

  if (captureXml) {
    const srcRes = await hubFetch(target, 'GET', `/session/${sessionId}/source`)
    if (srcRes.status >= 400) {
      emitResponse(srcRes, base)
      return
    }
    let srcXml
    try { srcXml = JSON.parse(srcRes.body.toString('utf8')).value || '' }
    catch (err) { softFail(base, 'parse', `source response was not JSON: ${err.message}`) }
    // Webview detection: looks for `<html` in the first 200 bytes, not strictly
    // at position 0 — some Appium drivers prepend an XML declaration or DOCTYPE.
    // Native trees (`<hierarchy>`, `<XCUIElementTypeApplication>`, `<SCREEN>`)
    // never carry `<html` near the start. See references/endpoint-reference.md
    // "Web sessions" for the strip rationale + iter-N.full.xml escape hatch.
    const isWebview = /<html[\s>]/i.test(srcXml.slice(0, 200))
    if (isWebview) {
      writeFileSync(`${base}.full.xml`, srcXml)
      srcXml = stripWebviewDom(srcXml)
    }
    writeFileSync(`${base}.xml`, srcXml)
    hash.update(srcXml)
    xmlSize = Buffer.byteLength(srcXml)
  }

  if (capturePng) {
    const shotRes = await hubFetch(target, 'GET', `/session/${sessionId}/screenshot`)
    if (shotRes.status >= 400) {
      emitResponse(shotRes, base)
      return
    }
    let b64
    try { b64 = JSON.parse(shotRes.body.toString('utf8')).value || '' }
    catch (err) { softFail(base, 'parse', `screenshot response was not JSON: ${err.message}`) }
    const pngBuf = Buffer.from(b64, 'base64')
    writeFileSync(`${base}.png`, pngBuf)
    hash.update(pngBuf)
    pngSize = pngBuf.length
  }

  const digest = hash.digest('hex')
  const out = {hash: digest, xmlBytes: xmlSize, pngBytes: pngSize}
  process.stdout.write(JSON.stringify(out) + '\n')
  persistResponse(base, JSON.stringify(out))
}

// ---- `actions` helper ------------------------------------------------------

function actionsBody(flags) {
  const type = getFlag(flags, 'type')
  switch (type) {
    case 'touch': {
      const x = Number(getFlag(flags, 'x'))
      const y = Number(getFlag(flags, 'y'))
      const holdMs = flags['hold-ms'] == null ? 50 : Number(flags['hold-ms'])
      if (!Number.isFinite(x) || !Number.isFinite(y)) fail(1, 'bad-input', '--x and --y must be numbers')
      return {actions: [{
        type: 'pointer', id: 'finger1', parameters: {pointerType: 'touch'},
        actions: [
          {type: 'pointerMove', duration: 0, x, y},
          {type: 'pointerDown', button: 0},
          {type: 'pause', duration: holdMs},
          {type: 'pointerUp', button: 0}
        ]
      }]}
    }
    case 'swipe': {
      const fromX = Number(getFlag(flags, 'from-x'))
      const fromY = Number(getFlag(flags, 'from-y'))
      const toX = Number(getFlag(flags, 'to-x'))
      const toY = Number(getFlag(flags, 'to-y'))
      const duration = flags['duration'] == null ? 300 : Number(flags['duration'])
      if (![fromX, fromY, toX, toY].every(Number.isFinite)) {
        fail(1, 'bad-input', '--from-x, --from-y, --to-x, --to-y must be numbers')
      }
      return {actions: [{
        type: 'pointer', id: 'finger1', parameters: {pointerType: 'touch'},
        actions: [
          {type: 'pointerMove', duration: 0, x: fromX, y: fromY},
          {type: 'pointerDown', button: 0},
          {type: 'pointerMove', duration, x: toX, y: toY},
          {type: 'pointerUp', button: 0}
        ]
      }]}
    }
    case 'key': {
      const key = getFlag(flags, 'key')
      return {actions: [{
        type: 'key', id: 'keyboard1',
        actions: [
          {type: 'keyDown', value: key},
          {type: 'keyUp', value: key}
        ]
      }]}
    }
    default:
      fail(1, 'bad-input', `unknown --type: ${type}. Expected one of: touch, swipe, key`)
  }
}

async function cmdActions(target, flags) {
  const sessionId = getFlag(flags, 'session-id')
  const body = actionsBody(flags)
  const base = artifactBase(flags)
  const audit = ['actions', '--session-id', sessionId, '--type', flags['type']]
  for (const k of ['x', 'y', 'hold-ms', 'from-x', 'from-y', 'to-x', 'to-y', 'duration', 'key']) {
    if (flags[k] != null) audit.push(`--${k}`, String(flags[k]))
  }
  persistRequest(base, audit)
  const res = await hubFetch(target, 'POST', `/session/${sessionId}/actions`, body)
  emitResponse(res, base)
}

// ---- `touch-perform` helper -----------------------------------------------

async function cmdTouchPerform(target, flags) {
  const sessionId = getFlag(flags, 'session-id')
  const steps = readBodyArg(getFlag(flags, 'steps'))
  if (!Array.isArray(steps)) fail(1, 'bad-input', '--steps must be a JSON array of {action, options} entries')
  const base = artifactBase(flags)
  persistRequest(base, ['touch-perform', '--session-id', sessionId, '--steps', String(flags['steps'])])
  const res = await hubFetch(target, 'POST', `/session/${sessionId}/touch/perform`, {actions: steps})
  emitResponse(res, base)
}

// ---- `control` helper ------------------------------------------------------

async function cmdControl(target, flags) {
  const base = artifactBase(flags)
  if (!base) fail(1, 'bad-input', 'control requires --session-dir and --iter (it writes iter-N.control.json)')
  const reason = flags['reason'] || ''
  let kind = null
  if (flags['done']) kind = 'DONE'
  else if (flags['blocked']) kind = 'BLOCKED'
  else fail(1, 'bad-input', 'control requires either --done or --blocked')
  const payload = {control: kind, reason}
  writeFileSync(`${base}.control.json`, JSON.stringify(payload, null, 2) + '\n')
  process.stdout.write(JSON.stringify(payload) + '\n')
}

// ---- Dispatch --------------------------------------------------------------

const HELPERS = {
  screen: cmdScreen,
  actions: cmdActions,
  'touch-perform': cmdTouchPerform,
  control: cmdControl
}

async function main() {
  const argv = process.argv.slice(2)
  let helper = null
  if (argv[0] && !argv[0].startsWith('-')) helper = argv.shift()

  const {values: flags} = parseArgs({
    args: argv,
    options: {
      // --hub-url is a legacy override (userinfo URL). Otherwise creds come
      // from ~/.kobiton/.credentials.
      'hub-url':           {type: 'string'},
      // Persistence
      'session-dir':       {type: 'string'},
      'iter':              {type: 'string'},
      // Generic mode
      'method':            {type: 'string'},
      'url':               {type: 'string'},
      'req-body':          {type: 'string'},
      // Common
      'session-id':        {type: 'string'},
      // screen helper
      'xml-only':           {type: 'boolean'},
      'png-only':           {type: 'boolean'},
      // actions helper
      'type':              {type: 'string'},
      'x':                 {type: 'string'},
      'y':                 {type: 'string'},
      'hold-ms':           {type: 'string'},
      'from-x':            {type: 'string'},
      'from-y':            {type: 'string'},
      'to-x':              {type: 'string'},
      'to-y':              {type: 'string'},
      'duration':          {type: 'string'},
      'key':               {type: 'string'},
      // touch-perform helper
      'steps':             {type: 'string'},
      // control helper
      'done':              {type: 'boolean'},
      'blocked':           {type: 'boolean'},
      'reason':            {type: 'string'}
    },
    strict: false
  })

  currentFlags = flags
  // control doesn't need credentials, but every other path does.
  const target = helper === 'control' ? null : resolveTarget(flags)
  const errBase = artifactBase(flags)
  try {
    if (helper) {
      const fn = HELPERS[helper]
      if (!fn) fail(1, 'bad-input', `unknown helper: ${helper}. Expected one of: ${Object.keys(HELPERS).join(', ')}, or omit for generic --method/--url mode`)
      await fn(target, flags)
    } else {
      await cmdGeneric(target, flags)
    }
  } catch (err) {
    const cls = err?.message === 'request timeout' ? 'request-timeout' : 'runtime'
    softFail(errBase, cls, err?.message || String(err))
  }
}

main()
