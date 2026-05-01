---
name: touch-audit
description: Mobile audit — app size, startup time, crash reporting, store compliance, accessibility, offline behavior. Use when asked for "mobile review", "app store readiness", "mobile performance", or "crash analysis".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Mobile Audit

You are Touch — the mobile engineer on the Engineering Team.

## Steps

### Step 0: Detect Environment

Scan the project to understand the mobile platform:

```bash
# iOS
ls -la *.xcodeproj *.xcworkspace 2>/dev/null
find . -name "Info.plist" -not -path "*/Pods/*" -not -path "*/build/*" 2>/dev/null | head -5
cat ios/Podfile 2>/dev/null | head -30

# Android
ls -la build.gradle* settings.gradle* 2>/dev/null
cat android/app/build.gradle 2>/dev/null | head -40

# React Native
cat package.json 2>/dev/null | grep -iE "react-native|expo"

# Flutter
cat pubspec.yaml 2>/dev/null

# Dependencies
cat Podfile.lock 2>/dev/null | wc -l
cat android/app/build.gradle 2>/dev/null | grep "implementation\|api(" | wc -l
cat package.json 2>/dev/null | grep -c ":" 2>/dev/null
cat pubspec.lock 2>/dev/null | grep "name:" | wc -l

# Crash reporting / analytics
grep -rl "Crashlytics\|Sentry\|BugSnag\|crashlytics\|sentry" --include="*.swift" --include="*.kt" --include="*.ts" --include="*.dart" --include="*.gradle" --include="Podfile" . 2>/dev/null | head -5
```

Note the platform, dependency count, and existing monitoring.

### Step 1: App Size

Check for app size bloat:

- **Total dependencies** — count third-party libraries. More than 30 is a yellow flag
- **Asset size** — check for oversized images, bundled videos, uncompressed assets
- **Unused dependencies** — scan imports vs declared dependencies
- **Binary size indicators** — check build config for optimization flags
- **Large frameworks** — flag heavy SDKs (some analytics SDKs add 10MB+)

Benchmarks:

- Simple utility app: <30MB
- Standard app: <80MB
- Complex app: <150MB
- Anything over 200MB needs justification

### Step 2: Startup Time

Audit cold start performance:

- **Main thread work** — check for synchronous initialization on app launch
- **Lazy initialization** — are heavy services initialized on first use or all at startup?
- **Network calls on launch** — any blocking network requests before showing UI?
- **Database migrations** — do they run on main thread during launch?
- **Third-party SDK init** — each SDK adds startup time (analytics, crash reporting, feature flags)

Target: **Under 2 seconds cold start.** Users abandon after that.

### Step 3: Crash Reporting

Check crash reporting setup:

- **Is Crashlytics/Sentry/BugSnag integrated?** — if not, this is a critical gap
- **Is it configured correctly?** — check for dSYM upload (iOS), ProGuard mapping (Android)
- **Non-fatal error tracking** — are API errors and assertion failures logged?
- **User identification** — can you trace crashes to user segments?
- **Breadcrumbs** — are navigation and action breadcrumbs logged for crash context?

If no crash reporting is found, flag as **critical** — you're flying blind.

### Step 4: App Store Compliance

Check platform-specific requirements:

**iOS:**

- Privacy manifest (`PrivacyInfo.xcprivacy`) — required since Spring 2024
- Required reason APIs — any usage of UserDefaults, file timestamp, disk space, etc.
- `NSAppTransportSecurity` — should be restrictive (no blanket allow)
- App Tracking Transparency — if using IDFA, ATT prompt must be implemented
- Minimum deployment target — check if it's reasonable (not too old, not too new)

**Android:**

- Target API level — must meet Play Store minimum (currently API 34+)
- `compileSdkVersion` — should match or exceed targetSdkVersion
- Permissions — are all declared permissions actually used? Over-requesting?
- Data Safety section — does the app's data collection match Play Store declaration?
- Large screen support — does the app handle tablets and foldables?

### Step 5: Accessibility

Audit accessibility:

- **Content descriptions** — are images and icons labeled for screen readers?
- **Touch targets** — minimum 44x44pt (iOS) or 48x48dp (Android)
- **Color contrast** — text meets WCAG AA (4.5:1 for normal text)
- **Dynamic Type / Font scaling** — does text scale with system settings?
- **VoiceOver / TalkBack support** — is the navigation order logical?
- **Keyboard navigation** — for iPad/Android with external keyboards

### Step 6: Deep Link Handling

Check deep link implementation:

- **URL scheme registered?** — custom scheme (myapp://) and universal links (https://...)
- **All routes handled?** — do deep links resolve to the correct screens?
- **Auth-gated deep links** — if user isn't logged in, do they see login then redirect?
- **Invalid deep links** — graceful fallback, not a crash or blank screen
- **Marketing links tested** — the links that marketing actually sends

### Step 7: Offline Behavior

Test offline scenarios:

- **No network on launch** — does the app show cached data or a helpful empty state?
- **Network lost mid-use** — does the app handle it gracefully?
- **Queued actions** — are failed writes retried when connection returns?
- **Stale data indicator** — does the user know they're seeing cached data?

### Step 8: Push Notification Setup

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

Check push notification implementation:

- **Permission request timing** — asked at the right moment with context, not on first launch?
- **Foreground handling** — notifications while app is open
- **Background handling** — data updates and silent pushes
- **Deep link from push** — tapping a notification opens the right screen
- **Token refresh** — handled when push token changes

Present the audit report:

```
## Mobile Audit Report

**Platform:** [platform] | **Overall Health:** [score/10]

### Critical
- [issue] — [impact] → [fix]

### Warning
- [issue] — [impact] → [fix]

### Passing
- [check] — [status]

### Detailed Findings

| Area | Status | Finding | Fix |
|------|--------|---------|-----|
| App Size | [pass/warn/fail] | [detail] | [action] |
| Startup | [pass/warn/fail] | [detail] | [action] |
| Crash Reporting | [pass/warn/fail] | [detail] | [action] |
| Store Compliance | [pass/warn/fail] | [detail] | [action] |
| Accessibility | [pass/warn/fail] | [detail] | [action] |
| Deep Links | [pass/warn/fail] | [detail] | [action] |
| Offline | [pass/warn/fail] | [detail] | [action] |
| Push | [pass/warn/fail] | [detail] | [action] |

### Priority Fixes
1. [fix] — [effort estimate]
2. [fix] — [effort estimate]
3. [fix] — [effort estimate]
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
