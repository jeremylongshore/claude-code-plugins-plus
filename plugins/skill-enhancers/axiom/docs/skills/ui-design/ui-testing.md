# UI Testing

Reliable UI testing with condition-based waiting patterns and new Recording UI Automation features from Xcode 26.

**When to use**: Writing UI tests, recording interactions, tests have race conditions or timing dependencies, flaky tests

## Key Features

- **Recording UI Automation** – Record interactions as Swift code, replay across configurations, review video recordings
  - Three phases: Record → Replay → Review
  - Replay configurations (devices, languages, regions, orientations, accessibility)
  - Video review with scrubbing, overlays, filters
- **Condition-based waiting** – Eliminates flaky tests from sleep() timeouts
  - waitForExistence patterns
  - NSPredicate expectations
  - Custom condition polling
- Accessibility-first testing patterns
- SwiftUI and UIKit testing strategies
- Test plans and configurations
- Real-world impact: 15 min → 5 min test suite, 20% flaky → 2%

**Requirements**: Xcode 26+ for Recording UI Automation, original patterns work with earlier versions

## WWDC References

- [Recording UI Automation – Session 344](https://developer.apple.com/videos/play/wwdc2025/344/)

**Philosophy**: Wait for conditions, not arbitrary timeouts. Flaky tests come from guessing how long operations take.

## Example Prompts

These are real questions developers ask that this skill answers:

- **"My UI tests pass locally but fail in CI with no obvious reason."**
  → Shows condition-based waiting patterns that work across devices/speeds, eliminating CI timing differences

- **"My tests use sleep(2) and sleep(5) but they're still flaky."**
  → Demonstrates waitForExistence, XCTestExpectation, and polling patterns for data loads and network requests

- **"I just recorded a test using Xcode 26's Recording UI Automation. How do I debug failures?"**
  → Covers video debugging workflows to analyze recordings and find exactly where tests fail

- **"My test fails on iPad but passes on iPhone."**
  → Explains multi-factor testing strategies and device-independent predicates for cross-device testing

- **"I want tests that aren't flaky. What patterns should I use?"**
  → Provides condition-based waiting templates, accessibility-first patterns, and reliable test architecture
