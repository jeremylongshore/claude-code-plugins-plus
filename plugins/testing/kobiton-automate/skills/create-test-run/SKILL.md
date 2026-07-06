---
name: create-test-run
description: >-
  Create a Kobiton test run from a test case or suite, then offer to monitor it.
  When the user gives only partial details (or just a test case id), fill the
  rest with sensible defaults that match the createTestRun schema, show a summary
  of what will run, and ask to proceed or customize before creating. After the
  run is created, offer monitoring in a single prompt — monitor + auto-open live
  remediation (only when the org's live-remediation flag is ON), monitor only,
  or don't monitor — and hand off to the monitor-test-run skill if chosen. Use
  when the user asks to "create / kick off / start / run a test run", "run test
  case X on N devices", or similar. Wraps the createTestRun MCP tool (and
  getOrgSettings / listDevices for defaults); delegates the watch to
  monitor-test-run.
allowed-tools: >-
  Read, Skill
version: 1.0.0
author: Kobiton Inc.
license: MIT
compatibility: >-
  Uses the Kobiton MCP tools createTestRun, getTestCase/getTestSuite,
  listDevices, and getOrgSettings; requires an authenticated Kobiton MCP
  connection. Delegates monitoring to the monitor-test-run skill (same plugin).
tags: [testing, test-run, create, monitoring, live-remediation, kobiton]
---

## Overview

Turn a "run this" request into a created test run with as little friction as the
user wants, then offer to watch it. Two phases:

1. **Build + confirm the run.** Resolve what to run (test case or suite), on which
   devices, with what app — filling any unspecified field with a documented
   default — then show a one-screen summary and create on confirmation.
2. **Offer monitoring once.** After creation, present the monitor choice in a
   single prompt and delegate to `monitor-test-run` if the user wants it.

> **Tool naming.** Kobiton MCP tools are referenced by bare name (`createTestRun`,
> `getOrgSettings`, `listDevices`, `getTestCase`, `getTestSuite`). The host
> resolves the prefix (`mcp__plugin_automate_kobiton__createTestRun`,
> `mcp__kobiton__createTestRun`, etc.).

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| test case id **or** test suite id | one of | A test case id → `TEST_CASE` selection; a suite id → `TEST_SUITE`. If the user named neither, ask for it (it's the one thing with no sensible default). |
| device count / specific devices | no | Default: 1 device matching the test case/suite platform. The user may say "3 devices", name models, or give UDIDs. |
| run name / app version / allocation | no | All defaulted (see Step 2). |

## Steps

### 1. Resolve the target and its platform

- A **test case id** → fetch it (`getTestCase`) to learn its platform and the app under test. Selection
  will be `TEST_CASE` with `testCaseSelections: [{ testCaseId, version }]` (default to the latest version
  if the user didn't pin one).
- A **test suite id** → fetch it (`getTestSuite`) for platform + member test cases. Selection will be
  `TEST_SUITE` with `testSuiteId`.
- If the user gave neither a case nor a suite id, ask for one — there's no sensible default for *what* to
  run. Everything else can be defaulted.

### 2. Fill defaults for anything unspecified

Apply these defaults so a bare request ("run test case X") becomes a complete, valid `createTestRun`
payload. **Use the exact enum values below — they are upper-case and case-sensitive; the API rejects
lower-case variants (`test_case`, `specific_devices`, …).**

| Field | Default | Notes |
|-------|---------|-------|
| `testSelection.type` | `TEST_CASE` (case) / `TEST_SUITE` (suite) | per Step 1 |
| test case version | latest version of the case | from `getTestCase` |
| `deviceSelection.type` | `INDIVIDUAL_DEVICES` | prefer explicit devices over a bundle (avoids stale-bundle surprises) |
| devices | **1** available device matching the target's platform | call `listDevices(platform=<platform>, available=true)` and pick online, unbooked, non-cloud devices; if the user asked for N, pick N distinct ones. Pass each as `{ udid, isCloud }`. |
| `appSelections` | the test case's app under test, latest version | derive `appPackage` + `appVersionId` from `getTestCase` (the case records its app); omit only if the target carries no app. |
| `deviceAllocationStrategy` | `CROSS_DEVICE` | "All Permutations" — run each test case on each device (see label map below) |
| `name` | `"<test case/suite name> — <N> device(s) — <YYYY-MM-DD HH:mm>"` | human-readable; the user can override |
| `description` | omit | optional |

Enum reference (exact API values — upper-case, case-sensitive):
- `testSelection.type`: `TEST_CASE` | `TEST_SUITE`
- `deviceSelection.type`: `INDIVIDUAL_DEVICES` | `DEVICE_BUNDLE`
- `deviceAllocationStrategy`: `CROSS_DEVICE` | `SINGLE_DEVICE`

**Allocation-strategy labels (show the human label to the user, send the enum to the API).** Mirror the
Portal's "Device Allocation Strategy" dropdown wording:

| API enum | Show to the user |
|----------|------------------|
| `CROSS_DEVICE` | **All Permutations** — run each test case on each device |
| `SINGLE_DEVICE` | **Random Allocation** — run each test case once, randomly chosen from the selected devices |

Never surface the bare enum (`CROSS_DEVICE`) in the summary or prompts — it's meaningless to the user.

### 3. Show the summary and confirm (skip the prompt only if the user already gave full, explicit details)

Post a compact summary of exactly what will be created, e.g.:

```
About to create this test run:
  Test case : API Demos  (id 019ef40b…, version 2, Android)
  Devices   : 3 × Android (Pixel 8 · Galaxy S24 Ultra · Pixel 4)
  App       : io.appium.android.apis  (version 73202)
  Allocation: All Permutations — run each test case on each device
  Name      : "API Demos — 3 devices — 2026-06-24 11:20"
```

(Allocation shows the human label, not the `CROSS_DEVICE` enum.)

Then ask to **proceed or customize** in one prompt — offer "Proceed", "Change devices", "Change
allocation", "Change name", and let the user free-type any other tweak. When the user wants to change
allocation, present the two human-labeled choices (All Permutations / Random Allocation) and map their
pick back to the enum. Re-summarize and re-ask only if they change something. If the user's original
request was already fully explicit (every field named), you may create directly and just state what you
created.

### 4. Create the run

Call `createTestRun` with the assembled payload (camelCase keys as in the tool schema; the exact enum
values from Step 2). On success it returns the test run id + queued sessions. Report the id and a
one-line confirmation.

If `createTestRun` returns a validation error, fix it from the error text and the Step-2 enum reference
rather than guessing — do not retry the same body.

### 5. Offer monitoring — one prompt, then delegate

Read the live-remediation flag first: call `getOrgSettings` once and note `live_remediation_enabled`
(`flagOn`). This decides whether the auto-open option is meaningful.

Then offer monitoring in a **single** message (don't fire multiple separate questions — that's the
annoying part). Present the choices inline and let the user pick one:

- **Monitor + auto-open live remediation** — *only list this option when `flagOn = true`.* Watches the
  run and, when an execution blocks, automatically opens the live-remediation window for the device.
- **Monitor only** — watches the run and surfaces blockers / the final summary, but doesn't auto-open
  windows (you print the URL instead).
- **Don't monitor** — stop here; give the user the test run id (and the portal link if handy) so they can
  watch it themselves later.

Phrase it as one prompt, e.g. (flag ON):

> Run created (`<testRunId>`). Want me to monitor it? **(a)** monitor + auto-open the live-remediation
> window when a blocker hits, **(b)** monitor only (I'll surface blockers + the URL), or **(c)** don't
> monitor. Reply a / b / c.

(flag OFF — drop option **a**, since there's no live window to open):

> Run created (`<testRunId>`). Want me to monitor it? **(b)** monitor only (I'll surface blockers + the
> portal URL), or **(c)** don't monitor. Reply b / c.

On the user's answer:

- **(a) or (b)** → invoke the **`monitor-test-run`** skill for `<testRunId>`. Pass along the auto-open
  intent: for **(a)**, the user has already opted into auto-open, so tell monitor-test-run to skip its own
  up-front auto-open question and treat `autoOpen = yes`; for **(b)**, `autoOpen = no`. monitor-test-run
  owns the watch loop (the bundled poller, blocker surfacing, post-mortem) from here.
- **(c)** → done. Report the test run id and how to watch later (`monitor-test-run <testRunId>`), then
  stop.

## Errors

| Condition | Handling |
|-----------|----------|
| No test case/suite id given | Ask for one — it's the only field with no default. |
| `createTestRun` validation error (bad enum, missing pair) | Correct from the error + the Step-2 enum reference; don't blind-retry. |
| No available devices for the platform | Tell the user; offer to widen (cloud devices) or wait. Don't create a run that can't dispatch. |
| `getOrgSettings` fails before the monitor offer | Assume `flagOn = false` (drop the auto-open option); still offer monitor-only / don't-monitor. |

## Notes

- This skill **creates** the run and **hands off** the watch; it does not implement monitoring itself —
  that's `monitor-test-run` (same plugin), which runs the bundled emit-on-change poller.
- Default to the smallest run that satisfies the request (1 device unless asked for more) — creating real
  device sessions consumes minutes/concurrency.
- Prefer `INDIVIDUAL_DEVICES` with explicit `{ udid, isCloud }` over a device bundle, so the exact devices
  are known and a stale/oversized bundle can't surprise the run.
