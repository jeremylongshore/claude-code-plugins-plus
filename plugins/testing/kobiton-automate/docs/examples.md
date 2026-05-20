# Kobiton MCP Tools — Examples

A guide to every tool available in the Kobiton MCP server, organized by domain. Each tool includes a description and natural-language prompt examples you can use directly in Claude Code.

---

## Table of Contents

| # | Domain | Tools |
|---|--------|-------|
| 1 | [Device Management](#1-device-management) | `listDevices`, `getDeviceStatus`, `reserveDevice`, `terminateReservation` |
| 2 | [Session Management](#2-session-management) | `listSessions`, `getSession`, `getSessionArtifacts`, `terminateSession` |
| 3 | [App Management](#3-app-management) | `listApps`, `getApp`, `uploadAppToStore`, `confirmAppUpload` |
| 4 | [Running Automation Tests](#4-running-automation-tests) | `run-automation-suite` skill |

---

## 1. Device Management

### `listDevices`

List available devices filtered by platform, availability, device group, name, or UDID. Returns device name, UDID, platform, OS version, and availability.

**Prompt examples:**

> "Show me all available Android devices"

> "List available iPhones in the cloud device group"

> "Find any Pixel devices in my private group"

> "Check if the device with UDID R58M20D1ELE is available"

---

### `getDeviceStatus`

Get real-time status of a specific device including availability, current session info, battery level, and connection state.

**Prompt examples:**

> "What is the status of device 1234?"

> "Is device 5678 currently in use?"

---

### `reserveDevice`

Reserve a device for exclusive use during testing. Prevents other users from starting sessions on the device. Use the UDID from `listDevices`.

**Prompt examples:**

> "Reserve the Galaxy S20 with UDID R58M20D1ELE for 60 minutes"

> "Lock device 19031FDF6003LP for me for 30 minutes"

---

### `terminateReservation`

Release a reserved device by terminating its reservation.

**Prompt examples:**

> "Release reservation 4521"

> "I'm done with my reserved device, terminate reservation 4521"

---

## 2. Session Management

### `listSessions`

List test sessions with filters. Returns session ID, status, device info, duration, and timestamps.

**Prompt examples:**

> "Show me all running sessions"

> "List my last 5 failed iOS sessions"

> "Show sessions running on Pixel devices"

---

### `getSession`

Get detailed info about a specific session including commands executed, device info, desired capabilities, and test results.

**Prompt examples:**

> "Get details for session 12345"

> "What device and capabilities were used in session 502?"

---

### `getSessionArtifacts`

Get download URLs for session artifacts: video recording, device logs, screenshots, and test reports.

**Prompt examples:**

> "Download the video and logs from session 12345"

> "Get the test report artifacts for session 502"

---

### `terminateSession`

Stop a running test session before it completes naturally.

**Prompt examples:**

> "Stop session 12345, it's been running too long"

> "Terminate my running session 6789"

---

## 3. App Management

### `listApps`

List uploaded app builds for the current organization. Returns app ID, name, version, platform, upload date, and status.

**Prompt examples:**

> "Show me all uploaded Android apps"

> "List my iOS apps in the Kobiton store"

---

### `getApp`

Get detailed info about an app including name, platform, state, and optionally all version history.

**Prompt examples:**

> "Get details for app 42"

> "Show me all versions of app 42"

---

### `uploadAppToStore`

Upload an app to Kobiton Store for permanent storage. The app appears in the portal's app repository. **Two-step process**: this tool returns a pre-signed URL, then the file must be uploaded to that URL.

**Prompt examples:**

> "Upload resources/apps/GS.apk to the Kobiton app store as an Android app"

> "Upload resources/apps/LeaderboardApp.ipa to the store for iOS"

---

### `confirmAppUpload`

Confirm a previously uploaded app so it appears in the Kobiton portal's app repository with a tracking record.

**Prompt examples:**

> "Confirm the upload for app 42"

> "Finish the upload process for the app I just uploaded"

---

## 4. Running Automation Tests

### `run-automation-suite` skill

Guided workflow that uploads your app, selects a device, parses capabilities from your local Appium script, and executes it. Supports Node.js, Python, .NET, and Java scripts.

**Pattern:**

```
Test this app <PATH_TO_APP> by my script <PATH_TO_SCRIPT> on Kobiton <PLATFORM> device <DEVICE_NAME>
```

**Prompt examples:**

> "Test this app resources/apps/GS.apk by my script resources/auto/Android_app_test.js on Kobiton Android device"

> "Test this app resources/apps/LeaderboardApp.ipa by my script tests/ios_test.py on Kobiton iOS device iPhone 15"

> "Test this app resources/apps/TurboTest.apk by my script tests/smoke_test.js on Kobiton Android device Pixel 6"


