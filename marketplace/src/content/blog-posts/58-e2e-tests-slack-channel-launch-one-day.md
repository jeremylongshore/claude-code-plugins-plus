---
title: "58 E2E Tests, a Slack Channel Launch, and the Auth Injection That Made It Work"
description: "How REST API auth plus IndexedDB injection unlocked 58 production E2E tests for cad-dxf-agent, while claude-code-slack-channel went from zero to v0.1.0 with CI and upstream submission in one day."
date: "2026-03-20"
tags: ["testing", "ci-cd", "typescript", "automation", "claude-code", "full-stack"]
featured: false
---
You cannot run production E2E tests if you cannot log in. That sentence sounds obvious. It took sixteen commits to solve.

March 20th was a 25-commit day across three projects. The headline: cad-dxf-agent got a full production E2E test suite — 58 tests covering every user action — and a brand new project launched from empty directory to v0.1.0 with CI, tests, and upstream plugin submission. Plus the usual dependency bumps and a bug fix in the plugins marketplace.

## The Auth Problem Nobody Talks About

E2E testing against production is a different animal than E2E testing against localhost. On localhost, you control everything. Seed the database. Mock the auth provider. Bypass the login screen. In production, you're hitting real Firebase Auth, real Firestore rules, real Cloud Run services. The login screen isn't optional.

Playwright's standard approach is to fill in the email field, fill in the password field, click submit, and wait. That works until it doesn't. Firebase Auth has rate limiting. CAPTCHA challenges appear after repeated logins from the same IP. The auth state needs to persist across page navigations. And if your test suite has 58 tests, you're logging in 58 times — which triggers every abuse-prevention mechanism Firebase has.

### REST API + IndexedDB: The Injection Pattern

The solution has two parts.

**Part one: authenticate via REST API.** Instead of driving the browser through the login form, hit Firebase Auth's REST endpoint directly:

```typescript
async function getAuthTokens(email: string, password: string) {
  const response = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        returnSecureToken: true,
      }),
    }
  );
  const data = await response.json();
  return {
    idToken: data.idToken,
    refreshToken: data.refreshToken,
    localId: data.localId,
  };
}
```

No browser involved. No CAPTCHA. No rate limiting on the standard auth endpoint. You get back an ID token, a refresh token, and the user's UID.

**Part two: inject into IndexedDB.** Firebase's client SDK stores auth state in IndexedDB under a predictable key structure. After navigating to the app's URL (so the browser has the right origin), inject the tokens directly:

```typescript
async function injectAuthState(page: Page, tokens: AuthTokens) {
  await page.evaluate(async (t) => {
    const dbName = 'firebaseLocalStorageDb';
    const storeName = 'firebaseLocalStorage';

    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open(dbName, 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore(storeName);
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);

    store.put(
      {
        uid: t.localId,
        email: t.email,
        stsTokenManager: {
          refreshToken: t.refreshToken,
          accessToken: t.idToken,
          expirationTime: Date.now() + 3600 * 1000,
        },
      },
      `firebase:authUser:${t.apiKey}:[DEFAULT]`
    );

    await new Promise((resolve) => (tx.oncomplete = resolve));
  }, tokens);

  await page.reload();
}
```

After the reload, Firebase's client SDK reads IndexedDB, finds valid tokens, and the app thinks the user logged in normally. No login form. No CAPTCHA. Auth state survives navigation. One REST call per test run, not per test.

### Why This Matters

The injection pattern turns a 58-test suite from "flaky and slow" to "deterministic and fast." Each test starts already authenticated. No shared state between tests — each gets its own browser context with fresh tokens. The login flow gets tested exactly once, in a dedicated auth spec. Everything else skips straight to the feature under test.

## 58 Tests Covering Every User Action

With auth solved, the coverage is comprehensive: file operations (open, save-as, import), entity selection (click, multi-select, selection-to-edit binding), viewer interactions (pan, zoom, click-to-focus), edit operations (move, rotate, scale, delete, undo/redo), change review, LLM planner prompts, and error states (invalid DXF, network failures, auth expiry).

Every test runs against the production deployment. Not staging. Production. If a test fails, the feature is broken for real users right now.

## Selection Hardening: The Edge Cases

PR #124 fixed a category of bugs in selection-to-edit binding. The pattern: user selects an entity, triggers an edit operation, but the edit applies to the wrong entity or no entity at all.

Root causes:

1. **Stale selection state.** User selects entity A, the viewer re-renders (e.g., zoom change), selection ref still points to entity A's old DOM node. The edit operation reads the ref, finds a detached node, and silently fails.
2. **Race between selection and focus.** PR #121 added click-to-focus — clicking a change or operation in the sidebar focuses the viewer on that entity. But if the user clicked an entity in the viewer *while* the sidebar focus animation was running, both handlers fired. Selection won sometimes. Focus won other times.
3. **Multi-select to single edit.** User multi-selects three entities, then triggers a single-entity operation like "rotate." Which entity gets rotated? The answer was "whichever was selected last," which is non-deterministic if selections happened in rapid succession via shift-click.

The fix is boring and correct: selection state is now derived from a single source (a Set of entity IDs in the store), focus events clear and re-set selection explicitly, and single-entity operations on a multi-selection prompt the user to pick one.

## v0.10.0 and v0.10.1

Both releases shipped the same day. v0.10.0 included the E2E suite, selection hardening, and viewer improvements. v0.10.1 was a patch release for the dependency bumps — `actions/upload-artifact`, `setup-node`, `checkout`, and `google-auth` all got version bumps in CI workflows.

Splitting the dependency bumps into a separate release is deliberate. If a CI workflow breaks because of a new `actions/checkout` version, you can revert v0.10.1 without losing the actual feature work in v0.10.0.

## New Project: claude-code-slack-channel

Meanwhile, an entirely new project went from empty directory to published v0.1.0.

claude-code-slack-channel is a Claude Code skill that lets you interact with Slack channels. Not the Slack API in general — specifically the channel operations that developers actually need during a coding session: read recent messages, post updates, search for context, check who's online.

### Zero to v0.1.0 in Eight Commits

The commit log tells the story:

1. `feat: initial Slack channel for Claude Code` — Project scaffolding, core skill implementation, basic channel operations.
2. `feat: add test suite for security-critical functions` — Token handling, permission scoping, input sanitization. Tests first for the parts that can hurt you.
3. `feat: add CI pipeline, CLAUDE.md, and GitHub Pages` — GitHub Actions CI, documentation, and a published landing page.
4. `fix: Anthropic spec compliance — skill namespace, install commands, docs (#2)` — The skill spec has specific requirements for how skills are namespaced and installed. First pass got the namespace wrong.
5. `fix: plugin schema for upstream submission (#1)` — Schema validation for the claude-code-plugins marketplace. Different requirements than the Anthropic spec.
6. `v0.1.0 release` — Tagged, released, published.

Two things stand out.

**Tests landed in commit two.** Not commit six. Not "we'll add tests later." The security-critical functions — token storage, permission checks, input sanitization — were tested before the CI pipeline existed. The CI pipeline then ran those tests. This is the correct order.

**Two fix commits for two different spec compliance issues.** The Anthropic skill spec and the claude-code-plugins marketplace schema have overlapping but different requirements. The skill namespace format that Anthropic requires didn't match what the marketplace validator expected. PR #2 fixed Anthropic compliance. PR #1 fixed marketplace compliance. Both were blocking issues for upstream submission.

### The Source Whitelist Bug

Over in claude-code-plugins, a single commit fixed a registration bug: `fix: killer skill signup broken by source whitelist mismatch (#374)`. The marketplace maintains a whitelist of approved source URLs for skill registration. The whitelist check was comparing normalized URLs against non-normalized entries. A trailing slash difference was enough to reject a valid skill.

This is the kind of bug that looks trivial in the diff and blocks an entire feature launch. The Slack channel skill couldn't register in the marketplace until this was fixed.

## The Day in Numbers

| Metric | Count |
|--------|-------|
| Total commits | 25 |
| New E2E tests | 58 |
| New project launches | 1 |
| Releases shipped | 3 (v0.10.0, v0.10.1, v0.1.0) |
| PRs merged | 6 |
| Spec compliance fixes | 2 |
| Dependency bumps | 4 |

## What Carries Forward

The auth injection pattern is reusable. Any Firebase project that needs production E2E tests can use the same REST API + IndexedDB approach. The Slack channel skill is the beginning of a different pattern — Claude Code skills that bridge into team communication tools, so the workflow is "code, and the agent handles the communication" instead of constant context-switching.

Twenty-five commits. Three releases. One new project. The auth injection pattern alone was worth the day.

---

## Related Posts

- [Shipping a CAD Agent from Zero: DXF Parsing, Edit Engines, and LLM Planner Interfaces](/posts/building-cad-dxf-agent-from-zero-to-v010/) — The original cad-dxf-agent build
- [Session Cookie Auth, Forgot-Password Timeouts, and Killing Flaky E2E Tests](/posts/session-cookies-forgot-password-flaky-e2e-tests/) — Earlier deep-dive into auth and E2E stability
- [Golden Tests, Fuzz Testing, and a Nasty Fixture Taxonomy for DXF Revisions](/posts/golden-tests-fuzz-testing-dxf-revision-corpus/) — Testing infrastructure for the DXF comparison engine
