# Loop Discipline

The skill is turn-based. Each turn, the AI host increments `ITER` and runs **exactly one** of three branches against `appium.js`: observe (`screen`), act (an Appium call), or control (end the cycle). The branch the host picks depends on what happened the previous turn — see "Branch decision guide" below.

## One branch per turn

The host exports `ITER` once per turn (`export ITER=$((ITER + 1))`). Every `appium.js` invocation in that turn reads it from env — no `--iter` flag on individual calls.

| Branch | Command | Effect |
|---|---|---|
| **screen** | `node appium.js screen --session-id <id> --session-dir <d>` [`--xml-only` \| `--png-only`] | Default writes BOTH `iter-<N>.xml` and `iter-<N>.png`. Emits `{hash, xmlBytes, pngBytes}` on stdout. |
| **act** | `node appium.js <argv> --session-dir <d>` | Issues the Appium call. Writes `iter-<N>.request.json` + either `iter-<N>.response.json` (success) or `iter-<N>.error.json` (any failure: Appium error, network, parse, usage). |
| **control** | `node appium.js control --done\|--blocked --reason "..." --session-dir <d>` | Writes `iter-<N>.control.json`; no HTTP call. Signals the host to end the cycle. |

The host picks one branch per turn. The script always exits 0; failures are detected by reading `iter-<N>.error.json`.

### Why PNG is captured by default

Native overlays (Chrome's "notifications" welcome card, OS-level permission prompts, system dialogs that appear over the app/webview) are NOT reflected in the webview's `/source` XML — the chromedriver page-source layer only sees the in-page DOM, not what's drawn on top. A turn that captures XML-only can completely miss a blocking dialog and lead the host to act on a stale picture.

The first pilot run hit exactly this: it opened Chrome, captured `about:blank` XML, and tried to navigate without seeing the "Chrome notifications make things easier — Continue / No thanks" welcome card. PNG-by-default catches that class of failure on iteration 1.

Use `--xml-only` when you trust the source XML is complete (e.g., known-stable native screens where you're just confirming a hash change) and want to save tokens. Use `--png-only` for verification turns where layout is the only signal that matters (e.g., confirming an animation finished, checking image rendering).

## Branch decision guide

Pick the next turn's branch based on what just happened:

| Previous turn outcome | Next branch | Why |
|---|---|---|
| `screen` just ran | **act** | You have a fresh observation; decide what to do. |
| `act` succeeded | **screen** | The screen probably changed; observe before the next decision. |
| `act` returned `no such element` / `invalid selector` / `invalid argument` / bad-input | **act** (again, with a corrected call) | The action didn't fire, so the screen didn't change. The previous `iter-K.xml` is still current — re-read it from disk if needed; don't burn an ITER on a fresh `screen`. |
| `act` returned `stale element reference` | **screen** | The element id is from a prior state; you need fresh element ids from a new observation. |
| `act` returned HTTP 5xx / network timeout | **act** (retry the same call) | Transient failure; retry once. If it fails twice, `control --blocked`. |
| Goal reached | **control --done** | End the cycle cleanly. |
| Stuck (per "Stuck patterns" below) | **control --blocked** | End the cycle and surface the reason to the user. |

The host is responsible for remembering which `iter-K.xml` represents the current screen state. After a successful `act`, the most recent `iter-K.xml` is stale until the next `screen`. After a failed `act`, the most recent `iter-K.xml` is still current.

For how to actually construct the `act` call body from the observed XML — selector strategies, the find-element → element-id workflow, when to fall back to coordinates — see `endpoint-reference.md` "Building Appium calls from the observed XML".

## Artifact layout

```
.kobiton/sessions/<session-id>/
  caps.json                            ← desired caps used to open the session
  iter-001.xml                         ← page source (stripped on webview turns; raw on native)
  iter-001.full.xml                    ← only on webview turns — raw /source for selector escape hatch
  iter-001.png                         ← skipped only when `--xml-only` is passed
  iter-001.request.json                ← {argv: [...]} — what the host invoked
  iter-001.response.json               ← raw Appium response on success
  iter-001.error.json                  ← raw Appium error on failure (line 1 = {status}; line 2+ = body)
  iter-001.control.json                ← only when the host emitted `control` (instead of an Appium call)
  iter-002.xml
  ...
  session.log                          ← human-readable timeline
```

Workspace-relative, NOT `/tmp`. Consistent with `run-interactive-cli-session` so existing post-session tooling (test-case authoring, video pickup) finds artifacts in the same place.

## Iteration ceiling

Hard cap at `MAX_ITERS=100` iterations per session — when the cycle crosses that count, end with `exit 0`; the trap cleans up. Override per session with `MAX_ITERS=<n>`. Disk is not rotated (a 100-iter session is ~50MB worst case with screenshots); the workspace's per-session directory is the user's to clean up.

This is a pure safety net against runaway cycles (host logic bugs, pathological flows). It is NOT the stuck-detection mechanism — see "Stuck patterns" below. Most real flows complete in 10-30 turns, well under the cap.

## Stuck patterns — host decides

The script does NOT enforce blocker thresholds. There is no `N_REPEAT`, no `N_UNCHANGED`, no `LAST_*` shell var. Mobile-Appium behavior is too diverse for fixed thresholds — a screen unchanged for 5 turns is normal during a lazy-load wait, but pathological after a tap on a "Submit" button. Only the AI host has the conversation context (intent, prior actions, prior observations) to make that call.

What the script provides:

- **`screen` emits `{hash, xmlBytes, pngBytes}`** on stdout. Track the hash across turns in your conversation context to detect repetition.
- **`iter-N.request.json`** — every prior call's audit, available for re-reading.
- **`iter-N.error.json`** — full raw Appium error from any recoverable failure.

What the host decides:

- When to keep going.
- When to wait (re-run `screen` without an act — a "no-op observe" turn).
- When to emit `control --blocked` to pause and ask the user.
- When to emit `control --done` because the intent is satisfied.

### Stuck-pattern examples

#### 1. Same-call repetition (selector misses)

You tapped an xpath, got `no such element`. You try the same xpath again, same error. Two consecutive identical recoverable errors on the same selector → that selector is wrong. Either pick a different strategy/value, or `control --blocked` if you genuinely can't tell what the right selector is.

```
iter 5: actions --session-id S --type touch ...  → "no such element"
iter 6: actions --session-id S --type touch ...  → "no such element"
       (same argv, same error)
Decision: don't repeat a third time. Either re-read iter-6.xml for a better
selector, or control --blocked with reason "selector missed twice; need user".
```

#### 2. Screen oscillation (A → B → A)

You tapped to navigate to B, then tapped back to A. Your conversation memory shows this hash existed at iter N-2. Programmatic same-call detection misses this (the argvs differ); only your context catches it.

```
iter 3: hash=aaa…  (Settings screen)
iter 4: tap "Bluetooth" → hash=bbb… (Bluetooth screen)
iter 5: tap "Back" → hash=aaa… (Settings screen again)
iter 6: tap "Bluetooth" → hash=bbb…
iter 7: tap "Back" → hash=aaa…
       (your prior 4 turns formed an A-B-A-B loop)
Decision: control --blocked with reason "navigated in a circle between
Settings and Bluetooth without completing the intent".
```

#### 3. Lazy load / no visible animation

You tapped a "Load more" button. The list re-fetches over the network with no spinner. The hash from `screen` doesn't change for several turns. Don't panic — the page is loading. Re-run `screen` as a no-op observe to wait.

```
iter 8: tap "Load more"
iter 9: screen → hash=X (page still loading)
iter 10: screen (no act) → hash=X
iter 11: screen → hash=Y (page rendered)
Decision: re-emit `screen` for as many turns as the use case suggests is
reasonable. Track the hash yourself; an unchanged hash is data, not a
deadline.
```

A useful timeout heuristic: ~10–15 no-op-observe turns ≈ 30s at typical Appium latency. If the screen still hasn't changed by then, that's evidence (not proof) the load failed — re-tap, change strategy, or `control --blocked`.

#### 4. Credentials prompt / OAuth / WebView login

The screen shows a username/password form, a "Sign in with Google" SSO redirect, or any flow that needs human input the host can't supply. This is a hard block — emit `control --blocked` immediately.

```
Decision: control --blocked with reason "Sign-in screen detected; need user
credentials to proceed".
```

#### 5. CAPTCHA / robot-check

Visual challenges, slider puzzles, reCAPTCHA iframes. Same as #4 — emit `control --blocked`.

#### 6. Network spinner indefinitely

A spinner is present in the source XML and isn't going away. After enough no-op observes (your judgment — typically ≥10 turns with no change AND a visible spinner), conclude the request is hung.

```
Decision: control --blocked with reason "Network request stuck for ~30s;
recommend retry or check connectivity".
```

#### 7. Modal stack you can't dismiss

Two modals overlap. Tapping the visible one's dismiss button doesn't reach the underlying one.

```
Decision: control --blocked with reason "Two stacked modals; the top one
won't dismiss with available controls". User may need to suggest a swipe
or a hardware-back-button approach.
```

When you emit `control --blocked`, post one concise line in the conversation: `I can't make progress on iter=<N>. <observed condition>. What would you like me to do?` — actionable, lets the user redirect.

## Termination

The cycle ends when **any one** of these is true:

- AI host runs `node appium.js control --done --reason "..."`. Reason is appended to `session.log`; the trap ends the WebDriver session.
- User issues a stop command (or Ctrl-C). The trap cleans up.
- Kobiton platform-side session termination. The next `appium.js` call returns exit 3 with `error: session-not-found` or `error: invalid session id`. The trap cleans up (no-op since the session is already gone).

There is no arbitrary action-count cap. There is no wall-clock cap inside this skill. The platform-side session-duration cap (set by the org plan; not configurable here) is the absolute ceiling.

## Try/finally cleanup contract

```bash
SESSION_ID=""
trap 'cleanup' EXIT INT TERM

cleanup() {
  [ -z "$SESSION_ID" ] && return 0
  delete_err=$(node "$SCRIPT_DIR/scripts/appium.js" \
    --method DELETE --url "/session/$SESSION_ID" 2>&1 >/dev/null)
  if [ -z "$delete_err" ]; then
    printf '%s session=%s end-via-trap status=COMPLETE\n' "$(date -u +%FT%TZ)" "$SESSION_ID" >> "$SESSION_DIR/session.log"
  else
    printf '%s session=%s end-via-trap delete-failed err=%s\n' "$(date -u +%FT%TZ)" "$SESSION_ID" "$delete_err" >> "$SESSION_DIR/session.log"
  fi
}
```

`appium.js` treats `DELETE /session/{id}` returning 404 as success (idempotent), so the trap is safe to fire even if the session has already been ended by the loop's DONE path or by Kobiton's platform-side cap. The `DELETE` is the **only** cleanup path — it ends the WebDriver session cleanly and Kobiton records the session state as `COMPLETE`.

Do NOT call the `terminateSession` MCP tool as a belt-and-braces follow-up: it marks the session `TERMINATED` (treated as an abnormal exit by the recording pipeline, distinct from `COMPLETE`). Reserve it for the force-kill case where the `DELETE` is genuinely unreachable AND the user asks to force-kill. If the `DELETE` fails silently, the session times out on its own per `appium:newCommandTimeout` — preferable to a `TERMINATED` mark.

## Reading errors

`appium.js` exits 0 for **all** Appium calls — successful and failed. The script does NOT classify "recoverable" vs "fatal". That classification is the host's judgment, made by reading `iter-<N>.error.json` (and the prior conversation context).

When a call fails, `iter-<N>.error.json` contains:

- **Line 1:** a `{status}` JSON summary (HTTP status code; `0` for runtime errors like timeout / parse / network).
- **Line 2+:** the raw response body verbatim. For Appium HTTP errors this is typically `{value: {error, message, stacktrace}}`. For runtime errors (script never reached the server) it's the script's own `{error, message}` JSON. For non-Appium error pages (HTML, plaintext from a misconfigured proxy, etc.) it's whatever the server sent.

The host detects failure by checking whether `iter-<N>.error.json` exists in the per-turn block. If present, read it before emitting the next turn's call.

### Re-plannable Appium errors (typically: continue, try again)

These are the classic W3C error values where the right move is usually a re-plan (different selector, refreshed source, slight timing adjustment):

- **`no such element`** — selector didn't match. Re-read the updated `iter-<N>.xml`, try a different strategy (xpath → accessibility id, or vice versa) or a more specific value. If repeated on a webview turn AND the target is clearly visible in `iter-<N>.png`, the identifying attribute may have been stripped from the DOM — open `iter-<N>.full.xml` (raw `/source`) for that turn, find the real attribute, build the selector against it. The next turn's selectors go back to `iter-<N>.xml`.
- **`stale element reference`** — element id is from a prior screen state. Re-find the element from the current source.
- **`invalid selector`** — XPath / accessibility-id syntax is wrong. Fix the syntax.
- **`invalid argument`** — usually the body shape doesn't match what Appium expects for that endpoint. Re-read Appium docs and correct the body.
- **HTTP 408** (gateway timeout) — Kobiton hub didn't get an answer in time. Retry once; if it fails again, that's a stronger signal.
- **`timeout`** (W3C) — Appium itself timed out (often during element wait). Retry, or use `POST /session/{id}/timeouts` to relax the implicit wait.

### Likely-fatal errors (typically: end the cycle with `control --blocked`)

- **`invalid session id`** (HTTP 404) — the session is gone server-side. The trap will clean up. Nothing to do but report to the user.
- **HTTP 5xx** — Kobiton platform error. Retry once; if it fails again, the platform may be having issues. `control --blocked`.
- **HTTP 401 / 403** — credentials expired or invalid. Tell the user to re-run `/automate:setup` or re-authenticate MCP.
- **Non-Appium error pages** (HTML, plaintext, empty body) — something is very wrong with the request path or the platform. Report to the user.
- **`status: 0` with `error: "request-timeout"`** — network timeout (script-side). Retry once; if it fails again, network issue.
- **`status: 0` with `error: "runtime"`** — uncaught script exception. Real bug. Report.

### Judgment cases

When you're not sure, read the full body. The Appium `message` and `stacktrace` fields often contain hints about the cause. If after reading you still can't tell whether to retry or stop, emit `control --blocked` with the error summary as the reason — the user can redirect.

## Capture-warning for unsupported endpoints

See `references/endpoint-reference.md` "Unsupported-for-capture endpoints" for which endpoints are NOT in the Kobiton scriptless-capture allowlist (today, `/execute/sync` for `mobile:` commands). Actions hitting those endpoints still execute, but they won't appear in `saveTestCase` output. Pick an allowlisted endpoint when capture matters.
