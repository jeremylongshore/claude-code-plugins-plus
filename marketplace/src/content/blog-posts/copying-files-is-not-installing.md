---
title: "Copying Files Is Not Installing"
description: "A marketplace install copies a plugin's files into place but never runs its installer. Here is how that bricked local mode and the dependency-free bootstrap that fixed it."
date: "2026-07-16"
tags: ["claude-code", "plugins", "mcp", "nodejs", "packaging", "npm", "native-modules"]
featured: false
---
A marketplace install copies your plugin's files into place. It does not run `npm install` in them. Those are two different operations, and the gap between them is where "works on my machine" lives.

We hit that gap shipping Bob's Big Brain, a Claude Code and Cowork plugin that runs a local stdio MCP server to give a team a governed knowledge brain. In the author's checkout it worked. For every teammate installing from the marketplace, one of its two modes died on start. The teammates did nothing wrong. The install path had an assumption baked into it, and the assumption only held on the machine where the code was written.

## Two modes, one of them has native code

The server runs in one of two modes, decided at startup.

**Team mode** talks to a remote API. It reads `TEAMKB_API_URL` from the environment or a `~/.teamkb/team.json` file, sends requests over HTTP, and holds no local state. It is pure JavaScript with zero native dependencies. Nothing to compile, nothing to install.

**Local mode** runs an embedded store on the user's own machine, backed by SQLite. That mode needs two *native* Node modules: `better-sqlite3` for the database and `fs-ext` for file locking. Native means compiled C++ bindings, not pure JS. They do not exist until something runs `npm install` and the build step produces a `.node` binary for the current platform.

So the dependency surface is lopsided. Team users need nothing. Local users need a compile step to have happened. That asymmetry is the whole story.

## The exact failure

Here is the sequence for a clean marketplace install of local mode:

1. The marketplace copies the plugin directory into place. Source files, `package.json`, `package-lock.json`, the `.mcp.json` manifest. Everything except `node_modules`.
2. Claude launches the MCP server named in the manifest.
3. The server enters local mode and calls `require('better-sqlite3')`.
4. There is no `node_modules`. The `require` throws `MODULE_NOT_FOUND`.
5. The server crashes on boot. Local mode is dead before it does any work.

In the dev checkout, step 4 never happened, because `npm install` had been run there by hand months earlier and `node_modules` was sitting on disk. The code was correct. The environment was not reproducible. A marketplace install is a *file copy*, and a file copy carries no build artifacts.

The fix is not "tell users to run npm install." A plugin that requires a manual build step after install is a plugin that fails for most people. The fix is to make the server provision its own native deps, on first start, only when it actually needs them, and to do it safely when several copies of the server start at once.

## The bootstrap launcher

The manifest now points at a small launcher instead of the server directly. `plugin-runtime/bootstrap.cjs` is about 125 lines and uses *only* Node builtins. That constraint is load-bearing: the launcher has to run before any dependency exists, so it cannot import a single thing from `node_modules`. `fs`, `path`, `child_process`, `module`. Nothing else.

On start it makes one decision: does this launch need native deps at all?

```js
// A value counts as "configured" only if it is real and expanded.
// An unexpanded ${VAR} placeholder is NOT configured.
function isConfigured(value) {
  return typeof value === 'string'
    && value.length > 0
    && !value.startsWith('${');
}

function teamModeRequested() {
  if (isConfigured(process.env.TEAMKB_API_URL)) return true;
  const base = process.env.TEAMKB_BASE_PATH
    || process.env.TEAMKB_HOME
    || path.join(os.homedir(), '.teamkb');
  return fs.existsSync(path.join(base, 'team.json'));
}
```

If team mode is requested, the launcher does nothing and executes the bundled server immediately. Team users pay zero install cost, which is correct: they never touch SQLite. The `${` guard matters more than it looks. When a manifest ships `"TEAMKB_API_URL": "${TEAMKB_API_URL}"` and the variable is unset, the literal string `${TEAMKB_API_URL}` arrives in the environment. Treating that as "configured" would route a local user into team mode and fail differently. So an unexpanded placeholder counts as absent.

If team mode is not requested, the launcher checks whether the native deps are already present before doing any work:

```js
const { createRequire } = require('module');

function nativeDependenciesReady() {
  const requireFromBundle = createRequire(BUNDLE);
  try {
    requireFromBundle('better-sqlite3');
    requireFromBundle('fs-ext');
    return true;
  } catch {
    return false;
  }
}
```

`createRequire(BUNDLE)` resolves from the bundle's own root, not the launcher's, so the check asks the exact question that matters: can the *server* load these when it runs? If yes, provisioning is skipped entirely. Idempotent by construction. If no, the launcher provisions:

```bash
npm ci --omit=dev --no-audit --no-fund
```

`npm ci`, not `npm install`. `ci` installs the exact versions pinned in `package-lock.json` and errors if the lockfile and manifest disagree. That makes provisioning reproducible: every teammate gets the same `better-sqlite3` build the author tested, not whatever "latest" resolves to that day. After the install the launcher re-runs `nativeDependenciesReady()` and throws if the deps are still missing. A silent partial install is worse than a loud failure.

## The concurrency protocol

The hard part is not installing. It is installing exactly once when the server can start several times at once.

An MCP server gets launched per client. Open three Claude windows, or run a few agents, and you get three concurrent bootstraps racing to `npm ci` the same directory. Two `npm ci` runs on one directory step on each other and corrupt the tree. A naive "check if node_modules exists, if not install" has a check-then-act race: both processes check, both see nothing, both install.

The lock is an atomic `mkdirSync` of a `.native-install.lock` directory. `mkdir` is the right primitive because it either creates the directory or fails with `EEXIST`, atomically, at the filesystem layer. There is no window between check and create. A check-then-write lock reintroduces the race; an atomic create, whether `mkdir` or an exclusive `wx` open, does not. `mkdir` is just the simplest primitive that gives it.

```js
function acquireInstallLock(lockDir) {
  const STALE_MS = 5 * 60 * 1000;   // 5 minutes
  const WAIT_STEP_MS = 250;
  const MAX_WAIT_MS = 2 * 60 * 1000; // 2 minutes
  let waited = 0;

  for (;;) {
    try {
      fs.mkdirSync(lockDir);        // atomic: create or EEXIST
      return;                        // we hold the lock
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;

      // Someone else holds it. Three ways out:
      if (nativeDependenciesReady()) return;  // 1. deps already landed
      if (lockIsStale(lockDir, STALE_MS)) {   // 2. crashed installer
        fs.rmSync(lockDir, { recursive: true, force: true });
        continue;                              //    reclaim and retry
      }
      if (waited >= MAX_WAIT_MS) {             // 3. give up loudly
        throw new Error('native install lock timed out after 2m');
      }
      sleep(WAIT_STEP_MS);
      waited += WAIT_STEP_MS;
    }
  }
}
```

Three exits when the lock is already held, in priority order:

- **Deps are ready.** Another process finished the install while we waited. Return, do nothing, let the server start. This is the common happy path for the second and third windows.
- **The lock is stale.** `lockIsStale` compares the lock directory's mtime against a 5-minute ceiling. A process that crashed mid-install leaves the lock dir behind forever; without reclamation, one crash wedges the whole team permanently. Older than 5 minutes means the holder is presumed dead, so we remove the lock and retry.
- **Otherwise wait, bounded.** Sleep 250ms and re-loop, up to a 2-minute ceiling, then throw. A live installer gets the time it needs; a pathological state fails with a clear message instead of hanging forever.

The sleep is a real blocking sleep, not a busy-spin:

```js
function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}
```

`Atomics.wait` on a throwaway `SharedArrayBuffer` blocks the thread for the duration without burning CPU. And the lock directory is removed in a `finally` around the install, so a successful holder always releases it.

The whole launcher fails closed. Any error, missing bundle, failed install, lock timeout, prints one line to stderr and exits non-zero:

```
[governed-brain] REFUSING TO START: <reason>
```

A server that cannot guarantee its own dependencies should not come up half-initialized and answer queries against a store that is not there. Refuse loudly. The operator sees the reason immediately.

## Proving it stays fixed

A fix you cannot regression-test is a fix with a shelf life. The environment assumption was invisible precisely because the author's machine always had `node_modules`. CI had the same problem: it installed deps before running tests, so it never exercised a clean install either.

The new smoke test removes that blind spot. `smoke/bootstrap-clean-install.mjs` copies the shipped plugin into a scratch directory with **no `node_modules`**, launches the actual MCP artifact through the bootstrap, and drives a full disposable round trip against local mode: capture a memory, govern it, read status, verify the audit chain, then clean up. It is wired into `.github/workflows/smoke.yml`, so CI now boots the plugin the way a teammate does. If a future change breaks the clean-install path, the smoke goes red before the release ships. It also exercises the lock path, which is what `test(plugin): harden bootstrap concurrency checks` covers.

## The general lesson, and two smaller ones

If you ship a plugin with native dependencies to any marketplace that installs by copying files, assume the install runs no build step. Provision deps yourself, at runtime, gated on a readiness check so you do nothing when there is nothing to do, and protected by a real lock because your process can start concurrently. Pin with `npm ci` so every install is the build you tested. Fail closed when you cannot.

Two hygiene fixes rode along in the same release, both small, both the difference between an install that reads clean to a new user and one that does not. The MCP manifest's `description` had command-shaped text in it, so it got rewritten as plain prose. A description is metadata a human reads, not a script, and shell syntax in a schema field is just noise that trips linters and confuses readers. And a team-onboarding README example pointed at an invalid API URL, corrected to a valid local example, so the first thing a new team user copies actually works.

This shipped as v1.1.2. The one-line version: copying files is not installing, and a plugin that assumes otherwise works only on the machine where the files were already installed.
