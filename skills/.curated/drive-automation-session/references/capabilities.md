# Capabilities

This skill talks WebDriver / Appium HTTP directly against the Kobiton hub. The capability payload sent on `POST /wd/hub/session` is rendered by `run-automation-suite/scripts/render-capabilities.js` (cross-skill reuse — both skills live in the same plugin).

## Invocation

```bash
node ../run-automation-suite/scripts/render-capabilities.js \
  --platformName "<Android | iOS>" \
  --udid "<udid>" \
  --deviceName "<device name>" \
  --platformVersion "<version>" \
  --automationName "<UiAutomator2 | XCUITest>" \
  --app "<kobiton-store:vXXXXX>" \
  --testingType app \
  --newCommandTimeout 1800
```

The `--newCommandTimeout 1800` flag is the key addition for this skill — it tells Appium not to terminate the session if no command arrives for 30 minutes. That window covers the human-in-the-loop pauses the skill enters when it gets stuck and asks the user.

The `--scriptlessCapture` flag emits `kobiton:scriptlessCapture: true`. This tells the Kobiton platform to record the session's WebDriver actions so the resulting session can be converted to a saveable test case via the `saveTestCase` MCP tool. This is the **single most important capability** for the skill — without it, the session id we return cannot be persisted as a re-runnable test case. The capability name evolved from `kobiton:scriptlessEnable` (older) to `kobiton:scriptlessCapture` (current). If you see "Session not created" errors mentioning either name, check which name the deployed Kobiton platform accepts; the skill currently emits only the new name.

Output is the desired-caps JSON written to `.kobiton/sessions/<session-id>/caps.json` and fed to `scripts/appium.js create-session --caps-file <path>`.

## Credentials → Hub URL

`appium.js` reads `~/.kobiton/.credentials` (written by `/automate:setup`) on every invocation, so they stay out of the AI host's transcript, argv, and env.

The composed hub URL is `https://{user}:{api_key}@{portal-host}/wd/hub` — for example, `https://api.kobiton.com/wd/hub`. The portal stored in `~/.kobiton/.credentials` is the API base (`https://api.kobiton.com`); the WebDriver path `/wd/hub` is appended by `appium.js`.

If `/automate:setup` has never been run on this host, the skill stops in Step 1 with a message pointing the user there. The setup command fetches credentials from the authenticated MCP context (the `getCredential` tool) and writes them to the file.

**Backward-compat:** `appium.js` still accepts `--hub-url <embedded-auth-url>` for callers that want to provide a pre-composed URL. The credential triple is preferred for new code.

## What the capability payload looks like

After `render-capabilities.js` runs:

```jsonc
{
  "kobiton:sessionName": "Automation test session",
  "kobiton:sessionDescription": "",
  "kobiton:aiToolName": "Claude",                  // or Codex / Copilot / Gemini, host-detected
  "kobiton:deviceOrientation": "portrait",
  "kobiton:captureScreenshots": true,
  "appium:noReset": true,
  "appium:fullReset": false,
  "appium:automationName": "UiAutomator2",         // platform-dependent
  "appium:newCommandTimeout": 1800,                // KEY ADDITION for this skill
  "appium:app": "kobiton-store:v72116",
  "appium:udid": "21161FDF60051K",
  "appium:deviceName": "Pixel 6",
  "platformName": "Android",
  "platformVersion": "15"
}
```

`scripts/appium.js create-session` wraps this in W3C `{capabilities: {alwaysMatch: ...}}` automatically — both raw and wrapped shapes are accepted.

## Platform cap on newCommandTimeout

Kobiton's platform-side session-duration cap (org-plan dependent) is the wall-clock bound on the session — it is independent of `appium:newCommandTimeout`. The two values do different things:

- `appium:newCommandTimeout: 1800` tells **Appium** not to time out the session for idleness (no WebDriver command in 30 min).
- The platform-side cap tells **Kobiton** to end the session after N minutes regardless of activity.

If Kobiton ever rejects a session-create with `newCommandTimeout: 1800` (HTTP 400 with a message about cap exceeded), lower the value here and update this doc. We have not observed this against Kobiton's public hub as of writing.

## App reference

The skill requires an `--app` value — a `kobiton-store:vXXXXX` reference uploaded ahead of time, OR a path the caller has just uploaded via the `uploadAppToStore` / `confirmAppUpload` MCP tools. The caller is responsible for ensuring an app is available before invoking the skill.

For web sessions (`--testingType web`), pass `--browserName safari` or `chrome` instead of `--app`.
