---
name: run-automation-suite
description: Run local Appium test scripts against Kobiton devices. Guides you through app upload, device selection, script capability parsing, and local execution.
---

## Workflow

### 1. Identify the app

**IMPORTANT: Always ask the user this question, even if they already provided an app file path. Do NOT skip ahead or start uploading automatically.**

Ask the user:

> "Would you like to:"
> 1. Upload a new app build
> 2. Use an existing app from Kobiton Store or a provided URL

Wait for their response before proceeding. Do not call any upload or app-related tools until the user responds.

**If uploading a new app:** Look for .apk, .ipa, .zip files in the project context, or ask the user for the file path. Upload via `uploadAppToStore` (permanent, visible in app repository). This is a three-step process: call the tool to get a pre-signed URL, upload the file via PUT, then confirm the upload.

**If reusing an existing app:** Check `appium:app` field of capabilities in the test script. Call `listApps` with that app version as keywork to check uploaded or not. Let the user pick the version to use (e.g., `kobiton-store:v72107`) if needed

### 2. Select a device

Ask the user which device or platform to target.

Call `listDevices` with the relevant platform filter to show available options.

If the user has a specific device in mind, confirm its availability with `getDeviceStatus`.

Reserve the device with `reserveDevice` if needed.

### 3. Identify script & parse capabilities

Ask the user for the path to their local Appium test script.

Detect the language and runtime from the file extension:

| Extension | Runtime | Command |
|-----------|---------|---------|
| `.js` | Node.js | `node <script> <udid>` |
| `.py` | Python | `python <script> <udid>` |
| `.cs` / `.csproj` | .NET | `dotnet test` |
| `.java` | Java | `mvn test` or `java -cp ...` |

Read the script file and extract key capabilities from the source code:

- `platformName` (Android / iOS)
- `udid` (hardcoded or parameterized)
- `app` (app URL or kobiton-store reference)
- `sessionName`, `sessionDescription`
- `automationName` (UiAutomator2, XCUITest, etc.)
- `browserName` (if browser-based test)
- `deviceOrientation`
- Any `kobiton:*` vendor extensions (especially `kobiton:runtime`)

Identify how the UDID is passed into the script (CLI argument, environment variable, or hardcoded) so it can be overridden with the selected device.

**Appium runtime:** Check if the script contains `'kobiton:runtime': 'appium'` or equivalent. If it does NOT, do not inject it — the default Kobiton runtime will be used. Only if the user explicitly asks to use the Appium runtime should you suggest adding `'kobiton:runtime': 'appium'` to the script's capabilities.

**Validate capabilities:** After parsing the script, run the render script to generate the correct capabilities for the selected device and app:

```
node skills/run-automation-suite/scripts/render-capabilities.js \
  --platformName <platform> \
  --udid <udid> \
  --deviceName "<deviceName>" \
  --platformVersion <version> \
  --automationName <automationName> \
  --app <app> \
  --testingType app
```

For web testing, replace `--app <app>` with `--browserName <browser> --testingType web`.

Compare the JSON output against the parsed script capabilities:

- **Must-match** (`platformName`, `platformVersion`, `appium:udid`, `appium:deviceName`, `appium:app`/`browserName`, `appium:automationName`): If different, show what will change and edit the script automatically. These must match the selected device/app.
- **Suggested defaults** (`kobiton:sessionName`, `kobiton:sessionDescription`, `kobiton:deviceOrientation`, `kobiton:captureScreenshots`, `appium:noReset`, `appium:fullReset`): If different or missing, show the diff and ask the user before changing. The user may have intentionally set different values.
- **User-controlled**: Any capabilities in the user's script that are not in the rendered output — leave untouched. Never inject or modify `kobiton:runtime` unless the user explicitly asks.

### 4. Confirm & execute

Present a summary to the user before running:

```
Language:     Node.js
Script:       /path/to/test.js
Platform:     Android
Device:       Pixel 4 (9B211FFAZ0017F)
App:          kobiton-store:v72107
Session Name: Verify Appium session
Command:      node /path/to/test.js 9B211FFAZ0017F
```

Wait for user confirmation, then execute the command via the Bash tool **in the background** (use `run_in_background: true`).

**Immediately after launching the script**, wait **2 seconds** (to allow the session to initialize on Kobiton), then open the running session in the user's browser.

**Determine the portal URL:** Read `.mcp.json` to get the MCP server URL, then map it to the portal base URL:

| MCP Server | Portal Base URL |
|------------|----------------|
| `api.kobiton.com` | `https://portal.kobiton.com` |
| `api-test-green.kobiton.com` | `https://portal-test.kobiton.com` |

**Build the launch URL:**

```
<portal-base-url>/devices/launch?id=<deviceId>
```

Where `<deviceId>` is the ID of the selected device from Step 2 (returned by `listDevices`, `getDeviceStatus`, or `reserveDevice`).

**Open the link** in the user's default browser:

| Platform | Command |
|----------|---------|
| macOS | `open <url>` |
| Linux | `xdg-open <url>` |

### 5. Collect results

After opening the browser, call `listSessions` with `deviceId=<deviceId>` (from Step 2) and `state='START'` to find the session that just triggered. Use the most recent session (first result) as the match.

Call `getSession` with the matched session ID to get detailed results.

Call `getSessionArtifacts` with the session ID to retrieve:

- Video recording URL
- Device logs URL
- Screenshots
- Test reports

### Error handling

- `listDevices` returns empty: suggest broadening filters (remove platform/group constraints) or trying again later when devices free up.
- Upload fails or times out: retry the upload. Pre-signed URLs expire after 30 minutes — if expired, call the upload tool again to get a fresh URL.
- Session stuck in a non-terminal state: poll `getSession` with a reasonable timeout. If still running, offer to call `terminateSession` and retry.
- `reserveDevice` fails (device already taken): call `listDevices` again to find another available device.
- Script execution fails: check error output for missing dependencies (e.g. `wd`, `appium`), incorrect UDID, or network issues. Suggest fixes.

### 6. Summarize

Present a summary to the user:

- Pass/fail status
- Session link in Kobiton portal
- Video recording link
- Key error messages (if failed)
- Execution duration
