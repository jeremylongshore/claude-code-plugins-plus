---
name: testing-mobile-apps
description: |
  Execute mobile app testing on iOS and Android devices/simulators.
  Use when performing specialized testing.
  Trigger with phrases like "test mobile app", "run iOS tests", or "validate Android functionality".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:mobile-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Mobile App Tester

## Overview

Execute automated mobile application testing on iOS simulators and Android emulators covering UI interactions, navigation flows, gesture handling, and platform-specific behaviors. Supports Appium, Detox (React Native), XCUITest (iOS native), Espresso (Android native), and Maestro for cross-platform mobile testing.

## Prerequisites

- Mobile testing framework installed (Appium, Detox, Maestro, or native XCUITest/Espresso)
- iOS Simulator via Xcode (macOS only) or Android Emulator via Android SDK
- Application build artifact (`.app`, `.apk`, or `.ipa`) or bundled dev server (React Native)
- Appium drivers installed (`uiautomator2` for Android, `xcuitest` for iOS) if using Appium
- Node.js for JavaScript-based test runners

## Instructions

1. Configure the test environment:
   - List target devices/simulators: specify OS versions, screen sizes, and orientations.
   - Build the application for testing (`xcodebuild`, `./gradlew assembleDebug`, or `npx react-native build`).
   - Start the emulator/simulator or connect physical devices.
   - Install the app on the target device.
2. Create test cases for core mobile interactions:
   - **Tap and navigation**: Tap buttons, navigate between screens, verify back navigation.
   - **Text input**: Fill forms, verify keyboard behavior, test autocomplete and paste.
   - **Scrolling**: Scroll lists, verify lazy loading, test pull-to-refresh.
   - **Gestures**: Swipe (carousel), pinch-to-zoom, long press, drag-and-drop.
   - **System interactions**: Handle permission dialogs, push notifications, deep links.
3. Test platform-specific behaviors:
   - iOS: Safe area insets, notch handling, Dynamic Type, VoiceOver accessibility.
   - Android: Back button behavior, multi-window, different navigation patterns, TalkBack.
   - Both: Screen rotation (portrait/landscape), dark mode, low battery mode.
4. Implement device-specific test configurations:
   - Define capability sets for each device/OS combination.
   - Use test tagging to run subsets on specific platforms (`@ios`, `@android`).
   - Configure screenshot capture on failure for visual debugging.
5. Handle asynchronous mobile behaviors:
   - Wait for animations to complete before assertions.
   - Handle network loading spinners with explicit waits.
   - Account for system dialogs (permissions, updates) that interrupt test flow.
6. Run the test suite and capture results:
   - Execute tests per platform: `npx detox test --configuration ios.sim.debug`.
   - Collect device logs, screenshots, and crash reports.
   - Generate JUnit XML or Allure reports for CI integration.
7. Set up CI pipeline for mobile testing (GitHub Actions macOS runners for iOS, Linux for Android).

## Output

- Mobile test files organized by feature/flow in `tests/mobile/` or `e2e/`
- Device configuration profiles for each target device/OS combination
- Screenshot captures for visual validation and failure debugging
- Test results in JUnit XML format with device-specific metadata
- CI pipeline configuration for automated mobile test execution

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Simulator/emulator fails to boot | Insufficient disk space or corrupted simulator image | Delete derived data and reset simulator; increase disk allocation; recreate the emulator AVD |
| App crashes on launch during test | Missing permissions or incompatible OS version | Check minimum deployment target; grant required permissions in test setup; verify app signing |
| Element not found | Element ID changed or screen did not finish loading | Use accessibility IDs instead of XPath; add explicit waits; verify element visibility before interaction |
| Test flaky on CI but passes locally | CI runner has slower CPU/GPU affecting animations and timing | Increase wait timeouts for CI; disable animations in developer settings; use dedicated CI hardware |
| Permission dialog blocks test | System alert appeared over the app UI | Auto-dismiss alerts in test setup; pre-grant permissions via `xcrun simctl` or ADB commands |

## Examples

**Detox test for React Native login flow:**
```javascript
describe('Login Flow', () => {
  beforeAll(async () => { await device.launchApp(); });
  beforeEach(async () => { await device.reloadReactNative(); });

  it('logs in with valid credentials', async () => {
    await element(by.id('email-input')).typeText('user@test.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();
    await expect(element(by.id('home-screen'))).toBeVisible();
  });
});
```

**Maestro flow file:**
```yaml
appId: com.example.myapp
---
- launchApp
- tapOn: "Sign In"
- inputText:
    id: "email-input"
    text: "user@test.com"
- inputText:
    id: "password-input"
    text: "password123"
- tapOn: "Submit"
- assertVisible: "Welcome"
```

## Resources

- Appium documentation: https://appium.io/docs/en/latest/
- Detox (React Native): https://wix.github.io/Detox/
- Maestro mobile testing: https://maestro.mobile.dev/
- XCUITest: https://developer.apple.com/documentation/xctest/user-interface-tests
- Espresso (Android): https://developer.android.com/training/testing/espresso