---
title: "Four production deploy gotchas: systemd, V8 JIT, tsc noEmit, Caddy"
description: "A mandy dashboard cutover surfaced four cross-layer deploy gotchas in fifteen minutes: tsc noEmit, systemd MemoryDenyWriteExecute vs V8 JIT, and two Caddy traps."
date: "2026-05-02"
tags: ["release-engineering", "devops", "systemd", "ci-cd", "monorepo"]
featured: false
---
Two release cadences collided on the same day. One was a thoughtful CI redesign that finally broke a four-month npm publish freeze across 400+ packages — good engineering, well-trodden ground. The other was a fifteen-minute production firefight on `mandy.intentsolutions.io` that surfaced four cross-layer deploy gotchas you would never know to look for until they hit you. Five releases in fifteen minutes, six commits, four production fixes, and a sixth release for the next layer of the system. The firefight is the one worth keeping in your runbook.

## The fifteen-minute firefight

Here is the timeline from the mandy repo on 2026-05-02 ET, copy-pasted from the git log:

```
20:20  PR #11  feat(dashboard): production deploy config                           v0.6.0
20:23  PR #12  fix(sidecar): emit dist/ on build (rootDir + --noEmit false)        v0.6.1
20:24  PR #13  fix(sidecar): drop MemoryDenyWriteExecute=true                      v0.6.2
20:34  PR #14  docs(dashboard): record the two deploy gotchas hit during cutover   v0.6.3
20:34  chore(beads): close MAND-8dm — dashboard deploy complete                    v0.6.4
20:35  PR #10  feat(orchestrator): Layer B Phase 1 — skeleton + compliance gate    v0.7.0
```

PR #11 was the production cutover for the dashboard sidecar — VPS paths, SOPS recipient, encrypted secrets. The kind of PR that should land green and stay green. Instead it was the first of four releases in the next fifteen minutes. Two of the four production gotchas surfaced as `fix:` commits in their own PRs (the `tsc noEmit` build gap, the systemd `MemoryDenyWriteExecute` crash). The other two surfaced during the Caddy step of the cutover script — fixed in place on the host, then committed as a docs PR (#14, the deploy README update) so the next dashboard deploy on the next host doesn't relearn them. Each was a one-symptom, one-cause, one-fix loop. Then the dashboard was actually live, the deploy bead got closed, and the next layer of the system shipped on top of it.

### Fix #1 — `tsc --noEmit` produces nothing, systemd cannot exec what does not exist

**Symptom.** systemd reported the unit failed to start. The journal showed the obvious error: `node: cannot find module dist/index.js`. The unit was correct. The path was correct. The build had supposedly run.

**Cause.** The sidecar's `package.json` build script was `tsc`. The `tsconfig.json` had `noEmit: true` set globally — a sane default when TypeScript is being used purely for type-checking and another tool (esbuild, swc, vite) handles the actual emit. But here nothing else handled emit. `pnpm build` was running, type-checking the project, exiting zero, and producing zero JavaScript files. `dist/` did not exist. The systemd `ExecStart=node dist/index.js` could not exec a file that was never written.

**Fix.** Two lines:

```diff
 // package.json
-"build": "tsc"
+"build": "tsc --noEmit false --outDir dist"
```

```diff
 // tsconfig.json
 {
   "compilerOptions": {
     "noEmit": true,
+    "rootDir": "./src",
     ...
   }
 }
```

The `rootDir` line is the smaller of the two changes but the one that matters for the output layout. TypeScript 5 inferred `rootDir` from the longest common prefix of all input files; TypeScript 6 changed the default to the tsconfig directory itself, and emits diagnostic 5011 when the new default would put outputs in a different place than the old inferred value. The build still compiles, but the output paths shift unless you set `rootDir` explicitly. Setting it to `./src` keeps `dist/` flat. The CLI flag `--noEmit false` overrides `noEmit` for the build invocation while leaving the in-editor type-check behavior unchanged. Verified locally with `pnpm build` producing `dist/{auth,config,index}.js`, the sidecar starting cleanly, `GET /healthz` returning 200.

**Transferable lesson.** `noEmit: true` is fine when TypeScript is a type-checker only. The moment the build artifact has to feed a runtime that wasn't TypeScript-aware (systemd, Docker `CMD`, a process manager that just wants a `.js` file), `noEmit` is silently catastrophic. Audit every `tsconfig.json` against the question: who consumes the output of `tsc`? If the answer is "nothing, because vite/esbuild handles it," `noEmit` is correct. If the answer is "node, directly," `noEmit` is a trap.

### Fix #2 — `MemoryDenyWriteExecute=true` versus the V8 baseline JIT

**Symptom.** SIGTRAP (exit status 133) from a freshly-spawned Node process under systemd means V8's baseline JIT tried to mark a page executable, the kernel refused, and the runtime trapped. Concretely: with `dist/index.js` now existing, systemd got further than the previous unit failure — and then the unit crashed on boot with status 133. Status 133 is signal 5 (SIGTRAP) plus 128 — the POSIX shell convention for encoding "process terminated by signal N" as exit status `128 + N`, which systemd inherits when it reports the unit's exit code. The journal had no Node-level stack trace because Node never got far enough to print one.

**Cause.** The sidecar systemd unit was using a modern hardening template — the kind that ships with `MemoryDenyWriteExecute=true` set by default. That directive installs a syscall filter that rejects any `mmap` call requesting `PROT_WRITE | PROT_EXEC` simultaneously, and — equally important — any `mprotect` call that adds `PROT_EXEC` to an existing mapping. Modern V8 actually uses W^X (write XOR execute): Sparkplug and the optimizing tiers (Maglev, TurboFan) write generated code into a writable page and then `mprotect` it to executable, never both at once. The directive blocks that `mprotect` transition just as effectively as it blocks the simpler W+X allocation, so V8 cannot even bootstrap; the first JIT page transition fails and the runtime SIGTRAPs.

**Fix.** Drop the directive. Keep the rest of the hardening profile.

```ini
[Service]
# Modern hardening — keep most of these, drop W^X for V8
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictNamespaces=true
RestrictRealtime=true
SystemCallArchitectures=native
# MemoryDenyWriteExecute=true   # ← removed: incompatible with V8 baseline JIT
```

**Transferable lesson.** Modern systemd hardening is genuinely good. The defaults assume static native binaries that never need to mmap a writable+executable page. Every JIT runtime — V8, JVM, .NET CLR, LuaJIT, PyPy — violates that assumption. If you copy a hardening template from a Rust or Go service onto a Node, Java, or .NET service, you will hit this. Either drop `MemoryDenyWriteExecute=true`, or use a runtime mode that doesn't JIT (Node has `--jitless`, but the throughput cost is brutal). The other dozen hardening directives are fine to keep.

### Fix #3 — Caddy access logs need pre-created files with the right ownership

**Symptom.** TLS terminator and reverse proxy was the next layer. Added a host block for `mandy.intentsolutions.io`, ran `caddy validate` (passed), ran `systemctl reload caddy`. The reload errored out: `permission denied` opening `/var/log/caddy/mandy-access.log`.

**Cause.** Caddy runs as the `caddy` user. When the Caddyfile names a per-host access log file, Caddy on reload tries to open or create that file with the running user's effective UID. If the file does not exist and the parent directory isn't writable by `caddy`, the open fails. If the file does exist but is owned by `root:root` from a previous touch, Caddy still cannot write to it. Either way: `permission denied`, reload aborted, the new host block does not become live.

**Fix.** Pre-create the log file with the right ownership before reloading Caddy:

```bash
sudo install -o caddy -g caddy -m 0644 /dev/null /var/log/caddy/mandy-access.log
sudo systemctl reload caddy
```

`install` is the right tool here; it atomically creates the file with the correct mode and ownership in a single syscall. A `touch` followed by a `chown` works but races against any process that opens the file in between.

**Transferable lesson.** The Caddy docs do mention this, but it is buried in the file-logger reference and easy to miss when you are scripting deploys for the first time. The general principle: any daemon that opens a per-resource log file at config-reload time needs that file to exist with the right ownership before the reload. The same trap applies to nginx with `access_log` directives that name new files, and to rsyslog when you add a per-program output destination. Bake the `install` call into the deploy script alongside the Caddyfile edit.

### Fix #4 — Caddy traversing `0750` home directories needs group membership and a full restart

**Symptom.** Caddy reload now succeeded (after fix #3), but the new host block returned 403 on every request to `mandy.intentsolutions.io`. The static dist was at `/home/intentsolutions/mandy/dashboard/dist/`. Caddy could see the host block was loaded. The site root path was correct. The 403 was Caddy refusing to read the directory.

**Cause.** `/home/intentsolutions/` was mode `0750` — the modern default for per-user home directories on a multi-tenant box. Mode `0750` means owner has rwx, group has rx, world has nothing. The `caddy` user is neither the owner nor in the group, so Caddy cannot even traverse into `/home/intentsolutions/` to reach the dist subdirectory. The 403 isn't from Caddy's own access control; it is the kernel refusing to let Caddy `open()` anything below that path.

**Fix.** Add `caddy` to the `intentsolutions` group, and restart (not reload) Caddy. (This assumes the `intentsolutions` group already exists — on this host it does because the `intentsolutions` user was created with a matching primary group.)

```bash
sudo usermod -a -G intentsolutions caddy
sudo systemctl restart caddy   # NOT reload — group membership only loads on process start
```

`systemctl reload` re-reads the Caddyfile but does not respawn the Caddy process; the running process keeps its original supplementary groups from when it was started. Group membership changes only take effect on a fresh `execve`. Reload is not enough; restart is required.

**Transferable lesson.** Two Linux fundamentals stacked. First: directory traversal requires `x` on every component of the path, not just the leaf. A `0755` dist directory is unreachable if its `0750` parent excludes you. Second: supplementary group membership is read once, at process spawn. Anywhere you cross the user-isolation boundary — a system service reading a user's home, a container picking up host volumes, a CI runner accessing a service account's working directory — both rules apply together. The cleanest mental model is: when you change which group a service runs as or belongs to, restart the service, do not reload it.

### What landed at 20:34 and 20:35

After the four fixes, the dashboard was actually live. The first two gotchas had already landed as fix commits in v0.6.1 and v0.6.2 — the JavaScript was in the patch. v0.6.3 wrote the two Caddy gotchas (the ones that were fixed in place on the host, not in code) into the deploy README so the next dashboard deploy on the next host doesn't relearn them. v0.6.4 closed the deploy bead with evidence. v0.7.0, fifteen minutes after the cutover started, shipped Layer B Phase 1 of the orchestrator — 1441 LOC, 45 files, the Python orchestrator scaffolded per spec, with the compliance gate (DNC scrub, TCPA quiet-hours fail-closed, twelve-zip service-area enforcement south of I-10) shipping at 100% line and branch coverage. The Pydantic v2 `Lead` schema is type-symmetric with the TypeScript `Lead` type on the dashboard side, frozen, with JSON round-trip tested. FastAPI `/health` is up, an APScheduler harness exists with no jobs registered yet, and every other module — enrich, score, draft, dispatch, sink, integrations, handlers — is a `NotImplementedError` stub waiting on Phase 2.

The dashboard going green at 20:34 is what unlocked Layer B going out at 20:35. That cadence is the point. When the foundation is shaky, every subsequent release waits. When the foundation lands clean, the next release ships immediately.

## The freeze break

Same day, different repo. `claude-code-plugins` v4.29.0 (PR #647) closed a four-month publish pipeline gap. Every `@intentsolutionsio/*` npm package was frozen at its first-published version — most since 2026-01-09 or 2026-04-21 — because there was no automated path from "code change merged" to "npm version bumped, published, tagged, released." Maintainers were either bumping versions by hand on selected packages or letting them sit. Across 400+ packages, "by hand" doesn't scale and "letting them sit" is the default outcome.

The design is three coordinated pieces, each minimal:

**Per-PR auto-bump.** A new script `scripts/auto-bump-changed-plugins.mjs` looks at every plugin whose source files changed in a PR (anything other than its own `package.json`), and bumps that plugin's patch version. A new workflow runs the bumper on every relevant PR and commits back to the PR head branch:

```yaml
# .github/workflows/auto-bump-on-pr.yml
on:
  pull_request:
    paths:
      - 'plugins/**'
      - 'packages/**'
jobs:
  auto-bump:
    if: >
      !contains(github.event.pull_request.labels.*.name, 'automation') &&
      !contains(github.event.pull_request.title, '[skip auto-bump]')
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.ref }}
      - run: node scripts/auto-bump-changed-plugins.mjs
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git commit -am "chore: auto-bump changed plugins" || exit 0
          git push
```

The bumper is idempotent. If a PR's only change to a plugin is its `package.json`, the bumper skips that plugin (preventing infinite version-bump loops on its own commits). Skip conditions on the workflow itself handle automation branches and explicit `[skip auto-bump]` opt-outs.

**Tags and GitHub Releases on every publish.** The existing publish workflow gets extended to create per-publish artifacts:

```yaml
# .github/workflows/publish-changed-packages.yml (excerpt of new step)
permissions:
  contents: write
  id-token: write
steps:
  - name: Publish to npm
    run: pnpm publish --access public --provenance
  - name: Create git tag
    run: |
      TAG="${PKG_NAME}@${PKG_VERSION}"
      git tag -a "$TAG" -m "Release $TAG"
      git push origin "$TAG"
  - name: Create GitHub Release
    run: |
      gh release create "${PKG_NAME}@${PKG_VERSION}" \
        --notes-file release-body.md \
        --generate-notes   # appends auto-generated notes after the file body (gh >= 2.20)
```

The tag convention `@scope/name@version` matches what lerna and changesets-managed monorepos use (turborepo itself is a build orchestrator and delegates publishing to changesets or semantic-release; in practice the tag format you end up with on a turborepo project is whatever its release tool writes). Existing tooling that parses tags in monorepos works against the same convention either way. The Release body includes the npm URL, the source path inside the monorepo, and the install command. Provenance attestations stay on.

**One-time bulk-bump utility.** `scripts/bulk-bump-versions.mjs` sweeps every `@intentsolutionsio/*` package and bumps the minor where the local version matches what's currently on npm. It is committed but deliberately not run as part of this PR. Firing it triggers a wave of roughly 400 publishes plus tags plus releases — that is a maintainer action you time, not something CI does on its own.

### Why not Changesets

The plan's original PR 3 was always going to be the auto-bump path. After feedback on best-practice visibility, **Changesets** got a real evaluation — it is the gold standard for npm monorepos for good reasons (explicit semver intent per change, human-curated changelog entries, pre-release modes, a clean release-PR workflow). The tradeoff broke this way: Changesets requires every PR to author a `.changeset/*.md` file describing intent. With 16 contributors and 400+ packages — most of which are markdown-only AI instruction sets, where the entire change is a paragraph rewrite — the per-PR `.changeset/*.md` ritual has no proportional payoff. The artifacts the maintainer ends up holding are equivalent: tags, releases, auto-generated notes. Auto-bump produces those from commit history; Changesets produces them from hand-written changeset files. Switching to Changesets later remains clean — the auto-bump can be removed, the changeset CLI added, and the publish workflow trigger pointed at the version-PR instead of the merge.

## Why the firefight is the keeper

The freeze break is good engineering. It is also well-trodden ground. Every npm monorepo of any size has written some version of "we picked auto-bump or Changesets and here is why." The decision is interesting in context but the mechanism is documented exhaustively elsewhere.

The four mandy gotchas are different. They are the kind of knowledge you would never know to look for until they hit you in production:

- Modern systemd hardening defaults like `MemoryDenyWriteExecute=true` are great — until you put a JIT runtime under them and the process SIGTRAPs before it can print a stack trace.
- `tsconfig` `noEmit: true` is a fine default for type-checking, and is silently catastrophic when something downstream actually needs the JavaScript.
- Caddy ownership on per-host log files is documented in the Caddy docs but easy to miss when you are scripting your first deploy and the failure mode (`permission denied` on reload) does not point you at log file ownership specifically.
- Group-traversal of `0750` home directories combined with the fact that supplementary groups are read once at process spawn is two Linux fundamentals stacked, and they bite cleanly the first time you cross the user-isolation boundary with a system service.

None of these is novel in isolation. All of them are documented somewhere. The point is: when you are fifteen minutes into a production cutover and the journal says SIGTRAP, you do not have time to read three man pages and reconstruct the mechanism. You want a runbook entry that says "if Node systemd unit exits 133 on boot, check `MemoryDenyWriteExecute`." That entry is what v0.6.3 of the mandy repo committed to the deploy README. That is where this knowledge belongs — in the runbook, on the host, where the next deploy will see it.

The blog post is for context. The runbook is for the next deploy at 20:20 on a Friday.

## Also shipped

The same calendar day's commit surface had four other items that don't fit either cadence above but are worth flagging because each closes a smaller production gap:

- **claude-code-plugins #648** — Skyvern promoted to Killer Skill of the Week (2026-W18) with auto-render tooling for the spotlight rotation. Skyvern files synced via #650.
- **claude-code-plugins #651** — Umami tracker wired into BaseLayout, closing the empty-data gap the analytics dashboard had been showing since the site went live.
- **braves #99** — post-VPS-migration cleanup: Firebase and skill artifacts evicted, CLAUDE.md tightened. Plus a `.env` materialization fix (braves-5ks) closing the gap that opened when the repo moved to SOPS.
- **nixtla** — strategic vision v2.0 landed, cutting the Trinity flagship from scope. README and pyproject versions re-aligned with VERSION/CHANGELOG/git tag in the same commit.

## Related Posts

- [VPS as the Home — Day 1, Eight Deploy Iterations](/posts/vps-as-the-home-day-1-eight-deploy-iterations/)
- [Propagation Day — When the Spec Becomes the Migration Plan](/posts/propagation-day-when-the-spec-becomes-the-migration-plan/)
- [Audit Harness v0.10 — Enforcement Travels with the Code](/posts/audit-harness-v010-enforcement-travels-with-code/)
