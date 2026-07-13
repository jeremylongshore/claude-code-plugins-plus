# Endpoint Reference

The skill speaks Appium's WebDriver protocol directly. There is no synthetic action language — the AI host emits raw Appium calls via `appium.js`.

Two ways to call:

- **Generic mode:** `node appium.js --method <GET|POST|DELETE> --url <path> [--req-body <json or @file>]`
- **Helpers:** `node appium.js actions ...` and `node appium.js touch-perform ...` for the two endpoints where W3C / MJSONWP boilerplate is too verbose to type by hand.

`appium.js` reads `~/.kobiton/.credentials` (written by `/automate:setup`) on each invocation. No credential flags or env vars.

## Building Appium calls from the observed XML

Every Appium call that targets an element follows the same workflow: **observe → read the XML → build a selector from the XML → find element → use the returned element id in the interaction call**. Selectors are **not invented**; they come from attributes you can see in `iter-K.xml`. Inventing a selector (guessing an id or class name that "should" exist) is the most common cause of `no such element` errors.

### Selector strategies, in preference order

When more than one strategy works for a target, prefer the higher-listed one. The reasons are speed, stability across screens, and survivability when the app's UI changes. The preference order differs by context — native (`NATIVE_APP`) vs web (a browser session or `WEBVIEW_*` context).

**Native context (UiAutomator2 / XCUITest):**

1. **`accessibility id`** — `content-desc` on Android, `name` on iOS (the accessibility label). Fastest lookup; intentionally exposed for testing; most stable across releases. Use whenever a `content-desc` (Android) or `name` (iOS) attribute is present and meaningful.

2. **`id`** (resource-id on Android, `name` on iOS) — second-fastest. Stable across screens within the same app version, less so across versions. Note: this is the Appium `id` strategy, **not** the opaque element-id returned by `POST /element` (that one is for use in interaction calls, see below).

3. **`xpath`** (relative > absolute) — slow but expressive. Prefer **relative xpath** (`//*[@content-desc='settings_btn']` on Android, `//XCUIElementTypeButton[@name='Settings']` on iOS) over absolute paths (`/hierarchy/android.widget.FrameLayout[1]/.../android.widget.Button[3]`). Absolute paths are brittle — any structural change to the screen breaks them. Use relative xpath when the target has no `content-desc`/`id` but has a distinctive attribute (`text`, `name`, `value`, `label`, or a unique combination).

4. **`class name`** — last resort. Matches the widget class (`android.widget.Button`, `XCUIElementTypeButton`). Almost always ambiguous (many buttons on a screen); only useful when combined with the index in xpath. Avoid as a top-level strategy.

**Web context (browser session or `WEBVIEW_*`)** — switch context first with `POST /session/{id}/context`, then read the DOM via `/source`:

1. **`css selector`** — preferred. On ChromeDriver, CSS selectors are generally faster and less brittle than XPath. Anchor on stable attributes: `[aria-label='Search']`, `#search_query`, `input[name='q']`, `[data-testid='result-0']`.

2. **`xpath`** (relative) — when CSS can't express the target (e.g. selecting by visible text: `//button[normalize-space()='Continue']`). Same brittleness caveats as native — anchor on attributes, not positional indices.

### The find-element → element-id workflow

```
1. screen                → iter-K.xml (the source)
2. read iter-K.xml       → find the target node + its attributes
3. POST /element         → body: {"using": "<strategy>", "value": "<selector>"}
                           response: {"value": {"element-6066-11e4-a52e-4f735466cecf": "<id>"}}
                                     OR: {"value": {"ELEMENT": "<id>"}}  (older drivers)
4. extract the id        → it's opaque (e.g. "00000000-0000-0000-3e00-000000000000")
5. use it                → in /element/{id}/click, /element/{id}/value, /element/{id}/clear,
                           /touch/longclick body, etc.
```

The element id is only valid **for the current screen state**. After the screen changes (a successful tap, navigation, etc.) the id is stale — re-`screen` and re-`POST /element` to get a fresh id. (The skill loop's "stale element reference" error is the symptom of skipping this rule.)

### Example: tap by accessibility id

XML excerpt (from `iter-3.xml`):

```xml
<android.widget.ImageButton
    index="2"
    text=""
    resource-id="com.example.app:id/settings_btn"
    content-desc="Open Settings"
    class="android.widget.ImageButton"
    clickable="true"
    bounds="[864,1872][1008,2016]" />
```

Build the selector (prefer `accessibility id` because `content-desc` is meaningful):

```bash
# Turn N+1 — find the element
node appium.js --method POST --url /session/$SID/element \
  --req-body '{"using":"accessibility id","value":"Open Settings"}' \
  --session-dir $DIR

# Read iter-(N+1).response.json → extract the element id, e.g. "el-9"
# Turn N+2 — click it
node appium.js --method POST --url /session/$SID/element/el-9/click \
  --req-body '{}' \
  --session-dir $DIR
```

The same strategy works on iOS — the accessibility label is the `name` attribute on an `XCUITest` element, so `<XCUIElementTypeButton name="Open Settings" .../>` is found with the identical `{"using":"accessibility id","value":"Open Settings"}` body.

### Example: tap by relative xpath

XML has no `content-desc`, no useful `resource-id`, but a unique `text`:

```xml
<android.widget.Button
    text="Continue"
    resource-id=""
    class="android.widget.Button"
    bounds="[100,1800][620,1920]" />
```

```bash
node appium.js --method POST --url /session/$SID/element \
  --req-body '{"using":"xpath","value":"//android.widget.Button[@text=\"Continue\"]"}' \
  --session-dir $DIR
```

If two buttons share `text="Continue"`, narrow with a parent / sibling predicate from the XML — not by adding index unless that's the only thing distinguishing them. Index in xpath is the structural-change foot-gun the warning above is about.

### Example: type into a text field by resource-id

```xml
<android.widget.EditText
    resource-id="com.example.app:id/email_input"
    text=""
    bounds="[60,820][1020,940]" />
```

```bash
# Step 1 — find
node appium.js --method POST --url /session/$SID/element \
  --req-body '{"using":"id","value":"com.example.app:id/email_input"}' \
  --session-dir $DIR
# → element id, e.g. "el-12"

# Step 2 — type (POST /element/{id}/value is the allowlisted endpoint)
node appium.js --method POST --url /session/$SID/element/el-12/value \
  --req-body '{"text":"user@example.com"}' \
  --session-dir $DIR
```

### When to use coordinates instead

Element-based interaction is always preferred (more stable, capturable, readable in the saved test case). Coordinates are a fallback for the cases element-based can't reach:

- **Scrolling a custom view** that doesn't expose scrollable children in the XML.
- **Dragging on a canvas** (drawing apps, signature pads, map gestures).
- **Swiping a carousel** that doesn't fire on element-level swipes.
- **Tapping a region of an image** without an underlying element.

**Coordinates come from the XML, too** — never invented. Read the target element's `bounds` attribute (Android: `[x1,y1][x2,y2]`; iOS exposes `x`/`y`/`width`/`height`) and compute the point you need:

- **Center of an element**: `cx = (x1+x2)/2`, `cy = (y1+y2)/2`.
- **Top edge of a scrollable region** (for a downward swipe to scroll up): `(cx, y1 + 50)`.
- **Bottom edge**: `(cx, y2 - 50)`.

Example — scroll a list down 800 pixels:

```xml
<!-- The scrollable list in iter-7.xml -->
<androidx.recyclerview.widget.RecyclerView
    bounds="[0,300][1080,2100]" />
```

Center: `(540, 1200)`. To scroll content **down** (finger moves **up**):

```bash
node appium.js actions --session-id $SID --type swipe \
  --from-x 540 --from-y 1800 \
  --to-x   540 --to-y    600 \
  --duration 300 \
  --session-dir $DIR
```

`swipe` (via `/actions`) is allowlisted and capturable. Prefer it over `execute/sync` + `mobile: scroll` whenever you'd like the action to appear in the saved test case.

### Appium 1.x vs 2.x

The guidance above is the W3C / Appium 1.x surface that Kobiton exposes today. Appium 2.x adds convenient gesture commands via `POST /session/{id}/execute/sync` with `mobile:` script names (`mobile: scroll`, `mobile: dragGesture`, `mobile: pinchOpenGesture`, `mobile: longClickGesture`, etc.). These work, but `/execute/sync` is **not** in the scriptless-capture allowlist — actions hitting it won't appear in `saveTestCase` output. Pick a W3C / MJSONWP equivalent (covered by the tables below) whenever capture matters.

When no allowlisted equivalent exists (e.g., `mobile: pinchOpenGesture` has no W3C analog), `/execute/sync` is the fallback. The skill works; only the saved test case is incomplete for that step.

## Allowlisted endpoints — emit these whenever possible

The Kobiton platform records actions hitting these endpoints into the saveable test case (consumed by `saveTestCase`). Other Appium endpoints work but are not recorded for capture — see "Unsupported-for-capture endpoints" below.

### Element discovery and interaction

| Intent | Method | URL pattern | Body | Notes |
|---|---|---|---|---|
| Find element | POST | `/session/{id}/element` | `{"using":"<strategy>","value":"<selector>"}` | strategies: `xpath`, `accessibility id`, `id`, `css selector`, `class name` |
| Find multiple elements | POST | `/session/{id}/elements` | `{"using":"<strategy>","value":"<selector>"}` | |
| Get active element | POST | `/session/{id}/element/active` | `{}` | |
| Click element | POST | `/session/{id}/element/{el}/click` | `{}` | |
| Type into element | POST | `/session/{id}/element/{el}/value` | `{"text":"<string>"}` | use after find + focus |
| Clear element | POST | `/session/{id}/element/{el}/clear` | `{}` | |

### W3C gestures (`/actions`)

Use the `actions` helper — these get verbose otherwise.

| Intent | Command | Equivalent body sent to `/session/{id}/actions` |
|---|---|---|
| Single tap | `node appium.js actions --session-id <id> --type touch --x N --y N [--hold-ms 50]` | W3C pointer sequence: move → down → pause → up |
| Long-press at coords | `--type touch --x N --y N --hold-ms 1000` | same shape, longer pause |
| Swipe / drag | `node appium.js actions --session-id <id> --type swipe --from-x A --from-y B --to-x C --to-y D [--duration 300]` | W3C pointer sequence: move → down → move(duration) → up |
| Key press (single) | `node appium.js actions --session-id <id> --type key --key "<W3C key>"` | W3C key sequence: keyDown → keyUp |

For element-anchored long-press, prefer `POST /session/{id}/touch/longclick` (next section) — it's the legacy MJSONWP endpoint Kobiton's allowlist recognizes for element-targeted long press.

### Legacy MJSONWP touch (`/touch/longclick`, `/touch/perform`)

| Intent | Method | URL pattern | Body | Notes |
|---|---|---|---|---|
| Long-press element | POST | `/session/{id}/touch/longclick` | `{"element":"<el>","duration":1000}` | |
| Long-press at coordinates | POST | `/session/{id}/touch/longclick` | `{"x":N,"y":N,"duration":1000}` | |
| Multi-step touch gesture | helper: `node appium.js touch-perform --session-id <id> --steps @<file>` | `/session/{id}/touch/perform` body: `{"actions":[{"action":"press","options":{"x":N,"y":N}},{"action":"wait","options":{"ms":1000}},{"action":"release"}]}` | Steps live in a JSON file; common when reproducing recorded Kobiton test cases |

### Device controls

| Intent | Method | URL pattern | Body |
|---|---|---|---|
| Press hardware keycode (Android) | POST | `/session/{id}/appium/device/press_keycode` | `{"keycode":N}` (e.g. 4=BACK, 3=HOME, 24=VOL_UP) |
| Press back (Android shortcut) | POST | `/session/{id}/back` | `{}` |
| Rotate device | POST | `/session/{id}/orientation` | `{"orientation":"LANDSCAPE"\|"PORTRAIT"}` |
| Hide keyboard | POST | `/session/{id}/appium/device/hide_keyboard` | `{}` |
| Set geolocation | POST | `/session/{id}/location` | `{"location":{"latitude":N,"longitude":N,"altitude":N}}` |
| Send keys | POST | `/session/{id}/keys` | `{"value":["<char>","<char>",...]}` |

### Read-only (always allowlisted; GETs are wildcard-allowlisted)

| Intent | Method | URL pattern |
|---|---|---|
| Get page source (XML) | GET | `/session/{id}/source` *(prefer the `screen` helper)* |
| Get screenshot (base64 PNG) | GET | `/session/{id}/screenshot` *(prefer the `screen` helper — captures PNG by default)* |
| Get current context | GET | `/session/{id}/context` |
| List contexts | GET | `/session/{id}/contexts` |
| Get current orientation | GET | `/session/{id}/orientation` |
| Get session info | GET | `/session/{id}` |

The `screen` helper combines `/source` and `/screenshot` into one call, writes both artifacts to disk, and emits a hash for blocker detection — see "Observe with `screen`" below. Prefer it over the raw GETs unless you need a different reason to read source or screenshot.

### Observe with `screen` helper (one of three per-turn branches)

`screen` is one of three branches the host can pick per turn (the others are `act` and `control` — see `loop-discipline.md`). Use it when the screen state has likely changed (after a successful act, at session start, or to verify mid-flow). Skip it on a turn that's retrying after a failed act — the previous `iter-K.xml` / `iter-K.png` is still current.

```
node appium.js screen --session-id <id> --session-dir <d> [--xml-only | --png-only]
```

(The iter number comes from the `ITER` env var the SKILL.md loop exports once per turn — no per-call `--iter` flag.)

- **Default: captures BOTH** — writes `<d>/iter-NNN.xml` AND `<d>/iter-NNN.png` (base64-decoded PNG).
- `--xml-only`: skips the screenshot. Use when you trust the source XML is complete (e.g., known-stable native screen) and want to save tokens.
- `--png-only`: skips the source. Use for visual-only verification turns (animation completion, image rendering).
- Emits a single JSON line on stdout: `{"hash": "<sha256>", "xmlBytes": N, "pngBytes": M}`. Track the hash in your conversation context across turns — repetition is a signal, never a forced stop.
- **Why both by default:** native overlays (Chrome's "notifications" welcome card, OS-level permission prompts, system dialogs) are NOT in the webview source XML. PNG-by-default catches that class of failure — see `loop-discipline.md` "Why PNG is captured by default".

### Control without an Appium call

```
node appium.js control --done    --reason "..." --session-dir <d>
node appium.js control --blocked --reason "..." --session-dir <d>
```

Writes `<d>/iter-NNN.control.json` (iter from `ITER` env var). No HTTP request. Signals end-of-cycle (DONE) or pause-and-ask (BLOCKED).

### Session lifecycle

| Intent | Method | URL pattern | Body |
|---|---|---|---|
| Create session | POST | `/session` | W3C `{"capabilities":{"alwaysMatch":{...}}}` — use `render-capabilities.js` |
| End session | DELETE | `/session/{id}` | (none; 404 treated as success — idempotent) |
| Switch context | POST | `/session/{id}/context` | `{"name":"NATIVE_APP"\|"WEBVIEW_..."}` |
| Set timeouts | POST | `/session/{id}/timeouts` | `{"implicit":N}` etc. |

## Web sessions (Chrome, mobile web, WebView)

### Reading the captured DOM

`iter-N.xml` is what you read. For webview sessions it is the **stripped DOM** — `<script>` / `<style>` / `<head>` / `<noscript>` blocks and `<img src="data:...base64,...">` blobs removed, attribute lists pruned to the ones an agent actually needs to drive (text, ids, names, classes, `aria-*`, `role`, `href`, `data-testid`, form-control attrs, ...). On the pilot YouTube run a 558KB raw body shrank to ~50KB — small enough to `Read` whole.

**Prefer `Read iter-N.xml` over `grep > probe.txt`.** Grepping into a workspace file used to be the only option when the raw DOM was too big to load; with the stripped DOM the standard Read tool handles the file in one shot. The shell pipeline (auto-backgrounding, file write, separate Read) is what made the first pilot drift past 19 minutes.

**Selector rule for stripped DOMs:** anchor relative xpath on stable attributes — `@aria-label`, `@id`, `@name`, `@href`, `@data-testid`, `@role`, `@class` — never on positional indices (`[3]`, `:nth-child`) or wrapper tag chains. Stripped tags collapse adjacent siblings, so any selector that counts position or threads through generic wrapper `<div>` / `<span>` is brittle.

**Escape hatch — `iter-N.full.xml`.** The raw `/source` body is also persisted on every webview turn. Open it only when a selector built from `iter-N.xml` returns `no such element` repeatedly but the target is visible in `iter-N.png` — that's the signal that the identifying attribute was in the strip list. Find the real attribute in the full DOM, build the selector against it, and the next turn's selectors go back to reading the stripped file.

Native sessions (`UiAutomator2` / `XCUITest`) write `iter-N.xml` as the raw source unchanged — no `iter-N.full.xml` is created, no strip happens. Detection is automatic from the source's leading token (`<html...` → strip; anything else → passthrough).

### Driving the page

Default to standard webview interactions — `find element` + `element click`, `element value`, or `execute/sync` in the `WEBVIEW_chrome_*` context. They work for most web flows and are the simplest path.

Switch to NATIVE_APP only when a webview approach can't do the job. Common symptoms:

- **Something covers the web page that isn't in the DOM** — a native modal, system dialog, permission prompt, or address-bar autofill. The PNG and the webview `/source` XML disagree (the source doesn't show what's blocking).
- **The web `click` succeeds at the HTTP layer but the page doesn't react** — the element doesn't accept clicks from the webview path (synthetic clicks lack user activation, container-webview not found, etc.). Re-issuing the click changes nothing.

When you do switch, treat the native UI tree as the new source of truth: switch context to NATIVE_APP, capture native XML via `screen`, find the element natively, and tap it natively. In the uncommon case where the element is missing from the native XML (rendered inside the webview canvas with no native-side mirror), fall back to a coordinates-based tap — derive coords from the native XML bounds if the surrounding native nodes pinpoint the target reliably, otherwise hop into `WEBVIEW_chrome_*` and call `getBoundingClientRect` for the web element to get viewport coords. Either way, the `actions` touch tap works from whichever context you're in — coordinate-based taps are context-agnostic.

```bash
# Only when a webview approach can't do the job.
node appium.js --method POST --url /session/$SID/context \
  --req-body '{"name":"NATIVE_APP"}' --session-dir $DIR

# Then capture native XML and find / tap the target natively (see the
# selector-construction guide above).
```

Caveats when staying in webview context with `execute/sync`: (1) not in the scriptless-capture allowlist — those actions won't appear in `saveTestCase` output; (2) the context name suffix can change (`WEBVIEW_chrome_1` → `..._3`) after any NATIVE_APP round-trip — always `GET /session/{id}/contexts` before switching back rather than reusing a cached name.

## Unsupported-for-capture endpoints

These work, but are **NOT** in the Kobiton scriptless-capture allowlist as of writing. The session keeps running; only the action's appearance in `saveTestCase` output is missing. Use only when no allowlisted alternative exists.

| Intent | Method | URL pattern | Body |
|---|---|---|---|
| Run Appium mobile command | POST | `/session/{id}/execute/sync` | `{"script":"mobile: <command>","args":[{...}]}` |
| Run JavaScript in webview | POST | `/session/{id}/execute` | `{"script":"...","args":[...]}` |

Common `mobile:` commands: `mobile: scroll`, `mobile: swipe`, `mobile: longClickGesture`, `mobile: doubleClickGesture`, `mobile: pinchOpenGesture`, `mobile: dragGesture`. **Refer to the official Appium docs** for the exact arg shapes — they vary by driver (UiAutomator2 vs XCUITest).

When the AI host emits an `execute/sync` call, log a one-line note in `session.log` so the dev knows that action won't appear in the saved test case:

```bash
# In the SKILL.md loop, after the act step:
if echo "$ACT_URL" | grep -q '/execute/sync'; then
  printf 'iter=%d capture-warning=execute/sync url=%s\n' "$N" "$ACT_URL" >> "$SESSION_DIR/session.log"
fi
```

## Loop-control sentinels (no Appium call)

The AI host signals loop termination by writing an `iter-N.control.json` file instead of an action:

```json
{ "control": "DONE",    "reason": "Settings page reached and toggle enabled." }
{ "control": "BLOCKED", "reason": "Two modal dialogs stacked; tapping the visible one dismisses nothing." }
```

The SKILL.md loop reads `iter-N.control.json` before dispatching any Appium call. Presence of `DONE` exits the loop cleanly (the trap ends the session); `BLOCKED` pauses and posts the reason to the conversation.

## How the host picks an endpoint

1. **Default to allowlisted.** Pick from the tables above — if the intent has an allowlisted endpoint, use it.
2. **Use a helper when boilerplate would be error-prone.** `actions` for W3C gestures, `touch-perform` for legacy multi-step touch.
3. **Fall back to `execute/sync` only when nothing else fits.** Log a capture-warning. Document the fallback in the action's reason field.
4. **Read Appium docs** when you need an `execute/sync` mobile command — the args differ by driver. The plugin doesn't ship the docs; treat the Appium project's `mobile-command-reference.md` as the authoritative source.

## Adding a new gesture

Today: there is no code change. Add a row to this table that documents the URL + body the host should emit. Done.

If the new gesture's body is verbose enough to be error-prone (think: a 6-sub-action W3C sequence with carefully placed pauses), consider adding a helper to `appium.js`. Helpers should be a thin wrapper around the generic POST + a body builder. Cover the helper with a co-located test case that asserts the assembled body shape. Use the existing `actions` and `touch-perform` helpers as templates.
