# iOS Privacy & Permissions

Best practices for permission requests, privacy UI, and building user trust.

## Permission Request Philosophy

**Core principle:** Request permissions only when needed, explain why, and respect "no."

Users are increasingly permission-fatigued. Every unnecessary or poorly-timed request damages trust and increases denial rates.

---

## Permission Request Timing

### Just-In-Time Requests

Request permissions when the user takes an action that requires them, not at app launch.

**Bad:** Request camera permission on first launch
**Good:** Request camera permission when user taps "Take Photo"

### The Pre-Permission Pattern

Before the system dialog, show a custom screen explaining the value.

```
┌─────────────────────────────────────────┐
│                                         │
│         [Camera icon]                   │
│                                         │
│    Take photos of your receipts         │
│                                         │
│    We use your camera to quickly        │
│    scan and organize your expenses.     │
│    Photos are stored only on your       │
│    device.                              │
│                                         │
│    ┌─────────────────────────────────┐  │
│    │        Allow Camera             │  │
│    └─────────────────────────────────┘  │
│                                         │
│            Maybe Later                  │
│                                         │
└─────────────────────────────────────────┘
```

**Benefits:**
- Explains value before system dialog
- "Maybe Later" doesn't trigger system denial
- Higher acceptance rates
- Better user understanding

### System Permission Dialog

```swift
// Camera
AVCaptureDevice.requestAccess(for: .video) { granted in
    // Handle response
}

// Photos
PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
    // Handle status
}

// Location
locationManager.requestWhenInUseAuthorization()
// or
locationManager.requestAlwaysAuthorization()

// Notifications
UNUserNotificationCenter.current().requestAuthorization(
    options: [.alert, .badge, .sound]
) { granted, error in
    // Handle response
}
```

---

## Permission Types & Best Practices

### Camera

**When to request:** When user initiates camera action

**Usage string example:**
"[App] needs camera access to scan documents and take photos for your projects."

**Best practices:**
- Only request when camera feature is used
- Offer photo library as alternative
- Handle denial gracefully (show library option)

### Photo Library

**Access levels (iOS 14+):**
- `.addOnly` - Can add photos, can't read (for saving)
- `.readWrite` - Full access
- Limited selection - User picks specific photos

**When to request:** When user wants to access photos

**Usage string example:**
"[App] accesses your photos to let you add images to your posts."

**Best practices:**
- Request `.addOnly` if you only need to save
- Support limited photo selection (don't require full access)
- Use PHPicker for one-time selection (no permission needed)

```swift
// PHPicker - no permission required
var config = PHPickerConfiguration()
config.selectionLimit = 1
config.filter = .images

let picker = PHPickerViewController(configuration: config)
```

### Location

**Authorization levels:**
- `.whenInUse` - Only while app is active
- `.always` - Background location access

**When to request:** When location feature is needed

**Usage strings needed:**
- `NSLocationWhenInUseUsageDescription`
- `NSLocationAlwaysAndWhenInUseUsageDescription` (for always)

**Best practices:**
- Start with "When In Use" before requesting "Always"
- Explain why background location is needed
- Provide value even without location
- Use significant location changes if precise tracking unnecessary

```swift
// Request when in use first
locationManager.requestWhenInUseAuthorization()

// Later, if needed, escalate to always
// (triggers new system prompt explaining upgrade)
locationManager.requestAlwaysAuthorization()
```

### Notifications

**When to request:** After user has experienced app value

**Usage string example:**
"[App] sends notifications for messages from your team and important updates."

**Best practices:**
- Don't request on first launch
- Wait until user has seen value
- Explain what notifications they'll receive
- Provide in-app notification preferences
- Respect system settings

**Provisional notifications (iOS 12+):**
```swift
// Quietly delivered to Notification Center
// User can choose to keep or turn off
UNUserNotificationCenter.current().requestAuthorization(
    options: [.provisional, .alert, .sound]
) { granted, error in }
```

### Contacts

**When to request:** When user initiates contact-related feature

**Usage string example:**
"[App] accesses your contacts to help you invite friends and find people you know."

**Best practices:**
- Use CNContactPickerViewController when possible (no permission)
- Only request full access when truly needed
- Never sync contacts without explicit permission

### Microphone

**When to request:** When user initiates audio recording

**Usage string example:**
"[App] uses your microphone to record voice messages and audio notes."

**Best practices:**
- Clear indicator when recording
- Option to preview before sending
- Explain storage/transmission of audio

### Health Data

**When to request:** When user enables health features

**Best practices:**
- Request only specific data types needed
- Explain how data will be used
- Provide value without health access
- Handle partial authorization

### Tracking (ATT)

**When to request:** Before tracking user across apps

**Required prompt:**
```swift
ATTrackingManager.requestTrackingAuthorization { status in
    switch status {
    case .authorized:
        // Enable tracking
    case .denied, .restricted:
        // Disable tracking
    case .notDetermined:
        // Request hasn't been shown yet
    }
}
```

**Best practices:**
- Explain value of personalized ads first
- Don't punish users who decline
- App must function without tracking

---

## Handling Denied Permissions

### Graceful Degradation

Always provide alternative paths when permission is denied.

| Permission Denied | Alternative |
|-------------------|-------------|
| Camera | Photo library option |
| Location | Manual address entry |
| Notifications | In-app message center |
| Contacts | Manual contact entry |
| Photos | Camera-only option |

### Re-Requesting After Denial

Once denied, system won't show prompt again. Guide users to Settings.

```swift
func openAppSettings() {
    guard let settingsUrl = URL(string: UIApplication.openSettingsURLString),
          UIApplication.shared.canOpenURL(settingsUrl) else {
        return
    }
    UIApplication.shared.open(settingsUrl)
}
```

**UI pattern:**
```
┌─────────────────────────────────────────┐
│                                         │
│         Camera Access Needed            │
│                                         │
│    To scan documents, allow camera      │
│    access in Settings.                  │
│                                         │
│    ┌─────────────────────────────────┐  │
│    │       Open Settings             │  │
│    └─────────────────────────────────┘  │
│                                         │
│           Not Now                       │
│                                         │
└─────────────────────────────────────────┘
```

### Don't Ask Again (Within Session)

If user taps "Maybe Later" on pre-permission screen, don't immediately ask again.

```swift
// Track dismissal
UserDefaults.standard.set(Date(), forKey: "camera_prompt_dismissed")

// Wait before showing again
func shouldShowCameraPrompt() -> Bool {
    guard let lastDismissed = UserDefaults.standard.object(
        forKey: "camera_prompt_dismissed"
    ) as? Date else {
        return true
    }
    // Wait at least 3 days
    return Date().timeIntervalSince(lastDismissed) > 3 * 24 * 60 * 60
}
```

---

## Privacy UI Patterns

### Permission Status Indicators

Show current permission state in settings:

```
┌─────────────────────────────────────────┐
│ Permissions                             │
├─────────────────────────────────────────┤
│ 📷 Camera                  Allowed    ▶ │
│ 📍 Location                While Using▶ │
│ 🔔 Notifications           Off        ▶ │
│ 📱 Contacts                Not Asked  ▶ │
└─────────────────────────────────────────┘
```

### Data Usage Transparency

Explain what data is collected and why:

```
┌─────────────────────────────────────────┐
│ Privacy                                 │
├─────────────────────────────────────────┤
│                                         │
│ Data We Collect                         │
│                                         │
│ • Usage analytics                       │
│   To improve app performance            │
│                                         │
│ • Crash reports                         │
│   To fix bugs and issues                │
│                                         │
│ • Photos you upload                     │
│   Stored securely on our servers        │
│                                         │
│ [View Privacy Policy]                   │
│                                         │
└─────────────────────────────────────────┘
```

### Data Deletion Options

Provide clear data management:

```
┌─────────────────────────────────────────┐
│ Your Data                               │
├─────────────────────────────────────────┤
│ Download My Data                      ▶ │
│ Delete My Account                     ▶ │
└─────────────────────────────────────────┘
```

---

## App Privacy Labels

### Required Categories

Your App Store listing must declare:

**Data Used to Track You**
- Data used for advertising across apps

**Data Linked to You**
- Identifiable data (name, email, etc.)

**Data Not Linked to You**
- Anonymous analytics, crash data

### Best Practices

- Be accurate—Apple verifies
- Minimize collection to reduce label size
- Simpler labels build trust
- Update when collection changes

---

## Usage String Best Practices

### Structure

```
"[App name] [action] to [user benefit]."
```

### Examples by Permission

| Permission | Good Example |
|------------|--------------|
| Camera | "MyApp uses the camera to scan barcodes for quick product lookup." |
| Photos | "MyApp saves photos you create to your photo library." |
| Location | "MyApp uses your location to show nearby restaurants and estimated delivery times." |
| Microphone | "MyApp uses the microphone to record voice notes for your journal entries." |
| Contacts | "MyApp accesses contacts to help you split bills with friends." |

### What to Avoid

- Generic explanations ("to improve your experience")
- Technical jargon
- Mentioning advertising without explaining value
- Being vague about data use

---

## Testing Permissions

### Reset Permissions

```bash
# Reset all permissions for specific app
xcrun simctl privacy booted reset all com.yourapp.bundleid

# Reset specific permission
xcrun simctl privacy booted reset camera com.yourapp.bundleid
```

### Test All States

For each permission:
1. Never requested (first launch)
2. Authorized
3. Denied
4. Restricted (parental controls)
5. Limited (Photos)
6. Provisional (Notifications)

### Automated Testing

```swift
func testCameraPermissionDenied() {
    // Set up mock authorization status
    mockCameraAuthorization = .denied

    // Trigger camera feature
    app.buttons["Take Photo"].tap()

    // Verify fallback UI appears
    XCTAssertTrue(app.staticTexts["Camera access needed"].exists)
    XCTAssertTrue(app.buttons["Open Settings"].exists)
}
```
