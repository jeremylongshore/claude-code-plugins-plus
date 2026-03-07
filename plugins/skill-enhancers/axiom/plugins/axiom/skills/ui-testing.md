---
name: ui-testing
description: Use when writing UI tests, recording interactions, tests have race conditions, timing dependencies, inconsistent pass/fail behavior, or XCTest UI tests are flaky - covers Recording UI Automation (WWDC 2025), condition-based waiting, network conditioning, multi-factor testing, crash debugging, and accessibility-first testing patterns
version: 2.1.0
last_updated: WWDC 2025 (Updated with production debugging patterns)
---

# UI Testing

## Overview

Wait for conditions, not arbitrary timeouts. **Core principle:** Flaky tests come from guessing how long operations take. Condition-based waiting eliminates race conditions.

**NEW in WWDC 2025**: Recording UI Automation allows you to record interactions, replay across devices/languages, and review video recordings of test runs.

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "My UI tests pass locally on my Mac but fail in CI. How do I make them more reliable?"**
→ The skill shows condition-based waiting patterns that work across devices/speeds, eliminating CI timing differences

**2. "My tests use sleep(2) and sleep(5) but they're still flaky. How do I replace arbitrary timeouts with real conditions?"**
→ The skill demonstrates waitForExistence, XCTestExpectation, and polling patterns for data loads, network requests, and animations

**3. "I just recorded a test using Xcode 26's Recording UI Automation. How do I review the video and debug failures?"**
→ The skill covers Video Debugging workflows to analyze recordings and find the exact step where tests fail

**4. "My test is failing on iPad but passing on iPhone. How do I write tests that work across all device sizes?"**
→ The skill explains multi-factor testing strategies and device-independent predicates for robust cross-device testing

**5. "I want to write tests that are not flaky. What are the critical patterns I need to know?"**
→ The skill provides condition-based waiting templates, accessibility-first patterns, and the decision tree for reliable test architecture

---

## Red Flags - Test Reliability Issues

If you see ANY of these, suspect timing issues:
- Tests pass locally, fail in CI (timing differences)
- Tests sometimes pass, sometimes fail (race conditions)
- Tests use `sleep()` or `Thread.sleep()` (arbitrary delays)
- Tests fail with "UI element not found" then pass on retry
- Long test runs (waiting for worst-case scenarios)

## Quick Decision Tree

```
Test failing?
├─ Element not found?
│  └─ Use waitForExistence(timeout:) not sleep()
├─ Passes locally, fails CI?
│  └─ Replace sleep() with condition polling
├─ Animation causing issues?
│  └─ Wait for animation completion, don't disable
└─ Network request timing?
   └─ Use XCTestExpectation or waitForExistence
```

## Core Pattern: Condition-Based Waiting

**❌ WRONG (Arbitrary Timeout)**:
```swift
func testButtonAppears() {
    app.buttons["Login"].tap()
    sleep(2)  // ❌ Guessing it takes 2 seconds
    XCTAssertTrue(app.buttons["Dashboard"].exists)
}
```

**✅ CORRECT (Wait for Condition)**:
```swift
func testButtonAppears() {
    app.buttons["Login"].tap()
    let dashboard = app.buttons["Dashboard"]
    XCTAssertTrue(dashboard.waitForExistence(timeout: 5))
}
```

## Common UI Testing Patterns

### Pattern 1: Waiting for Elements

```swift
// Wait for element to appear
func waitForElement(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
    return element.waitForExistence(timeout: timeout)
}

// Usage
XCTAssertTrue(waitForElement(app.buttons["Submit"]))
```

### Pattern 2: Waiting for Element to Disappear

```swift
func waitForElementToDisappear(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
    let predicate = NSPredicate(format: "exists == false")
    let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
    let result = XCTWaiter().wait(for: [expectation], timeout: timeout)
    return result == .completed
}

// Usage
XCTAssertTrue(waitForElementToDisappear(app.activityIndicators["Loading"]))
```

### Pattern 3: Waiting for Specific State

```swift
func waitForButton(_ button: XCUIElement, toBeEnabled enabled: Bool, timeout: TimeInterval = 5) -> Bool {
    let predicate = NSPredicate(format: "isEnabled == %@", NSNumber(value: enabled))
    let expectation = XCTNSPredicateExpectation(predicate: predicate, object: button)
    let result = XCTWaiter().wait(for: [expectation], timeout: timeout)
    return result == .completed
}

// Usage
let submitButton = app.buttons["Submit"]
XCTAssertTrue(waitForButton(submitButton, toBeEnabled: true))
submitButton.tap()
```

### Pattern 4: Accessibility Identifiers

**Set in app**:
```swift
Button("Submit") {
    // action
}
.accessibilityIdentifier("submitButton")
```

**Use in tests**:
```swift
func testSubmitButton() {
    let submitButton = app.buttons["submitButton"]  // Uses identifier, not label
    XCTAssertTrue(submitButton.waitForExistence(timeout: 5))
    submitButton.tap()
}
```

**Why**: Accessibility identifiers don't change with localization, remain stable across UI updates.

### Pattern 5: Network Request Delays

```swift
func testDataLoads() {
    app.buttons["Refresh"].tap()

    // Wait for loading indicator to disappear
    let loadingIndicator = app.activityIndicators["Loading"]
    XCTAssertTrue(waitForElementToDisappear(loadingIndicator, timeout: 10))

    // Now verify data loaded
    XCTAssertTrue(app.cells.count > 0)
}
```

### Pattern 6: Animation Handling

```swift
func testAnimatedTransition() {
    app.buttons["Next"].tap()

    // Wait for destination view to appear
    let destinationView = app.otherElements["DestinationView"]
    XCTAssertTrue(destinationView.waitForExistence(timeout: 2))

    // Optional: Wait a bit more for animation to settle
    // Only if absolutely necessary
    RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.3))
}
```

## Testing Checklist

### Before Writing Tests
- [ ] Use accessibility identifiers for all interactive elements
- [ ] Avoid hardcoded labels (use identifiers instead)
- [ ] Plan for network delays and animations
- [ ] Choose appropriate timeouts (2s UI, 10s network)

### When Writing Tests
- [ ] Use `waitForExistence()` not `sleep()`
- [ ] Use predicates for complex conditions
- [ ] Test both success and failure paths
- [ ] Make tests independent (can run in any order)

### After Writing Tests
- [ ] Run tests 10 times locally (catch flakiness)
- [ ] Run tests on slowest supported device
- [ ] Run tests in CI environment
- [ ] Check test duration (if >30s per test, optimize)

## Xcode UI Testing Tips

### Launch Arguments for Testing

```swift
func testExample() {
    let app = XCUIApplication()
    app.launchArguments = ["UI-Testing"]
    app.launch()
}
```

In app code:
```swift
if ProcessInfo.processInfo.arguments.contains("UI-Testing") {
    // Use mock data, skip onboarding, etc.
}
```

### Faster Test Execution

```swift
override func setUpWithError() throws {
    continueAfterFailure = false  // Stop on first failure
}
```

### Debugging Failing Tests

```swift
func testExample() {
    // Take screenshot on failure
    addUIInterruptionMonitor(withDescription: "Alert") { alert in
        alert.buttons["OK"].tap()
        return true
    }

    // Print element hierarchy
    print(app.debugDescription)
}
```

## Common Mistakes

### ❌ Using sleep() for Everything
```swift
sleep(5)  // ❌ Wastes time if operation completes in 1s
```

### ❌ Not Handling Animations
```swift
app.buttons["Next"].tap()
XCTAssertTrue(app.buttons["Back"].exists)  // ❌ May fail during animation
```

### ❌ Hardcoded Text Labels
```swift
app.buttons["Submit"].tap()  // ❌ Breaks with localization
```

### ❌ Tests Depend on Each Other
```swift
// ❌ Test 2 assumes Test 1 ran first
func test1_Login() { /* ... */ }
func test2_ViewDashboard() { /* assumes logged in */ }
```

### ❌ No Timeout Strategy
```swift
element.waitForExistence(timeout: 100)  // ❌ Too long
element.waitForExistence(timeout: 0.1)  // ❌ Too short
```

**Use appropriate timeouts**:
- UI animations: 2-3 seconds
- Network requests: 10 seconds
- Complex operations: 30 seconds max

## Real-World Impact

**Before** (using sleep()):
- Test suite: 15 minutes (waiting for worst-case)
- Flaky tests: 20% failure rate
- CI failures: 50% require retry

**After** (condition-based waiting):
- Test suite: 5 minutes (waits only as needed)
- Flaky tests: <2% failure rate
- CI failures: <5% require retry

**Key insight:** Tests finish faster AND are more reliable when waiting for actual conditions instead of guessing times.

---

## Recording UI Automation (WWDC 2025)

### Overview

**NEW in Xcode 26**: Record, replay, and review UI automation tests with video recordings.

**Three Phases**:
1. **Record** - Capture interactions (taps, swipes, hardware button presses) as Swift code
2. **Replay** - Run across multiple devices, languages, regions, orientations
3. **Review** - Watch video recordings, analyze failures, view UI element overlays

**Supported Platforms**: iOS, iPadOS, macOS, watchOS, tvOS, visionOS (Designed for iPad)

### How UI Automation Works

**Key Principles**:
- UI automation interacts with your app **as a person does** using gestures and hardware events
- Runs **completely independently** from your app (app models/data not directly accessible)
- Uses **accessibility framework** as underlying technology
- Tells OS which gestures to perform, then waits for completion **synchronously** one at a time

**Actions include**:
- Launching your app
- Interacting with buttons and navigation
- Setting system state (Dark Mode, localization, etc.)
- Setting simulated location

### Accessibility is the Foundation

**Critical Understanding**: Accessibility provides information directly to UI automation.

What accessibility sees:
- Element types (button, text, image, etc.)
- Labels (visible text)
- Values (current state for checkboxes, etc.)
- Frames (element positions)
- **Identifiers** (accessibility identifiers - NOT localized)

**Best Practice**: Great accessibility experience = great UI automation experience.

### Preparing Your App for Recording

#### Step 1: Add Accessibility Identifiers

**SwiftUI**:
```swift
Button("Submit") {
    // action
}
.accessibilityIdentifier("submitButton")

// Make identifiers specific to instance
List(landmarks) { landmark in
    LandmarkRow(landmark)
        .accessibilityIdentifier("landmark-\(landmark.id)")
}
```

**UIKit**:
```swift
let button = UIButton()
button.accessibilityIdentifier = "submitButton"

// Use index for table cells
cell.accessibilityIdentifier = "cell-\(indexPath.row)"
```

**Good identifiers are**:
- ✅ Unique within entire app
- ✅ Descriptive of element contents
- ✅ Static (don't react to content changes)
- ✅ Not localized (same across languages)

**Why identifiers matter**:
- Titles/descriptions may change, identifiers remain stable
- Work across localized strings
- Uniquely identify elements with dynamic content

**Pro Tip**: Use Xcode coding assistant to add identifiers:
```
Prompt: "Add accessibility identifiers to the relevant parts of this view"
```

#### Step 2: Review Accessibility with Accessibility Inspector

**Launch Accessibility Inspector**:
- Xcode menu → Open Developer Tool → Accessibility Inspector
- Or: Launch from Spotlight

**Features**:
1. **Element Inspector** - List accessibility values for any view
2. **Property details** - Click property name for documentation
3. **Platform support** - Works on all Apple platforms

**What to check**:
- Elements have labels
- Interactive elements have types (button, not just text)
- Values set for stateful elements (checkboxes, toggles)
- Identifiers set for elements with dynamic/localized content

**Sample Code Reference**: [Delivering an exceptional accessibility experience](https://developer.apple.com/documentation/accessibility/delivering_an_exceptional_accessibility_experience)

#### Step 3: Add UI Testing Target

1. Open project settings in Xcode
2. Click "+" below targets list
3. Select **UI Testing Bundle**
4. Click Finish

**Result**: New UI test folder with template tests added to project.

### Recording Interactions

#### Starting a Recording (Xcode 26)

1. Open UI test source file
2. **Popover appears** explaining how to start recording (first time only)
3. Click **"Start Recording"** button in editor gutter
4. Xcode builds and launches app in Simulator/device

**During Recording**:
- Interact with app normally (taps, swipes, text entry, etc.)
- Code representing interactions appears in source editor in real-time
- Recording updates as you type (e.g., text field entries)

**Stopping Recording**:
- Click **"Stop Run"** button in Xcode

#### Example Recording Session

```swift
func testCreateAustralianCollection() {
    let app = XCUIApplication()
    app.launch()

    // Tap "Collections" tab (recorded automatically)
    app.tabBars.buttons["Collections"].tap()

    // Tap "+" to add new collection
    app.navigationBars.buttons["Add"].tap()

    // Tap "Edit" button
    app.buttons["Edit"].tap()

    // Type collection name
    app.textFields.firstMatch.tap()
    app.textFields.firstMatch.typeText("Max's Australian Adventure")

    // Tap "Edit Landmarks"
    app.buttons["Edit Landmarks"].tap()

    // Add landmarks
    app.tables.cells.containing(.staticText, identifier:"Great Barrier Reef").buttons["Add"].tap()
    app.tables.cells.containing(.staticText, identifier:"Uluru").buttons["Add"].tap()

    // Tap checkmark to save
    app.navigationBars.buttons["Done"].tap()
}
```

#### Reviewing Recorded Code

After recording, **review and adjust queries**:

**Multiple Options**: Each line has dropdown showing alternative ways to address element.

**Selection Recommendations**:
1. **For localized strings** (text, button labels): Choose accessibility identifier if available
2. **For deeply nested views**: Choose shortest query (stays resilient as app changes)
3. **For dynamic content** (timestamps, temperature): Use generic query or identifier

**Example**:
```swift
// Recorded options for text field:
app.textFields["Collection Name"]              // ❌ Breaks if label localizes
app.textFields["collectionNameField"]          // ✅ Uses identifier
app.textFields.element(boundBy: 0)             // ✅ Position-based
app.textFields.firstMatch                      // ✅ Generic, shortest
```

**Choose shortest, most stable query** for your needs.

### Adding Validations

After recording, **add assertions** to verify expected behavior:

#### Wait for Existence

```swift
// Validate collection created
let collection = app.buttons["Max's Australian Adventure"]
XCTAssertTrue(collection.waitForExistence(timeout: 5))
```

#### Wait for Property Changes

```swift
// Wait for button to become enabled
let submitButton = app.buttons["Submit"]
XCTAssertTrue(submitButton.wait(for: .enabled, toEqual: true, timeout: 5))
```

#### Combine with XCTAssert

```swift
// Fail test if element doesn't appear
let landmark = app.staticTexts["Great Barrier Reef"]
XCTAssertTrue(landmark.waitForExistence(timeout: 5), "Landmark should appear in collection")
```

### Advanced Automation APIs

#### Setup Device State

```swift
override func setUpWithError() throws {
    let app = XCUIApplication()

    // Set device orientation
    XCUIDevice.shared.orientation = .landscapeLeft

    // Set appearance mode
    app.launchArguments += ["-UIUserInterfaceStyle", "dark"]

    // Simulate location
    let location = XCUILocation(location: CLLocation(latitude: 37.7749, longitude: -122.4194))
    app.launchArguments += ["-SimulatedLocation", location.description]

    app.launch()
}
```

#### Launch Arguments & Environment

```swift
func testWithMockData() {
    let app = XCUIApplication()

    // Pass arguments to app
    app.launchArguments = ["-UI-Testing", "-UseMockData"]

    // Set environment variables
    app.launchEnvironment = ["API_URL": "https://mock.api.com"]

    app.launch()
}
```

In app code:
```swift
if ProcessInfo.processInfo.arguments.contains("-UI-Testing") {
    // Use mock data, skip onboarding
}
```

#### Custom URL Schemes

```swift
// Open app to specific URL
let app = XCUIApplication()
app.open(URL(string: "myapp://landmark/123")!)

// Open URL with system default app (global version)
XCUIApplication.open(URL(string: "https://example.com")!)
```

#### Accessibility Audits in Tests

```swift
func testAccessibility() throws {
    let app = XCUIApplication()
    app.launch()

    // Perform accessibility audit
    try app.performAccessibilityAudit()
}
```

**Reference**: [Perform accessibility audits for your app - WWDC23](https://developer.apple.com/videos/play/wwdc2023/10035/)

### Test Plans for Multiple Configurations

**Test Plans** let you:
- Include/exclude individual tests
- Set system settings (language, region, appearance)
- Configure test properties (timeouts, repetitions, parallelization)
- Associate with schemes for specific build settings

#### Creating Test Plan

1. Create new or use existing test plan
2. Add/remove tests on first screen
3. Switch to **Configurations** tab

#### Adding Multiple Languages

```
Configurations:
├─ English
├─ German (longer strings)
├─ Arabic (right-to-left)
└─ Hebrew (right-to-left)
```

**Each locale** = separate configuration in test plan.

**Settings**:
- Focused for specific locale
- Shared across all configurations

#### Video & Screenshot Capture

**In Configurations tab**:
- **Capture screenshots**: On/Off
- **Capture video**: On/Off
- **Keep media**: "Only failures" or "On, and keep all"

**Defaults**: Videos/screenshots kept only for failing runs (for review).

**"On, and keep all" use cases**:
- Documentation
- Tutorials
- Marketing materials

**Reference**: [Author fast and reliable tests for Xcode Cloud - WWDC22](https://developer.apple.com/videos/play/wwdc2022/110371/)

### Replaying Tests in Xcode Cloud

**Xcode Cloud** = built-in service for:
- Building app
- Running tests
- Uploading to App Store
- All in cloud without using team devices

**Workflow configuration**:
- Same test plan used locally
- Runs on multiple devices and configurations
- Videos/results available in App Store Connect

**Viewing Results**:
- Xcode: Xcode Cloud section
- App Store Connect: Xcode Cloud section
- See build info, logs, failure descriptions, video recordings

**Team Access**: Entire team can see run history and download results/videos.

**Reference**: [Create practical workflows in Xcode Cloud - WWDC23](https://developer.apple.com/videos/play/wwdc2023/10269/)

### Reviewing Test Results with Videos

#### Accessing Test Report

1. Click **Test** button in Xcode
2. Double-click failing run to see video + description

**Features**:
- **Runs dropdown** - Switch between video recordings of different configurations (languages, devices)
- **Save video** - Secondary click → Save
- **Play/pause** - Video playback with UI interaction overlays
- **Timeline dots** - UI interactions shown as dots on timeline
- **Jump to failure** - Click failure diamond on timeline

#### UI Element Overlay at Failure

**At moment of failure**:
- Click timeline failure point
- **Overlay shows all UI elements** present on screen
- Click any element to see code recommendations for addressing it
- **Show All** - See alternative examples

**Workflow**:
1. Identify what was actually present (vs what test expected)
2. Click element to get query code
3. Secondary click → Copy code
4. **View Source** → Go directly to test
5. Paste corrected code

**Example**:
```swift
// Test expected:
let button = app.buttons["Max's Australian Adventure"]

// But overlay shows it's actually text, not button:
let text = app.staticTexts["Max's Australian Adventure"] // ✅ Correct
```

#### Running Test in Different Language

Click test diamond → Select configuration (e.g., Arabic) → Watch automation run in right-to-left layout.

**Validates**: Same automation works across languages/layouts.

**Reference**: [Fix failures faster with Xcode test reports - WWDC23](https://developer.apple.com/videos/play/wwdc2023/10175/)

### Recording UI Automation Checklist

#### Before Recording
- [ ] Add accessibility identifiers to interactive elements
- [ ] Review app with Accessibility Inspector
- [ ] Add UI Testing Bundle target to project
- [ ] Plan workflow to record (user journey)

#### During Recording
- [ ] Interact naturally with app
- [ ] Record complete user journeys (not individual taps)
- [ ] Check code generates as you interact
- [ ] Stop recording when workflow complete

#### After Recording
- [ ] Review recorded code options (dropdown on each line)
- [ ] Choose stable queries (identifiers > labels)
- [ ] Add validations (waitForExistence, XCTAssert)
- [ ] Add setup code (device state, launch arguments)
- [ ] Run test to verify it passes

#### Test Plan Configuration
- [ ] Create/update test plan
- [ ] Add multiple language configurations
- [ ] Include right-to-left languages (Arabic, Hebrew)
- [ ] Configure video/screenshot capture settings
- [ ] Set appropriate timeouts for network tests

#### Running & Reviewing
- [ ] Run test locally across configurations
- [ ] Review video recordings for failures
- [ ] Use UI element overlay to debug failures
- [ ] Run in Xcode Cloud for team visibility
- [ ] Download and share videos if needed

## Network Conditioning in Tests

### Overview

UI tests can pass on fast networks but fail on 3G/LTE. **Network Link Conditioner** simulates real-world network conditions to catch timing-sensitive crashes.

**Critical scenarios**:
- ❌ iPad Pro over Wi-Fi (fast) → pass
- ❌ iPad Pro over 3G (slow) → crash
- ✅ Test both to catch device-specific failures

### Setup Network Link Conditioner

**Install Network Link Conditioner**:
1. Download from [Apple's Additional Tools for Xcode](https://developer.apple.com/download/all/)
2. Search: "Network Link Conditioner"
3. Install: `sudo open Network\ Link\ Conditioner.pkg`

**Verify Installation**:
```bash
# Check if installed
ls ~/Library/Application\ Support/Network\ Link\ Conditioner/
```

**Enable in Tests**:
```swift
override func setUpWithError() throws {
    let app = XCUIApplication()

    // Launch with network conditioning argument
    app.launchArguments = ["-com.apple.CoreSimulator.CoreSimulatorService", "-networkShaping"]
    app.launch()
}
```

### Common Network Profiles

**3G Profile** (most failures occur here):
```swift
override func setUpWithError() throws {
    let app = XCUIApplication()

    // Simulate 3G (type in launch arguments)
    app.launchEnvironment = [
        "SIMULATOR_UDID": ProcessInfo.processInfo.environment["SIMULATOR_UDID"] ?? "",
        "NETWORK_PROFILE": "3G"
    ]
    app.launch()
}
```

**Manual Network Conditioning** (macOS System Preferences):
1. Open System Preferences → Network
2. Click "Network Link Conditioner" (installed above)
3. Select profile: 3G, LTE, WiFi
4. Click "Start"
5. Run tests (they'll use throttled network)

### Real-World Example: Photo Upload with Network Throttling

**❌ Without Network Conditioning**:
```swift
func testPhotoUpload() {
    app.buttons["Upload Photo"].tap()

    // Passes locally (fast network)
    XCTAssertTrue(app.staticTexts["Upload complete"].waitForExistence(timeout: 5))
}
// ✅ Passes locally, ❌ FAILS on 3G with timeout
```

**✅ With Network Conditioning**:
```swift
func testPhotoUploadOn3G() {
    let app = XCUIApplication()
    // Network Link Conditioner running (3G profile)
    app.launch()

    app.buttons["Upload Photo"].tap()

    // Increase timeout for 3G
    XCTAssertTrue(app.staticTexts["Upload complete"].waitForExistence(timeout: 30))

    // Verify no crash occurred
    XCTAssertFalse(app.alerts.element.exists, "App should not crash on 3G")
}
```

**Key differences**:
- Longer timeout (30s instead of 5s)
- Check for crashes
- Run on slowest expected network

---

## Multi-Factor Testing: Device Size + Network Speed

### The Problem

Tests can pass on device A but fail on device B due to layout differences + network delays. **Multi-factor testing** catches these combinations.

**Common failure patterns**:
- ✅ iPhone 14 Pro (compact, fast network)
- ❌ iPad Pro 12.9 (large, 3G network) → crashes
- ✅ iPhone 15 (compact, LTE)
- ❌ iPhone 12 (older GPU, 3G) → timeout

### Test Plan Configuration for Multiple Devices

**Create Test Plan in Xcode**:
1. File → New → Test Plan
2. Select tests to include
3. Click "Configurations" tab
4. Add configurations for each device/network combo

**Example Configuration Matrix**:
```
Configurations:
├─ iPhone 14 Pro + LTE
├─ iPhone 14 Pro + 3G
├─ iPad Pro 12.9 + LTE
├─ iPad Pro 12.9 + 3G  (⚠️ Most failures here)
└─ iPhone 12 + 3G      (⚠️ Older device)
```

**In Test Plan UI**:
- Device: iPhone 14 Pro / iPad Pro 12.9
- OS Version: Latest
- Locale: English
- Network Profile: LTE / 3G

### Programmatic Device-Specific Testing

```swift
import XCTest

final class MultiFactorUITests: XCTestCase {
    var deviceModel: String { UIDevice.current.model }

    override func setUpWithError() throws {
        let app = XCUIApplication()
        app.launch()

        // Adjust timeouts based on device
        switch deviceModel {
        case "iPad" where UIScreen.main.bounds.width > 1000:
            // iPad Pro - larger layout, slower rendering
            app.launchEnvironment["TEST_TIMEOUT"] = "30"
        case "iPhone":
            // iPhone - compact, standard timeout
            app.launchEnvironment["TEST_TIMEOUT"] = "10"
        default:
            app.launchEnvironment["TEST_TIMEOUT"] = "15"
        }
    }

    func testListLoadingAcrossDevices() {
        let app = XCUIApplication()
        let timeout = Double(app.launchEnvironment["TEST_TIMEOUT"] ?? "10") ?? 10

        app.buttons["Refresh"].tap()

        // Wait for list to load (timeout varies by device)
        XCTAssertTrue(
            app.tables.cells.count > 0,
            "List should load on \(deviceModel)"
        )

        // Verify no crashes
        XCTAssertFalse(app.alerts.element.exists)
    }
}
```

### Real-World Example: iPad Pro + 3G Crash

**Scenario**: App works on iPhone 14, crashes on iPad Pro over 3G.

**Why it crashes**:
1. iPad Pro has larger layout (landscape)
2. 3G network is slow (latency 100ms+)
3. Images don't load in time, layout engine crashes
4. Single-device testing misses this combo

**Test that catches it**:
```swift
func testLargeLayoutOn3G() {
    let app = XCUIApplication()
    // Running with Network Link Conditioner on 3G profile
    app.launch()

    // iPad Pro: Large grid of images
    app.buttons["Browse"].tap()

    // Wait longer for images on slow network
    let firstImage = app.images["photoGrid-0"]
    XCTAssertTrue(
        firstImage.waitForExistence(timeout: 20),
        "First image must load on slow network"
    )

    // Verify grid loaded without crash
    let loadedCount = app.images.matching(identifier: NSPredicate(format: "identifier BEGINSWITH 'photoGrid'")).count
    XCTAssertGreater(loadedCount, 5, "Multiple images should load on 3G")

    // No alerts (no crashes)
    XCTAssertFalse(app.alerts.element.exists, "App should not crash on large device + slow network")
}
```

### Running Multi-Factor Tests in CI

**In GitHub Actions or Xcode Cloud**:
```yaml
- name: Run tests across devices
  run: |
    xcodebuild -scheme MyApp \
      -testPlan MultiDeviceTestPlan \
      test
```

**Test Plan runs on**:
- iPhone 14 Pro + LTE
- iPhone 14 Pro + 3G
- iPad Pro + LTE
- iPad Pro + 3G

**Result**: Catch device-specific crashes before App Store submission.

---

## Debugging Crashes Revealed by UI Tests

### Overview

UI tests sometimes reveal crashes that don't happen in manual testing. **Key insight:** Automated tests run faster, interact with app differently, and can expose concurrency/timing bugs.

**When crashes happen**:
- ❌ Manual testing: Can't reproduce (works when you run it)
- ✅ UI Test: Crashes every time (automated repetition finds race condition)

### Recognizing Test-Revealed Crashes

**Signs in test output**:
```
Failing test: testPhotoUpload
Error: The app crashed while responding to a UI event
App died from an uncaught exception
Stack trace: [EXC_BAD_ACCESS in PhotoViewController]
```

**Video shows**: App visibly crashes (black screen, immediate termination).

### Systematic Debugging Approach

#### Step 1: Capture Crash Details

**Enable detailed logging**:
```swift
override func setUpWithError() throws {
    let app = XCUIApplication()

    // Enable all logging
    app.launchEnvironment = [
        "OS_ACTIVITY_MODE": "debug",
        "DYLD_PRINT_STATISTICS": "1"
    ]

    // Enable test diagnostics
    if #available(iOS 17, *) {
        let options = XCUIApplicationLaunchOptions()
        options.captureRawLogs = true
        app.launch(options)
    } else {
        app.launch()
    }
}
```

#### Step 2: Reproduce Locally

```swift
func testReproduceCrash() {
    let app = XCUIApplication()
    app.launch()

    // Run exact sequence that causes crash
    app.buttons["Browse"].tap()
    app.buttons["Photo Album"].tap()
    app.buttons["Select All"].tap()
    app.buttons["Upload"].tap()

    // Should crash here
    let uploadButton = app.buttons["Upload"]
    XCTAssertFalse(uploadButton.exists, "App crashed (expected)")

    // Don't assert - just let it crash and read logs
}
```

**Run test with Console logs visible**:
- Xcode: View → Navigators → Show Console
- Watch for exception messages

#### Step 3: Analyze Crash Logs

**Locations**:
1. Xcode Console (real-time, less detail)
2. ~/Library/Logs/DiagnosticMessages/crash_*.log (full details)
3. Device Settings → Privacy → Analytics → Analytics Data

**Look for**:
- Thread that crashed
- Exception type (EXC_BAD_ACCESS, EXC_CRASH, etc.)
- Stack trace showing which method crashed

**Example crash log**:
```
Exception Type: EXC_BAD_ACCESS (SIGSEGV)
Exception Codes: KERN_INVALID_ADDRESS at 0x0000000000000000
Thread 0 Crashed:
0  MyApp    0x0001a234 -[PhotoViewController reloadPhotos:] + 234
1  MyApp    0x0001a123 -[PhotoViewController viewDidLoad] + 180
```

**This tells us**:
- Crash in `PhotoViewController.reloadPhotos(_:)`
- Likely null pointer dereference
- Called from `viewDidLoad`

#### Step 4: Connection to Swift Concurrency Issues

**Most UI test crashes are concurrency bugs** (not specific to UI testing). Reference related skills:

```swift
// Common pattern: Race condition in async image loading
class PhotoViewController: UIViewController {
    var photos: [Photo] = []

    override func viewDidLoad() {
        super.viewDidLoad()

        // ❌ WRONG: Accessing photos array from multiple threads
        Task {
            let newPhotos = await fetchPhotos()
            self.photos = newPhotos  // May crash if main thread access
            reloadPhotos()  // ❌ Crash here
        }
    }
}

// ✅ CORRECT: Ensure main thread
class PhotoViewController: UIViewController {
    @MainActor
    var photos: [Photo] = []

    override func viewDidLoad() {
        super.viewDidLoad()

        Task {
            let newPhotos = await fetchPhotos()
            await MainActor.run { [weak self] in
                self?.photos = newPhotos
                self?.reloadPhotos()  // ✅ Safe
            }
        }
    }
}
```

**For deep crash analysis**: See `swift-concurrency` skill for @MainActor patterns and `memory-debugging` skill for thread-safety issues.

#### Step 5: Add Crash-Prevention Tests

**After fixing**:
```swift
func testPhotosLoadWithoutCrash() {
    let app = XCUIApplication()
    app.launch()

    // Rapid fire interactions that previously caused crash
    app.buttons["Browse"].tap()
    app.buttons["Photo Album"].tap()

    // Load should complete without crash
    let photoGrid = app.otherElements["photoGrid"]
    XCTAssertTrue(photoGrid.waitForExistence(timeout: 10))

    // No alerts (no crash dialogs)
    XCTAssertFalse(app.alerts.element.exists)
}
```

#### Step 6: Stress Test to Verify Fix

```swift
func testPhotosLoadUnderStress() {
    let app = XCUIApplication()
    app.launch()

    // Repeat the crash-causing action multiple times
    for iteration in 0..<10 {
        app.buttons["Browse"].tap()

        // Wait for load
        let grid = app.otherElements["photoGrid"]
        XCTAssertTrue(grid.waitForExistence(timeout: 10), "Iteration \(iteration)")

        // Go back
        app.navigationBars.buttons["Back"].tap()
        app.buttons["Refresh"].tap()
    }

    // Completed without crash
    XCTAssertTrue(true, "Stress test passed")
}
```

### Prevention Checklist

**Before releasing:**
- [ ] Run UI tests on slowest network (3G)
- [ ] Run on largest device (iPad Pro)
- [ ] Run on oldest supported device (iPhone 12)
- [ ] Record video of test runs (saves debugging time)
- [ ] Check for crashes in logs
- [ ] Run stress tests (10x repeated actions)
- [ ] Verify @MainActor on UI properties
- [ ] Check for race conditions in async code

---

## Reference

**WWDC 2025 Sessions**:
- [Record, replay, and review: UI automation with Xcode - WWDC25 Session 344](https://developer.apple.com/videos/play/wwdc2025/344/)
  - Recording UI automation, test plans, video review

**WWDC 2023 Sessions**:
- [Fix failures faster with Xcode test reports - WWDC23](https://developer.apple.com/videos/play/wwdc2023/10175/)
- [Perform accessibility audits for your app - WWDC23](https://developer.apple.com/videos/play/wwdc2023/10035/)

**WWDC 2024 Sessions**:
- [Meet Swift Testing - WWDC24](https://developer.apple.com/videos/play/wwdc2024/10179/)

**Apple Documentation**:
- [XCTest Framework](https://developer.apple.com/documentation/xctest)
- [Recording UI automation for testing](https://developer.apple.com/documentation/XCUIAutomation/recording-ui-automation-for-testing)
- [UI Testing in Xcode](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/testing_with_xcode/chapters/09-ui_testing.html)
- [XCTWaiter](https://developer.apple.com/documentation/xctest/xctwaiter)
- [Delivering an exceptional accessibility experience](https://developer.apple.com/documentation/accessibility/delivering_an_exceptional_accessibility_experience)
- [Performing accessibility testing for your app](https://developer.apple.com/documentation/accessibility/performing_accessibility_testing_for_your_app)

**Note**: This skill focuses on reliability patterns and Recording UI Automation. For TDD workflow, see superpowers:test-driven-development.

---

## Version History

- **2.1.0**: Added Network Conditioning, Multi-Factor Testing (device + network combinations), and Crash Debugging sections from TDD pressure testing (iPad Pro + 3G scenario). Prevents App Store review blockers by catching device-specific failures before submission
- **2.0.0 (WWDC 2025)**: Added Recording UI Automation section with comprehensive guidance on recording, replaying, reviewing tests; test plans; video debugging; accessibility-first patterns from WWDC 2025 Session 344
- **1.0.0**: Initial version focusing on condition-based waiting patterns
