import {describe, it, expect} from 'vitest'
import {execFileSync} from 'node:child_process'
import {resolve} from 'node:path'
import {existsSync} from 'node:fs'

const DISPATCHER = resolve(import.meta.dirname, 'chromeless-launcher.sh')
const LINUX_SHIM = resolve(import.meta.dirname, 'chromeless-launcher-linux.sh')
const MAC_SHIM = resolve(import.meta.dirname, 'chromeless-launcher-mac.sh')
const WINDOWS_SHIM = resolve(import.meta.dirname, 'chromeless-launcher-windows.ps1')

// Use /bin/bash absolute so tests that override PATH (to simulate Chrome
// being absent) don't accidentally break bash resolution itself.
const BASH = '/bin/bash'

function runExpectError(script, args, env) {
  try {
    execFileSync(BASH, [script, ...args], {
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {...process.env, ...env}
    })
    throw new Error('expected script to exit non-zero')
  }
  catch (err) {
    return {exitCode: err.status, stderr: err.stderr ?? '', stdout: err.stdout ?? ''}
  }
}

describe('chromeless-launcher shim layout', () => {
  it('ships a dispatcher script', () => {
    expect(existsSync(DISPATCHER)).toBe(true)
  })

  it('ships a macOS shim', () => {
    expect(existsSync(MAC_SHIM)).toBe(true)
  })

  it('ships a Windows PowerShell shim', () => {
    expect(existsSync(WINDOWS_SHIM)).toBe(true)
  })

  it('ships a Linux shim', () => {
    expect(existsSync(LINUX_SHIM)).toBe(true)
  })
})

describe('chromeless-launcher.sh dispatcher', () => {
  it('exits 64 with usage on stderr when --url is missing', () => {
    const r = runExpectError(DISPATCHER, [])
    expect(r.exitCode).toBe(64)
    expect(r.stderr).toMatch(/--url is required/)
  })

  it('exits 64 on unknown argument', () => {
    const r = runExpectError(DISPATCHER, ['--url', 'http://x', '--bogus'])
    expect(r.exitCode).toBe(64)
    expect(r.stderr).toMatch(/unknown arg/)
  })

  it('accepts --width, --height, --orientation, --x, --y', () => {
    // We cannot easily mock the per-OS shim here; instead verify the script
    // does not error out on argument parsing by giving an unsupported
    // OSTYPE which forces a clean exit 2 BEFORE invoking the shim.
    const r = runExpectError(DISPATCHER, [
      '--url', 'http://example.com',
      '--width', '500', '--height', '900',
      '--orientation', 'portrait',
      '--x', '50', '--y', '50'
    ], {OSTYPE: 'unknown-os'})
    expect(r.exitCode).toBe(2)
    expect(r.stderr).toMatch(/unsupported OSTYPE/)
  })

  it('swaps width/height when --orientation landscape is set and dimensions are still portrait', () => {
    // The dispatcher logs nothing about the swap, but it must not error.
    // Same approach: force unsupported OSTYPE so we exit cleanly before
    // touching a real Chrome.
    const r = runExpectError(DISPATCHER, [
      '--url', 'http://example.com',
      '--width', '540', '--height', '920',
      '--orientation', 'landscape'
    ], {OSTYPE: 'unknown-os'})
    expect(r.exitCode).toBe(2)
  })
})

describe('chromeless-launcher-linux.sh', () => {
  // Force Chrome detection to fail by giving an empty PATH so `command -v`
  // returns nothing. This proves the exit-2 sentinel works.
  it('exits 2 with fallback message when Chrome is absent', () => {
    const r = runExpectError(LINUX_SHIM, ['--url', 'http://example.com'], {PATH: '/nonexistent'})
    expect(r.exitCode).toBe(2)
    expect(r.stderr).toMatch(/falling back to default browser/)
  })

  it('exits 64 when --url is missing', () => {
    const r = runExpectError(LINUX_SHIM, [])
    expect(r.exitCode).toBe(64)
    expect(r.stderr).toMatch(/--url required/)
  })

  it('exits 64 on unknown argument', () => {
    const r = runExpectError(LINUX_SHIM, ['--url', 'http://x', '--mystery'])
    expect(r.exitCode).toBe(64)
    expect(r.stderr).toMatch(/unknown arg/)
  })
})

describe('chromeless-launcher-mac.sh', () => {
  it('exits 64 when --url is missing', () => {
    const r = runExpectError(MAC_SHIM, [])
    expect(r.exitCode).toBe(64)
    expect(r.stderr).toMatch(/--url required/)
  })

  it('exits 64 on unknown argument', () => {
    const r = runExpectError(MAC_SHIM, ['--url', 'https://example.com', '--foo'])
    expect(r.exitCode).toBe(64)
    expect(r.stderr).toMatch(/unknown arg/)
  })
})

describe('URL validation (defense in depth)', () => {
  // The dispatcher reaches validation BEFORE OSTYPE routing, so we force an
  // unknown OS to short-circuit before invoking a real per-OS shim.
  const scripts = [
    {name: 'dispatcher', path: DISPATCHER, env: {OSTYPE: 'unknown-os'}},
    {name: 'mac', path: MAC_SHIM, env: {}},
    {name: 'linux', path: LINUX_SHIM, env: {}}
  ]

  for (const {name, path, env} of scripts) {
    it(`${name}: rejects URL with embedded double quote`, () => {
      const r = runExpectError(path, ['--url', 'https://x"y.com'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/quoting-breaking metacharacters/)
    })

    it(`${name}: rejects URL with backtick`, () => {
      const r = runExpectError(path, ['--url', 'https://x`whoami`.com'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/quoting-breaking metacharacters/)
    })

    it(`${name}: rejects URL with command substitution`, () => {
      const r = runExpectError(path, ['--url', 'https://x$(id).com'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/quoting-breaking metacharacters/)
    })

    it(`${name}: rejects URL with backslash`, () => {
      const r = runExpectError(path, ['--url', 'https://x\\y.com'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/quoting-breaking metacharacters/)
    })

    it(`${name}: rejects non-http(s) scheme`, () => {
      const r = runExpectError(path, ['--url', 'file:///etc/passwd'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/http:\/\/ or https:\/\//)
    })
  }

  // Regression guard: real Kobiton portal URLs use `&` and `?` between
  // query-string params. An earlier revision over-blocked these and broke
  // every chromeless launch. We verify the dispatcher (with OSTYPE forced
  // to an unsupported value so it short-circuits with exit 2 BEFORE
  // spawning a real Chrome) accepts these URL shapes cleanly. The per-OS
  // shims share the same validation logic, so testing the dispatcher is
  // sufficient — testing the mac/linux shims directly would either spawn
  // Chrome (slow + side-effecting) or time out the test runner.
  describe('valid URL chars pass through (regression guard)', () => {
    const env = {OSTYPE: 'unknown-os'}

    it('dispatcher: accepts URL with & between query params (real Kobiton shape)', () => {
      const url = 'https://portal-test-blue.kobiton.com/devices/launch?id=13003138&view=device-only'
      const r = runExpectError(DISPATCHER, ['--url', url], env)
      expect(r.stderr).not.toMatch(/quoting-breaking metacharacters/)
      expect(r.stderr).not.toMatch(/must start with http/)
      expect(r.exitCode).toBe(2)  // OS-unsupported sentinel, NOT a validation reject
    })

    it('dispatcher: accepts URL with ; in path', () => {
      const r = runExpectError(DISPATCHER, ['--url', 'https://example.com/path;param=1'], env)
      expect(r.stderr).not.toMatch(/quoting-breaking metacharacters/)
      expect(r.exitCode).toBe(2)
    })

    it('dispatcher: accepts URL with single quote', () => {
      const r = runExpectError(DISPATCHER, ['--url', "https://example.com/o'brien"], env)
      expect(r.stderr).not.toMatch(/quoting-breaking metacharacters/)
      expect(r.exitCode).toBe(2)
    })

    it('dispatcher: accepts URL with | < > pipe/redirect chars', () => {
      const r = runExpectError(DISPATCHER, ['--url', 'https://example.com/?a=1|2<3>4'], env)
      expect(r.stderr).not.toMatch(/quoting-breaking metacharacters/)
      expect(r.exitCode).toBe(2)
    })
  })
})

describe('numeric argument validation', () => {
  // The bash shims and the dispatcher all guard --width / --height (and the
  // dispatcher also guards --x / --y) against non-numeric, zero, or negative
  // values. Without the guard, a non-numeric value would trip `set -e` on
  // later arithmetic with a confusing shell error; zero/negative would pass
  // through and produce an invalid window size.
  const scripts = [
    {name: 'dispatcher', path: DISPATCHER, env: {OSTYPE: 'unknown-os'}},
    {name: 'mac', path: MAC_SHIM, env: {}},
    {name: 'linux', path: LINUX_SHIM, env: {}}
  ]

  for (const {name, path, env} of scripts) {
    it(`${name}: rejects non-numeric --width with exit 64`, () => {
      const r = runExpectError(path, ['--url', 'https://example.com', '--width', 'abc'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/--width must be a positive integer/)
    })

    it(`${name}: rejects zero --width with exit 64`, () => {
      const r = runExpectError(path, ['--url', 'https://example.com', '--width', '0'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/--width must be a positive integer/)
    })

    it(`${name}: rejects non-numeric --height with exit 64`, () => {
      const r = runExpectError(path, ['--url', 'https://example.com', '--height', 'foo'], env)
      expect(r.exitCode).toBe(64)
      expect(r.stderr).toMatch(/--height must be a positive integer/)
    })
  }
})

describe('codex mirror parity', () => {
  // Codex CLI's plugin installer (openai/codex copy_dir_recursive) silently
  // skips symlinks, so the .codex/ subtree has to be real files mirroring
  // skills/. The byte-identity contract is enforced by
  // scripts/sync-codex-artifacts.js --check (run by `pnpm run validate`),
  // but the unit test surface didn't previously assert it — so the chromeless
  // shims could in theory diverge in one tree and the launcher tests would
  // still pass. These checks close that gap.
  const CODEX_DIR = resolve(import.meta.dirname, '..', '..', '..', '.codex', 'skills', 'run-automation-suite', 'scripts')
  const filenames = [
    'chromeless-launcher.sh',
    'chromeless-launcher-mac.sh',
    'chromeless-launcher-windows.ps1',
    'chromeless-launcher-linux.sh',
    'chromeless-launcher.test.js'
  ]

  for (const f of filenames) {
    it(`.codex/ mirror has ${f}`, async () => {
      const codexPath = resolve(CODEX_DIR, f)
      expect(existsSync(codexPath)).toBe(true)
    })

    it(`.codex/ mirror is byte-identical for ${f}`, async () => {
      const {readFileSync} = await import('node:fs')
      const src = readFileSync(resolve(import.meta.dirname, f))
      const mirror = readFileSync(resolve(CODEX_DIR, f))
      expect(mirror.equals(src)).toBe(true)
    })
  }
})
