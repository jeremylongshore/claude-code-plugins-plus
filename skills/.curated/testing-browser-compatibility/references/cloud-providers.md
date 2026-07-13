# Cloud Testing Providers Reference

Comprehensive reference for BrowserStack, Sauce Labs, LambdaTest, and Kobiton -- authentication, API endpoints, capabilities format, and session management.

---

## BrowserStack

**Strength:** Broadest browser/OS matrix -- 3,000+ real device and browser combinations.

### Authentication

```bash
export BROWSERSTACK_USERNAME="your_username"
export BROWSERSTACK_ACCESS_KEY="your_access_key"
```

HTTP Basic Auth: `Authorization: Basic base64(username:access_key)`

### API Base URL

`https://api.browserstack.com`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/automate/browsers.json` | GET | List available browsers |
| `/automate/sessions/{id}.json` | GET | Session details |
| `/automate/sessions/{id}.json` | PUT | Update session (name, status) |
| `/automate/builds.json` | GET | List builds |
| `/app-automate/recent_apps` | GET | List uploaded apps |

### WebDriver Capabilities

```json
{
  "bstack:options": {
    "os": "Windows",
    "osVersion": "11",
    "browserVersion": "latest",
    "projectName": "Cross-Browser Tests",
    "buildName": "build-1.0",
    "sessionName": "Homepage Layout",
    "local": false,
    "seleniumVersion": "4.0.0"
  },
  "browserName": "Chrome"
}
```

### Mobile Capabilities

```json
{
  "bstack:options": {
    "deviceName": "iPhone 15",
    "osVersion": "17",
    "realMobile": true,
    "projectName": "Mobile Compat",
    "buildName": "mobile-build-1"
  },
  "browserName": "Safari"
}
```

### Local Tunnel (for staging/localhost)

```bash
# Download and run BrowserStackLocal binary
./BrowserStackLocal --key $BROWSERSTACK_ACCESS_KEY
```

Then set `"local": true` in `bstack:options`.

### Artifacts

- Screenshots: `GET /automate/sessions/{id}/logs` (screenshot logs)
- Video: Available on session detail page -- enabled by default
- Logs: Console, network, Selenium logs via session endpoint
- Network HAR: Enable with `"browserstack.networkLogs": true`

### Pricing Model

Per-parallel-test pricing. Free tier: 100 minutes/month. Plans start at 1 parallel test. Real device plans billed separately from desktop browser plans.

---

## Sauce Labs

**Strength:** Deep CI/CD integrations, Sauce Connect tunnel for secure staging access, detailed analytics.

### Authentication

```bash
export SAUCE_USERNAME="your_username"
export SAUCE_ACCESS_KEY="your_access_key"
```

HTTP Basic Auth: `Authorization: Basic base64(username:access_key)`

### API Base URL

- US West: `https://api.us-west-1.saucelabs.com`
- EU Central: `https://api.eu-central-1.saucelabs.com`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rest/v1/{username}/tunnels` | GET | List active tunnels |
| `/rest/v1/{username}/jobs/{id}` | GET | Job/session details |
| `/rest/v1/{username}/jobs/{id}` | PUT | Update job metadata |
| `/rest/v1/{username}/jobs/{id}/assets/{filename}` | GET | Download artifacts |
| `/v2/builds` | GET | List builds |

### WebDriver Capabilities

```json
{
  "sauce:options": {
    "username": "env:SAUCE_USERNAME",
    "accessKey": "env:SAUCE_ACCESS_KEY",
    "build": "build-1.0",
    "name": "Homepage Layout Test",
    "screenResolution": "1920x1080",
    "seleniumVersion": "4.0.0"
  },
  "browserName": "chrome",
  "browserVersion": "latest",
  "platformName": "Windows 11"
}
```

### Mobile Capabilities (Real Devices)

```json
{
  "sauce:options": {
    "appiumVersion": "2.0.0",
    "deviceName": "iPhone_15_Pro_Max_real",
    "platformVersion": "17",
    "build": "mobile-build-1"
  },
  "platformName": "iOS",
  "browserName": "Safari"
}
```

### Sauce Connect (Secure Tunnel)

```bash
# Download sc binary for your OS
sc -u $SAUCE_USERNAME -k $SAUCE_ACCESS_KEY --tunnel-name my-tunnel
```

Then set `"tunnelName": "my-tunnel"` in `sauce:options`.

### Artifacts

- Screenshots: `GET /rest/v1/{username}/jobs/{id}/assets/screenshot.png`
- Video: `GET /rest/v1/{username}/jobs/{id}/assets/video.mp4`
- Logs: `GET /rest/v1/{username}/jobs/{id}/assets/log.json`
- HAR: `GET /rest/v1/{username}/jobs/{id}/assets/network.har`

### Pricing Model

Per-concurrent-session pricing. Free tier available for open-source. Plans include virtual cloud (desktop browsers) and real device cloud (billed together or separately).

---

## LambdaTest

**Strength:** Smart testing with auto-healing selectors, geolocation testing, fast parallel execution.

### Authentication

```bash
export LT_USERNAME="your_username"
export LT_ACCESS_KEY="your_access_key"
```

HTTP Basic Auth: `Authorization: Basic base64(username:access_key)`

### API Base URL

`https://api.lambdatest.com`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/automation/api/v1/platforms` | GET | Available OS/browser combos |
| `/automation/api/v1/sessions/{id}` | GET | Session details |
| `/automation/api/v1/sessions/{id}` | PATCH | Update session |
| `/automation/api/v1/builds` | GET | List builds |
| `/automation/api/v1/sessions/{id}/log/command` | GET | Command logs |

### WebDriver Capabilities

```json
{
  "LT:Options": {
    "username": "env:LT_USERNAME",
    "accessKey": "env:LT_ACCESS_KEY",
    "build": "build-1.0",
    "name": "Homepage Layout Test",
    "resolution": "1920x1080",
    "selenium_version": "4.0.0",
    "w3c": true,
    "smartUI.project": "cross-browser-tests"
  },
  "browserName": "Chrome",
  "browserVersion": "latest",
  "platformName": "Windows 11"
}
```

### Mobile Capabilities

```json
{
  "LT:Options": {
    "deviceName": "iPhone 15",
    "platformVersion": "17",
    "isRealMobile": true,
    "build": "mobile-build-1"
  },
  "platformName": "iOS",
  "browserName": "Safari"
}
```

### LambdaTest Tunnel

```bash
# Download LT binary
./LT --user $LT_USERNAME --key $LT_ACCESS_KEY --tunnelName my-tunnel
```

Then set `"tunnel": true, "tunnelName": "my-tunnel"` in `LT:Options`.

### Artifacts

- Screenshots: Available via session dashboard and API
- Video: Enabled by default, downloadable via session API
- Logs: Network, console, command logs via session endpoint
- SmartUI: Visual regression screenshots with AI-powered comparison

### Pricing Model

Per-parallel-test pricing. Free tier: 60 minutes/month. Plans scale by parallel sessions. Real device and desktop browser testing in unified plans.

---

## Kobiton

**Strength:** Real physical devices (not emulators), scriptless automation, AI-driven test generation, device lab management.

### Authentication

```bash
export KOBITON_USERNAME="your_username"
export KOBITON_API_KEY="your_api_key"
```

HTTP Basic Auth: `Authorization: Basic base64(username:api_key)`

### API Base URL

`https://api.kobiton.com`

API documentation: `https://api.kobiton.com/docs/`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/devices` | GET | List available real devices (filter by `isOnline`, `platformName`) |
| `/v1/sessions` | GET | List test sessions |
| `/v1/sessions/{id}` | GET | Session details (status, device, duration) |
| `/v1/sessions` | POST | Create manual session on a specific device |
| `/v1/sessions/{id}/terminate` | POST | End a running session |
| `/v1/apps` | GET | List uploaded apps |
| `/v1/apps/upload` | POST | Upload app for testing |
| `/v1/scriptless/executions` | GET | List scriptless automation runs |

### Device Query Example

```bash
# List all online iOS devices
curl -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
  "https://api.kobiton.com/v1/devices?isOnline=true&platformName=iOS"

# Response (truncated):
# {
#   "devices": [
#     {
#       "id": 12345,
#       "deviceName": "iPhone 15 Pro",
#       "platformName": "iOS",
#       "platformVersion": "17.4",
#       "isOnline": true,
#       "udid": "abc123..."
#     }
#   ]
# }
```

### Appium Capabilities (Scripted Testing)

```json
{
  "platformName": "iOS",
  "appium:deviceName": "iPhone 15 Pro",
  "appium:platformVersion": "17",
  "appium:automationName": "XCUITest",
  "browserName": "Safari",
  "kobiton:options": {
    "username": "env:KOBITON_USERNAME",
    "apiKey": "env:KOBITON_API_KEY",
    "sessionName": "Safari Compat Test",
    "sessionDescription": "Cross-browser layout validation",
    "deviceGroup": "KOBITON",
    "captureScreenshots": true,
    "ensureWebviewsHavePages": true
  }
}
```

### Android Capabilities

```json
{
  "platformName": "Android",
  "appium:deviceName": "Galaxy S24",
  "appium:platformVersion": "14",
  "appium:automationName": "UiAutomator2",
  "browserName": "chrome",
  "kobiton:options": {
    "username": "env:KOBITON_USERNAME",
    "apiKey": "env:KOBITON_API_KEY",
    "sessionName": "Chrome Android Compat",
    "deviceGroup": "KOBITON",
    "captureScreenshots": true
  }
}
```

### Scriptless Automation

Kobiton offers scriptless test automation -- record a manual session, then Kobiton replays it across multiple real devices using AI to adapt to UI differences.

```bash
# Trigger scriptless execution from a baseline session
curl -X POST -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
  "https://api.kobiton.com/v1/scriptless/executions" \
  -H "Content-Type: application/json" \
  -d '{
    "baselineSessionId": 98765,
    "deviceBundleId": 111,
    "name": "Cross-device replay"
  }'
```

### Session Management

```bash
# Get session details with video and log URLs
curl -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
  "https://api.kobiton.com/v1/sessions/12345"

# Response includes:
# - state: "COMPLETE" | "RUNNING" | "FAILED"
# - video.url: direct link to session recording
# - log.url: device/Appium log download
# - executionData.screenshots[]: per-step screenshots
```

### Artifacts

- Screenshots: Per-step screenshots captured automatically when `captureScreenshots: true`
- Video: Full session recording available via session detail endpoint
- Logs: Appium server logs, device logs (logcat/syslog), network logs
- Scriptless reports: Side-by-side comparison across devices with pass/fail per step

### Pricing Model

Device minutes pricing. Plans include access to Kobiton's shared real device cloud. Private/dedicated device lab options available for enterprise. Scriptless automation included in higher-tier plans.

---

## Provider Comparison Summary

| Feature | BrowserStack | Sauce Labs | LambdaTest | Kobiton |
|---------|-------------|------------|------------|---------|
| Desktop browsers | 3,000+ combos | 1,000+ combos | 3,000+ combos | Limited (mobile focus) |
| Real mobile devices | Yes | Yes | Yes | Yes (primary strength) |
| Secure tunnel | BrowserStackLocal | Sauce Connect | LT Tunnel | VPN access |
| Scriptless automation | No | No | SmartUI visual | Yes (AI replay) |
| Appium support | Yes | Yes | Yes | Yes |
| Selenium support | Yes | Yes | Yes | Via Appium |
| Video recording | Default on | Default on | Default on | Default on |
| Network HAR logs | Yes | Yes | Yes | Yes |
| Free tier | 100 min/mo | OSS only | 60 min/mo | Trial available |
| Best for | Broadest matrix | Enterprise CI/CD | Scaling teams | Mobile-first testing |
