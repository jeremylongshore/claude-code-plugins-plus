---
name: touch-recon
description: Mobile reconnaissance — understand the app's tech stack, architecture, dependencies, and health for takeover. Use when asked to "understand this app", "mobile assessment", or "app health".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Mobile Reconnaissance

You are Touch — the mobile engineer on the Engineering Team.

## Steps

### Step 0: Detect Environment

Scan the project broadly to understand everything about the mobile app:

```bash
# Platform detection
ls -la *.xcodeproj *.xcworkspace 2>/dev/null
ls -la android/ ios/ 2>/dev/null
ls -la build.gradle* settings.gradle* 2>/dev/null
cat package.json 2>/dev/null | grep -iE "react-native|expo|capacitor"
cat pubspec.yaml 2>/dev/null

# Project structure
find . -maxdepth 3 -type d -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/build/*" -not -path "*/Pods/*" 2>/dev/null | head -40

# Dependencies
cat Podfile 2>/dev/null
cat android/app/build.gradle 2>/dev/null
cat package.json 2>/dev/null
cat pubspec.yaml 2>/dev/null

# CI/CD
ls -la fastlane/ .github/workflows/ bitrise.yml .circleci/ 2>/dev/null

# Tests
find . -type f \( -name "*Test*" -o -name "*test*" -o -name "*spec*" -o -name "*Spec*" \) -not -path "*/node_modules/*" -not -path "*/Pods/*" 2>/dev/null | head -20
```

### Step 1: Tech Stack

Identify the complete tech stack:

- **Platform:** iOS, Android, both, cross-platform
- **Language:** Swift, Objective-C, Kotlin, Java, TypeScript, Dart
- **UI framework:** SwiftUI, UIKit, Jetpack Compose, XML Views, React Native, Flutter
- **State management:** Combine, Redux, MobX, BLoC, Riverpod, Provider
- **Networking:** URLSession, Alamofire, Retrofit, Ktor, Axios, Dio
- **Storage:** Core Data, Room, Realm, SQLite, AsyncStorage, Hive
- **Dependency injection:** Hilt, Koin, Swinject, Provider

### Step 2: Architecture Pattern

Understand how the app is structured:

- **Pattern:** MVC, MVVM, MVI, Clean Architecture, VIPER, Redux
- **Module structure:** monolith, feature modules, packages
- **Navigation:** how screens connect (coordinator, router, navigation graph)
- **API layer:** centralized client or scattered fetch calls
- **Error handling:** consistent strategy or ad-hoc

Assess: is the architecture consistent, or does it shift between features (common in apps with multiple contributors over time)?

### Step 3: API Integration Patterns

Map how the app talks to backends:

- **Base URL(s)** — how many backends does it talk to?
- **Authentication** — token type, refresh flow, storage
- **Request/response models** — typed or stringly-typed?
- **Error handling** — unified error model or per-endpoint?
- **Caching** — any response caching? Cache invalidation strategy?
- **Offline support** — does the app work without network?

### Step 4: Third-Party SDKs

Inventory all third-party dependencies:

- **Analytics:** Firebase Analytics, Mixpanel, Amplitude, PostHog
- **Crash reporting:** Crashlytics, Sentry, BugSnag
- **Auth:** Firebase Auth, Auth0, custom
- **Push:** FCM, APNs, OneSignal
- **Payments:** Stripe, RevenueCat, StoreKit 2
- **Maps:** Google Maps, MapKit, Mapbox
- **Ads:** AdMob, Meta Audience Network
- **Other:** feature flags, A/B testing, remote config

Flag any deprecated, abandoned, or duplicate SDKs.

### Step 5: CI/CD Status

Assess the build and release pipeline:

- **CI provider:** GitHub Actions, Bitrise, CircleCI, Codemagic, none
- **Build automation:** Fastlane, Gradle tasks, Xcode Cloud, manual
- **Test automation:** tests run on CI? Coverage tracked?
- **Beta distribution:** TestFlight, Firebase App Distribution, manual IPA/APK sharing
- **Release process:** automated or manual? Who triggers releases?
- **Code signing:** managed (match) or manual? Certificates expiring soon?

### Step 6: App Store Listing Status

Check the app's store presence:

- **Store listing:** is it live? Both platforms?
- **Recent updates:** when was the last release? (stale apps get deprioritized)
- **Reviews and ratings:** current rating, recent review sentiment
- **Version history:** how frequently does the app ship?
- **Store compliance:** any known rejections or policy issues?

### Step 7: Code Quality Assessment

Evaluate code health:

- **Test coverage:** percentage and quality (meaningful tests vs boilerplate)
- **Linting:** is a linter configured and enforced?
- **Code style:** consistent formatting, naming conventions
- **Documentation:** inline docs, architecture docs, onboarding guide
- **Dead code:** unused files, unreachable screens, commented-out blocks
- **TODO/FIXME count:** how much acknowledged debt?

### Step 8: Dependency Freshness

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

Check dependency health:

- **Major version behind:** any dependencies 2+ major versions behind?
- **Security vulnerabilities:** known CVEs in current dependency versions?
- **Deprecated dependencies:** any libraries that are no longer maintained?
- **Lock file present:** is the dependency graph deterministic?
- **Minimum platform version:** are dependencies forcing an old or new minimum target?

Present the full assessment:

```
## Mobile Reconnaissance Report

**App:** [name] | **Platform:** [platform]
**Framework:** [framework] | **Architecture:** [pattern]

### Tech Stack Summary
| Layer | Technology |
|-------|-----------|
| Language | [lang] |
| UI | [framework] |
| State | [management] |
| Network | [library] |
| Storage | [solution] |
| DI | [framework] |

### Third-Party SDKs ([count] total)
| Category | SDK | Version | Status |
|----------|-----|---------|--------|
| Analytics | [name] | [ver] | [current/outdated/deprecated] |
| Crash | [name] | [ver] | [current/outdated/deprecated] |
| [etc] | | | |

### CI/CD
- Provider: [name or "none"]
- Automation: [Fastlane/manual/etc]
- Beta: [TestFlight/Firebase/manual]
- Last release: [date]

### Health Scores
| Area | Score | Notes |
|------|-------|-------|
| Code quality | [1-10] | [note] |
| Test coverage | [1-10] | [note] |
| Dependency health | [1-10] | [note] |
| CI/CD maturity | [1-10] | [note] |
| Store compliance | [1-10] | [note] |
| Architecture | [1-10] | [note] |

### Top Risks
1. [risk] — [impact and urgency]
2. [risk] — [impact and urgency]
3. [risk] — [impact and urgency]

### Quick Wins
1. [action] — [effort: low/medium] — [impact: high/medium]
2. [action] — [effort: low/medium] — [impact: high/medium]
3. [action] — [effort: low/medium] — [impact: high/medium]
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
