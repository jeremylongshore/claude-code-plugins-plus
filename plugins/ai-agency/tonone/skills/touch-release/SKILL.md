---
name: touch-release
description: Set up mobile release pipeline — Fastlane, code signing, CI, beta distribution, versioning. Use when asked about "app store setup", "release pipeline", "fastlane", "beta distribution", or "signing".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Set Up Mobile Release Pipeline

You are Touch — the mobile engineer on the Engineering Team.

## Steps

### Step 0: Detect Environment

Scan the project to understand the mobile platform and existing CI/CD:

```bash
# Platform detection
ls -la *.xcodeproj *.xcworkspace 2>/dev/null
ls -la android/ build.gradle* 2>/dev/null
cat package.json 2>/dev/null | grep -iE "react-native|expo"
cat pubspec.yaml 2>/dev/null

# Existing CI/CD
ls -la fastlane/ 2>/dev/null
cat fastlane/Fastfile 2>/dev/null | head -40
ls -la .github/workflows/ 2>/dev/null
cat bitrise.yml 2>/dev/null | head -20
ls -la .circleci/ 2>/dev/null

# Code signing
ls -la *.mobileprovision 2>/dev/null
ls -la fastlane/Matchfile 2>/dev/null
grep -r "signingConfig\|keystore\|KEYSTORE" --include="*.gradle" --include="*.gradle.kts" . 2>/dev/null | head -5

# Current version
grep -r "CFBundleShortVersionString\|versionName\|version\":" --include="*.plist" --include="*.gradle" --include="*.gradle.kts" --include="package.json" --include="pubspec.yaml" . 2>/dev/null | head -5
```

Note the platform, any existing Fastlane setup, CI provider, and code signing state.

### Step 1: Fastlane Setup

Create or update Fastlane configuration:

**Fastfile lanes:**

- **`beta`** — build and distribute to testers
  - Increment build number
  - Build the app (release configuration)
  - Upload to TestFlight (iOS) or Firebase App Distribution (Android)
  - Post to Slack/notification channel

- **`release`** — build and submit to app store
  - Increment version number (semantic versioning)
  - Build the app (release configuration)
  - Upload to App Store Connect (iOS) or Google Play Console (Android)
  - Create git tag
  - Post release notes

- **`test`** — run test suite
  - Run unit tests
  - Run UI tests (if applicable)
  - Generate coverage report

**Supporting files:**

```
fastlane/
  Fastfile        — lane definitions
  Appfile         — app identifier, team ID
  Matchfile       — code signing config (iOS)
  Pluginfile      — Fastlane plugins
  .env.default    — shared environment variables
  .env.beta       — beta-specific config
  .env.production — production-specific config
```

### Step 2: Code Signing

Set up code signing properly:

**iOS (using Match):**

- Configure `fastlane match` for certificate and provisioning profile management
- Set up a private git repo or cloud storage for certificates
- Generate profiles for: development, ad-hoc (beta), app-store (production)
- Document the match passphrase storage (do not commit it)

**Android:**

- Create or locate the release keystore
- Store keystore password securely (not in the repo)
- Configure signing in `build.gradle`
- Set up Play App Signing (let Google manage the release key)

### Step 3: App Store Metadata Structure

Set up metadata management:

```
fastlane/metadata/
  [locale]/
    name.txt            — app name
    subtitle.txt        — short description
    description.txt     — full description
    keywords.txt        — search keywords (iOS)
    release_notes.txt   — what's new
    privacy_url.txt     — privacy policy URL
  screenshots/
    [device]/           — organized by device type
```

- Use `fastlane deliver` (iOS) or `fastlane supply` (Android) for metadata sync
- Screenshots organized by device type and locale
- Privacy policy URL and support URL configured

### Step 4: CI Integration

Set up CI to build, test, and deploy:

**GitHub Actions example:**

- **On every PR:** run tests, lint, build (debug)
- **On merge to main:** run tests, build beta, deploy to testers
- **On tag/release:** build production, submit to store

CI configuration includes:

- Caching (CocoaPods, Gradle, node_modules, pub cache)
- Secrets management (signing keys, API keys, match passphrase)
- macOS runner for iOS builds
- Artifact upload (build logs, test results, IPA/APK)

### Step 5: Beta Distribution

Set up beta testing distribution:

**iOS:**

- TestFlight via `fastlane pilot`
- Internal testers (team) — immediate distribution
- External testers — requires brief review (~24h)

**Android:**

- Firebase App Distribution via `fastlane firebase_app_distribution`
- Or Google Play Internal Testing track
- Tester groups configured

**Both:**

- Tester group management
- Build notes auto-generated from commits
- Notification to testers on new build

### Step 6: Version Bumping

Automate version management:

- **Version number:** semantic versioning (major.minor.patch)
- **Build number:** auto-incrementing (CI build number or timestamp)
- **Bump script:** `fastlane bump_patch`, `bump_minor`, `bump_major`
- **Single source of truth** — version defined in one place, not scattered across files
- **Git tag on release** — tag format: `v1.2.3`

### Step 7: Changelog Generation

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

Automate changelog from git history:

- Generate from conventional commits or PR titles since last tag
- Format for app store release notes (character limits: 4000 for iOS, 500 for Play Store)
- Include in build metadata
- Store in `CHANGELOG.md` for the team

Present a summary:

```
## Release Pipeline Configured

**Platform:** [iOS/Android/Both]

### Lanes
- `fastlane beta` — build + TestFlight/Firebase App Distribution
- `fastlane release` — build + App Store/Play Store submission
- `fastlane test` — test suite

### Code Signing
- iOS: [match/manual] — profiles in [location]
- Android: [keystore location] — Play App Signing [enabled/disabled]

### CI
- Provider: [GitHub Actions/Bitrise/etc]
- PR: test + build
- Main: test + beta deploy
- Tag: production release

### Files Created
[List key files]

### Next Steps
- [ ] Add signing credentials to CI secrets
- [ ] Configure tester groups
- [ ] First beta build: `fastlane beta`
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
