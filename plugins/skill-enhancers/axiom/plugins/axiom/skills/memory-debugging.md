---
name: memory-debugging
description: Use when debugging retain cycles, memory leaks, crashes after 10+ minutes, or progressive memory growth from 50MB → 200MB - provides systematic diagnosis, Instruments patterns, and production-ready fixes for iOS/macOS apps under time pressure
---

# Memory Debugging

## Overview

Memory issues manifest as crashes after prolonged use. **Core principle:** 90% of memory leaks follow 3 patterns (retain cycles, timer/observer leaks, collection growth). Diagnose systematically with Instruments, never guess.

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "My app crashes after 10-15 minutes of use, but there are no error messages. How do I figure out what's leaking?"**
→ The skill covers systematic Instruments workflows to identify memory leaks vs normal memory pressure, with real diagnostic patterns

**2. "I'm seeing memory jump from 50MB to 200MB+ when I perform a specific action. Is this a leak or normal caching behavior?"**
→ The skill distinguishes between progressive leaks (continuous growth) and temporary spikes (caches that stabilize), with diagnostic criteria

**3. "View controllers don't seem to be deallocating after I dismiss them. How do I find the retain cycle causing this?"**
→ The skill demonstrates Memory Graph Debugger techniques to identify objects holding strong references and common retain cycle patterns

**4. "I have timers/observers in my code and I think they're causing memory leaks. How do I verify and fix this?"**
→ The skill covers the 5 diagnostic patterns, including specific timer and observer leak signatures with prevention strategies

**5. "My app uses 200MB of memory and I don't know if that's normal or if I have multiple leaks. How do I diagnose?"**
→ The skill provides the Instruments decision tree to distinguish normal memory use, expected caches, and actual leaks requiring fixes

---

## Red Flags - Memory Leak Likely

If you see ANY of these, suspect memory leak not just heavy memory use:

- Progressive memory growth: 50MB → 100MB → 200MB (not plateauing)
- App crashes after 10-15 minutes with no error in Xcode console
- Memory warnings appear repeatedly in device logs
- Specific screen/operation makes memory jump (10-50MB spike)
- View controllers don't deallocate after dismiss (visible in Memory Graph Debugger)
- Same operation run multiple times causes linear memory growth

**Difference from normal memory use:**
- Normal: App uses 100MB, stays at 100MB (memory pressure handled by iOS)
- Leak: App uses 50MB, becomes 100MB, 150MB, 200MB → CRASH

## Mandatory First Steps

**ALWAYS run these commands/checks FIRST** (before reading code):

```bash
# 1. Check device logs for memory warnings
# Connect device, open Xcode Console (Cmd+Shift+2)
# Trigger the crash scenario
# Look for: "Memory pressure critical", "Jetsam killed", "Low Memory"

# 2. Check which objects are leaking
# Use Memory Graph Debugger (below) - shows object count growth

# 3. Check instruments baseline
# Xcode → Product → Profile → Memory
# Run for 1 minute, note baseline
# Perform operation 5 times, note if memory keeps growing
```

**What this tells you:**
- **Memory stays flat** → Likely not a leak, check memory pressure handling
- **Memory grows linearly** → Classic leak (timer, observer, closure capture)
- **Sudden spikes then flattens** → Probably normal (caches, lazy loading)
- **Spikes AND keeps growing** → Compound leak (multiple leaks stacking)

**Why diagnostics first:**
- Finding leak with Instruments: 5-15 minutes
- Guessing and testing fixes: 45+ minutes

## Quick Decision Tree

```
Memory growing?
├─ Progressive growth every minute?
│  └─ Likely retain cycle or timer leak
├─ Spike when action performed?
│  └─ Check if operation runs multiple times
├─ Spike then flat for 30 seconds?
│  └─ Probably normal (collections, caches)
├─ Multiple large spikes stacking?
│  └─ Compound leak (multiple sources)
└─ Can't tell from visual inspection?
   └─ Use Instruments Memory Graph (see below)
```

## Detecting Leaks - Step by Step

### Step 1: Memory Graph Debugger (Fastest Leak Detection)

```
1. Open your app in Xcode simulator
2. Click: Debug → Memory Graph Debugger (or icon in top toolbar)
3. Wait for graph to generate (5-10 seconds)
4. Look for PURPLE/RED circles with "⚠" badge
5. Click them → Xcode shows retain cycle chain
```

**What you're looking for:**
```
✅ Object appears once
❌ Object appears 2+ times (means it's retained multiple times)
```

**Example output (indicates leak):**
```
PlayerViewModel
  ↑ strongRef from: progressTimer
    ↑ strongRef from: TimerClosure [weak self] captured self
      ↑ CYCLE DETECTED: This creates a retain cycle!
```

### Step 2: Instruments (Detailed Memory Analysis)

```
1. Product → Profile (Cmd+I)
2. Select "Memory" template
3. Run scenario that causes memory growth
4. Perform action 5-10 times
5. Check: Does memory line go UP for each action?
   - YES → Leak confirmed
   - NO → Probably not a leak
```

**Key instruments to check:**
- **Heap Allocations**: Shows object count
- **Leaked Objects**: Direct leak detection
- **VM Tracker**: Shows memory by type
- **System Memory**: Shows OS pressure

**How to read the graph:**
```
Time ──→
Memory
   │     ▗━━━━━━━━━━━━━━━━  ← Memory keeps growing (LEAK)
   │    ▄▀
   │   ▄▀
   │  ▄
   └─────────────────────
     Action 1  2  3  4  5

vs normal pattern:

Time ──→
Memory
   │  ▗━━━━━━━━━━━━━━━━━━  ← Memory plateaus (OK)
   │ ▄▀
   │▄
   └─────────────────────
     Action 1  2  3  4  5
```

### Step 3: View Controller Memory Check

For SwiftUI or UIKit view controllers:

```swift
// SwiftUI: Check if view disappears cleanly
@main
struct DebugApp: App {
    init() {
        NotificationCenter.default.addObserver(
            forName: NSNotification.Name("UIViewControllerWillDeallocate"),
            object: nil,
            queue: .main
        ) { _ in
            print("✅ ViewController deallocated")
        }
    }
    var body: some Scene { ... }
}

// UIKit: Add deinit logging
class MyViewController: UIViewController {
    deinit {
        print("✅ MyViewController deallocated")
    }
}

// SwiftUI: Use deinit in view models
@MainActor
class ViewModel: ObservableObject {
    deinit {
        print("✅ ViewModel deallocated")
    }
}
```

**Test procedure:**
```
1. Add deinit logging above
2. Launch app in Xcode
3. Navigate to view/create ViewModel
4. Navigate away/dismiss
5. Check Console: Do you see "✅ deallocated"?
   - YES → No leak there
   - NO → Object is retained somewhere
```

## Common Memory Leak Patterns (With Fixes)

### Pattern 1: Timer Leaks (Most Common)

**❌ Leak - Timer retains closure, closure retains self**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var currentTrack: Track?
    private var progressTimer: Timer?

    func startPlayback(_ track: Track) {
        currentTrack = track
        // LEAK: Timer.scheduledTimer captures 'self' in closure
        // Even with [weak self], the Timer itself is strong
        progressTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.updateProgress()
        }
        // Timer is never stopped → keeps firing forever
    }

    // Missing: Timer never invalidated
    deinit {
        // LEAK: If timer still running, deinit never called
    }
}
```

**Leak mechanism:**
```
ViewController → strongly retains ViewModel
               ↓
ViewModel → strongly retains Timer
           ↓
Timer → strongly retains closure
        ↓
Closure → captures [weak self] but still holds reference to Timer
```

**Closure captures `self` weakly BUT:**
- Timer is still strong reference in ViewModel
- Timer is still running (repeats: true)
- Even with [weak self], timer closure doesn't go away

**✅ Fix 1: Invalidate on deinit**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var currentTrack: Track?
    private var progressTimer: Timer?

    func startPlayback(_ track: Track) {
        currentTrack = track
        progressTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.updateProgress()
        }
    }

    func stopPlayback() {
        progressTimer?.invalidate()
        progressTimer = nil  // Important: nil after invalidate
        currentTrack = nil
    }

    deinit {
        progressTimer?.invalidate()  // ← CRITICAL FIX
        progressTimer = nil
    }
}
```

**✅ Fix 2: Use AnyCancellable (Modern approach)**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var currentTrack: Track?
    private var cancellable: AnyCancellable?

    func startPlayback(_ track: Track) {
        currentTrack = track

        // Timer with Combine - auto-cancels when cancellable is released
        cancellable = Timer.publish(
            every: 1.0,
            tolerance: 0.1,
            on: .main,
            in: .default
        )
        .autoconnect()
        .sink { [weak self] _ in
            self?.updateProgress()
        }
    }

    func stopPlayback() {
        cancellable?.cancel()  // Auto-cleans up
        cancellable = nil
        currentTrack = nil
    }

    // No need for deinit - Combine handles cleanup
}
```

**✅ Fix 3: Weak self + nil check (Emergency fix)**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var currentTrack: Track?
    private var progressTimer: Timer?

    func startPlayback(_ track: Track) {
        currentTrack = track

        // If progressTimer already exists, stop it first
        progressTimer?.invalidate()
        progressTimer = nil

        progressTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            guard let self = self else {
                // If self deallocated, timer still fires but does nothing
                // Still not ideal - timer keeps consuming CPU
                return
            }
            self.updateProgress()
        }
    }

    func stopPlayback() {
        progressTimer?.invalidate()
        progressTimer = nil
    }

    deinit {
        progressTimer?.invalidate()
        progressTimer = nil
    }
}
```

**Why the fixes work:**
- `invalidate()`: Stops timer immediately, breaks retain cycle
- `cancellable`: Automatically invalidates when released
- `[weak self]`: If ViewModel released before timer, timer becomes no-op
- `deinit cleanup`: Ensures timer always cleaned up

**Test the fix:**
```swift
func testPlayerViewModelNotLeaked() {
    var viewModel: PlayerViewModel? = PlayerViewModel()
    let track = Track(id: "1", title: "Song")
    viewModel?.startPlayback(track)

    // Verify timer running
    XCTAssertNotNil(viewModel?.progressTimer)

    // Stop and deallocate
    viewModel?.stopPlayback()
    viewModel = nil

    // ✅ Should deallocate without leak warning
}
```

### Pattern 2: Observer/Notification Leaks

**❌ Leak - Observer holds strong reference to self**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    init() {
        // LEAK: addObserver keeps strong reference to self
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleAudioSessionChange),
            name: AVAudioSession.routeChangeNotification,
            object: nil
        )
        // No matching removeObserver → accumulates listeners
    }

    @objc private func handleAudioSessionChange() { }

    deinit {
        // Missing: Never unregistered
    }
}
```

**✅ Fix 1: Manual cleanup in deinit**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    init() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleAudioSessionChange),
            name: AVAudioSession.routeChangeNotification,
            object: nil
        )
    }

    @objc private func handleAudioSessionChange() { }

    deinit {
        NotificationCenter.default.removeObserver(self)  // ← FIX
    }
}
```

**✅ Fix 2: Use modern Combine approach (Best practice)**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    private var cancellables = Set<AnyCancellable>()

    init() {
        NotificationCenter.default.publisher(
            for: AVAudioSession.routeChangeNotification
        )
        .sink { [weak self] _ in
            self?.handleAudioSessionChange()
        }
        .store(in: &cancellables)  // Auto-cleanup with viewModel
    }

    private func handleAudioSessionChange() { }

    // No deinit needed - cancellables auto-cleanup
}
```

**✅ Fix 3: Use @Published with map (Reactive)**
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var currentRoute: AVAudioSession.AudioSessionRouteDescription?
    private var cancellables = Set<AnyCancellable>()

    init() {
        NotificationCenter.default.publisher(
            for: AVAudioSession.routeChangeNotification
        )
        .map { _ in AVAudioSession.sharedInstance().currentRoute }
        .assign(to: &$currentRoute)  // Auto-cleanup with publisher chain
    }
}
```

### Pattern 3: Closure Capture Leaks (Collection/Array)

**❌ Leak - Closure captured in array, captures self**
```swift
@MainActor
class PlaylistViewController: UIViewController {
    private var tracks: [Track] = []
    private var updateCallbacks: [(Track) -> Void] = []  // LEAK SOURCE

    func addUpdateCallback() {
        // LEAK: Closure captures 'self'
        updateCallbacks.append { [self] track in
            self.refreshUI(with: track)  // Strong capture of self
        }
        // updateCallbacks grows and never cleared
    }

    // No mechanism to clear callbacks
    deinit {
        // updateCallbacks still references self
    }
}
```

**Leak mechanism:**
```
ViewController
  ↓ strongly owns
updateCallbacks array
  ↓ contains
Closure captures self
  ↓ CYCLE
Back to ViewController (can't deallocate)
```

**✅ Fix 1: Use weak self in closure**
```swift
@MainActor
class PlaylistViewController: UIViewController {
    private var tracks: [Track] = []
    private var updateCallbacks: [(Track) -> Void] = []

    func addUpdateCallback() {
        updateCallbacks.append { [weak self] track in
            self?.refreshUI(with: track)  // Weak capture
        }
    }

    deinit {
        updateCallbacks.removeAll()  // Clean up array
    }
}
```

**✅ Fix 2: Use unowned (when you're certain self lives longer)**
```swift
@MainActor
class PlaylistViewController: UIViewController {
    private var updateCallbacks: [(Track) -> Void] = []

    func addUpdateCallback() {
        updateCallbacks.append { [unowned self] track in
            self.refreshUI(with: track)  // Unowned is faster
        }
        // Use unowned ONLY if callback always destroyed before ViewController
    }

    deinit {
        updateCallbacks.removeAll()
    }
}
```

**✅ Fix 3: Cancel callbacks when done (Reactive)**
```swift
@MainActor
class PlaylistViewController: UIViewController {
    private var cancellables = Set<AnyCancellable>()

    func addUpdateCallback(_ handler: @escaping (Track) -> Void) {
        // Use PassthroughSubject instead of array
        Just(())
            .sink { [weak self] in
                handler(/* track */)
            }
            .store(in: &cancellables)
    }

    // When done:
    func clearCallbacks() {
        cancellables.removeAll()  // Cancels all subscriptions
    }
}
```

**Test the fix:**
```swift
func testCallbacksNotLeak() {
    var viewController: PlaylistViewController? = PlaylistViewController()
    viewController?.addUpdateCallback { _ in }

    // Verify callback registered
    XCTAssert(viewController?.updateCallbacks.count ?? 0 > 0)

    // Clear and deallocate
    viewController?.updateCallbacks.removeAll()
    viewController = nil

    // ✅ Should deallocate
}
```

### Pattern 4: Strong Reference Cycles (Closures + Properties)

**❌ Leak - Two objects strongly reference each other**
```swift
@MainActor
class Player: NSObject {
    var delegate: PlayerDelegate?  // Strong reference
    var onPlaybackEnd: (() -> Void)?  // ← Closure captures self

    init(delegate: PlayerDelegate) {
        self.delegate = delegate
        // LEAK CYCLE:
        // Player → (owns) → delegate
        // delegate → (through closure) → owns → Player
    }
}

class PlaylistController: PlayerDelegate {
    var player: Player?

    override init() {
        super.init()
        self.player = Player(delegate: self)  // Self-reference cycle

        player?.onPlaybackEnd = { [self] in
            // LEAK: Closure captures self
            // self owns player
            // player owns delegate (self)
            // Cycle!
            self.playNextTrack()
        }
    }
}
```

**✅ Fix: Break cycle with weak self**
```swift
@MainActor
class PlaylistController: PlayerDelegate {
    var player: Player?

    override init() {
        super.init()
        self.player = Player(delegate: self)

        player?.onPlaybackEnd = { [weak self] in
            // Weak self breaks the cycle
            self?.playNextTrack()
        }
    }

    deinit {
        player?.onPlaybackEnd = nil  // Optional cleanup
        player = nil
    }
}
```

### Pattern 5: View/Layout Callback Leaks

**❌ Leak - View layout callback retains view controller**
```swift
@MainActor
class DetailViewController: UIViewController {
    let customView = UIView()

    override func viewDidLoad() {
        super.viewDidLoad()

        // LEAK: layoutIfNeeded closure captures self
        customView.layoutIfNeeded = { [self] in
            // Every layout triggers this, keeping self alive
            self.updateLayout()
        }
    }
}
```

**✅ Fix: Use @IBAction or proper delegation pattern**
```swift
@MainActor
class DetailViewController: UIViewController {
    @IBOutlet weak var customView: CustomView!

    override func viewDidLoad() {
        super.viewDidLoad()
        customView.delegate = self  // Weak reference through protocol
    }

    deinit {
        customView?.delegate = nil  // Clean up
    }
}

protocol CustomViewDelegate: AnyObject {  // AnyObject = weak by default
    func customViewDidLayout(_ view: CustomView)
}
```

### Pattern 6: PhotoKit Image Request Leaks

**❌ Leak - PHImageManager requests accumulate without cancellation**

This pattern is specific to photo/media apps using PhotoKit or similar async image loading APIs.

```swift
// LEAK: Image requests not cancelled when cells scroll away
class PhotoViewController: UIViewController {
    let imageManager = PHImageManager.default()

    func collectionView(_ collectionView: UICollectionView,
                       cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        let cell = collectionView.dequeueReusableCell(withReuseIdentifier: "cell", for: indexPath)
        let asset = photos[indexPath.item]

        // LEAK: Requests accumulate - never cancelled
        imageManager.requestImage(
            for: asset,
            targetSize: thumbnailSize,
            contentMode: .aspectFill,
            options: nil
        ) { [weak self] image, _ in
            cell.imageView.image = image  // Still called even if cell scrolled away
        }

        return cell
    }

    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        // Each scroll triggers 50+ new image requests
        // Previous requests still pending, accumulating in queue
    }
}
```

**Symptoms:**
- Memory jumps 50MB+ when scrolling long photo lists
- Crashes happen after scrolling through 100+ photos
- Specific operation causes leak (photo scrolling, not other screens)
- Works fine locally with 10 photos, crashes on user devices with 1000+ photos

**Root cause:** `PHImageManager.requestImage()` returns a `PHImageRequestID` that must be explicitly cancelled. Without cancellation, pending requests queue up and hold memory.

**✅ Fix: Store request ID and cancel in prepareForReuse()**

```swift
class PhotoCell: UICollectionViewCell {
    @IBOutlet weak var imageView: UIImageView!
    private var imageRequestID: PHImageRequestID = PHInvalidImageRequestID

    func configure(with asset: PHAsset, imageManager: PHImageManager) {
        // Cancel previous request before starting new one
        if imageRequestID != PHInvalidImageRequestID {
            imageManager.cancelImageRequest(imageRequestID)
        }

        imageRequestID = imageManager.requestImage(
            for: asset,
            targetSize: PHImageManagerMaximumSize,
            contentMode: .aspectFill,
            options: nil
        ) { [weak self] image, _ in
            self?.imageView.image = image
        }
    }

    override func prepareForReuse() {
        super.prepareForReuse()

        // CRITICAL: Cancel pending request when cell is reused
        if imageRequestID != PHInvalidImageRequestID {
            PHImageManager.default().cancelImageRequest(imageRequestID)
            imageRequestID = PHInvalidImageRequestID
        }

        imageView.image = nil  // Clear stale image
    }

    deinit {
        // Safety check - shouldn't be needed if prepareForReuse called
        if imageRequestID != PHInvalidImageRequestID {
            PHImageManager.default().cancelImageRequest(imageRequestID)
        }
    }
}

// Controller
class PhotoViewController: UIViewController, UICollectionViewDataSource {
    let imageManager = PHImageManager.default()

    func collectionView(_ collectionView: UICollectionView,
                       cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        let cell = collectionView.dequeueReusableCell(withReuseIdentifier: "PhotoCell",
                                                      for: indexPath) as! PhotoCell
        let asset = photos[indexPath.item]
        cell.configure(with: asset, imageManager: imageManager)
        return cell
    }
}
```

**Key points:**
- Store `PHImageRequestID` in cell (not in view controller)
- Cancel BEFORE starting new request (prevents request storms)
- Cancel in `prepareForReuse()` (critical for collection views)
- Check `imageRequestID != PHInvalidImageRequestID` before cancelling

**Other async APIs with similar patterns:**
- `AVAssetImageGenerator.generateCGImagesAsynchronously()` → call `cancelAllCGImageGeneration()`
- `URLSession.dataTask()` → call `cancel()` on task
- Custom image caches → implement `invalidate()` or `cancel()` method

## Debugging Non-Reproducible Memory Issues

**Challenge:** Memory leak only happens with specific user data (large photo collections, complex data models) that you can't reproduce locally.

### Step 1: Enable Remote Memory Diagnostics

Add MetricKit diagnostics to your app:

```swift
import MetricKit

class MemoryDiagnosticsManager {
    static let shared = MemoryDiagnosticsManager()

    private let metricManager = MXMetricManager.shared

    func startMonitoring() {
        metricManager.add(self)
    }
}

extension MemoryDiagnosticsManager: MXMetricManagerSubscriber {
    func didReceive(_ payloads: [MXMetricPayload]) {
        for payload in payloads {
            if let memoryMetrics = payload.memoryMetrics {
                let peakMemory = memoryMetrics.peakMemoryUsage

                // Log if exceeding threshold
                if peakMemory > 400_000_000 {  // 400MB
                    print("⚠️ High memory: \(peakMemory / 1_000_000)MB")
                    // Send to analytics
                }
            }
        }
    }
}
```

### Step 2: Ask Users for Device Logs

When user reports crash:

1. iPhone → Settings → Privacy & Security → Analytics → Analytics Data
2. Look for latest crash log (named like `YourApp_2024-01-15-12-45-23`)
3. Email or upload to your support system
4. Xcode → Window → Devices & Simulators → select device → View Device Logs
5. Search for "Memory" or "Jetsam" in logs

### Step 3: TestFlight Beta Testing

Before App Store release:

```swift
#if DEBUG
// Add to AppDelegate
import os.log
let logger = os.log(subsystem: "com.yourapp.memory", category: "lifecycle")

// Log memory milestones
func logMemory(_ event: String) {
    let memoryUsage = ProcessInfo.processInfo.physicalMemory / 1_000_000
    os.log("🔍 [%s] Memory: %dMB", log: logger, type: .info, event, memoryUsage)
}
#endif
```

Send TestFlight build to affected users:
1. Build → Archive → Distribute App
2. Select TestFlight
3. Add affected user email
4. In TestFlight, ask user to:
   - Reproduce the crash scenario
   - Check if memory stabilizes (logs to system.log)
   - Report if crash still happens

### Step 4: Verify Fix Production Deployment

After deploying fix:

1. Monitor MetricKit metrics for 24-48 hours
2. Check crash rate drop in App Analytics
3. If still seeing high memory users:
   - Add more diagnostic logging for next version
   - Consider lower memory device testing (iPad with constrained memory)

## Systematic Debugging Workflow

### Phase 1: Confirm Leak (5 minutes)

```
1. Open app in simulator
2. Xcode → Product → Profile → Memory
3. Record baseline memory
4. Repeat action 10 times
5. Check memory graph:
   - Flat line = NOT a leak (stop here)
   - Steady climb = LEAK (go to Phase 2)
```

### Phase 2: Locate Leak (10-15 minutes)

```
1. Close Instruments
2. Xcode → Debug → Memory Graph Debugger
3. Wait for graph (5-10 sec)
4. Look for purple/red circles with ⚠
5. Click on leaked object
6. Read the retain cycle chain:
   PlayerViewModel (leak)
     ↑ retained by progressTimer
       ↑ retained by TimerClosure
         ↑ retained by [self] capture
```

**Common leak locations (in order of likelihood):**
- Timers (50% of leaks)
- Notifications/KVO (25%)
- Closures in arrays/collections (15%)
- Delegate cycles (10%)

### Phase 3: Test Hypothesis (5 minutes)

Apply fix from "Common Patterns" section above, then:

```swift
// Add deinit logging
class PlayerViewModel: ObservableObject {
    deinit {
        print("✅ PlayerViewModel deallocated - leak fixed!")
    }
}
```

Run in Xcode, perform operation, check console for dealloc message.

### Phase 4: Verify Fix with Instruments (5 minutes)

```
1. Product → Profile → Memory
2. Repeat action 10 times
3. Confirm: Memory stays flat (not climbing)
4. If climbing continues, go back to Phase 2 (second leak)
```

## Compound Leaks (Multiple Sources)

Real apps often have 2-3 leaks stacking:

```
Leak 1: Timer in PlayerViewModel (+10MB/minute)
Leak 2: Observer in delegate (+5MB/minute)
Result: +15MB/minute → Crashes in 13 minutes
```

**How to find compound leaks:**

```
1. Fix obvious leak (Timer)
2. Run Instruments again
3. If memory STILL growing, there's a second leak
4. Repeat Phase 1-3 for each leak
5. Test each fix in isolation (revert one, test another)
```

## Memory Leak Detection - Testing Checklist

```swift
// Pattern 1: Verify object deallocates
@Test func viewModelDeallocates() {
    var vm: PlayerViewModel? = PlayerViewModel()
    vm?.startPlayback(Track(id: "1", title: "Test"))

    // Cleanup
    vm?.stopPlayback()
    vm = nil

    // If no crash, object deallocated
}

// Pattern 2: Verify timer stops
@Test func timerStopsOnDeinit() {
    var vm: PlayerViewModel? = PlayerViewModel()
    let startCount = Timer.activeCount()

    vm?.startPlayback(Track(id: "1", title: "Test"))
    XCTAssertGreater(Timer.activeCount(), startCount)

    vm?.stopPlayback()
    vm = nil

    XCTAssertEqual(Timer.activeCount(), startCount)
}

// Pattern 3: Verify observer unregistered
@Test func observerRemovedOnDeinit() {
    var vc: DetailViewController? = DetailViewController()
    let startCount = NotificationCenter.default.observers().count

    // Perform action that adds observer
    _ = vc

    vc = nil
    XCTAssertEqual(NotificationCenter.default.observers().count, startCount)
}

// Pattern 4: Memory stability over time
@Test func memoryStableAfterRepeatedActions() {
    let vm = PlayerViewModel()

    var measurements: [UInt] = []
    for _ in 0..<10 {
        vm.startPlayback(Track(id: "1", title: "Test"))
        vm.stopPlayback()

        let memory = ProcessInfo.processInfo.physicalMemory
        measurements.append(memory)
    }

    // Check last 5 measurements are within 10% of each other
    let last5 = Array(measurements.dropFirst(5))
    let average = last5.reduce(0, +) / UInt(last5.count)

    for measurement in last5 {
        XCTAssertLessThan(
            abs(Int(measurement) - Int(average)),
            Int(average / 10)  // 10% tolerance
        )
    }
}
```

## Command Line Tools for Memory Debugging

```bash
# Monitor memory in real-time
# Connect device, then:
xcrun xctrace record --template "Memory" --output memory.trace

# Analyze with command line
xcrun xctrace dump memory.trace

# Check for leaked objects
instruments -t "Leaks" -a YourApp -p 1234

# Memory pressure simulator
xcrun simctl spawn booted launchctl list | grep memory

# Check malloc statistics
leaks -atExit -excludeNoise YourApp
```

## Common Mistakes

❌ **Using [weak self] but never calling invalidate()**
- Weak self prevents immediate crash but doesn't stop timer
- Timer keeps running and consuming CPU/battery
- ALWAYS call `invalidate()` or `cancel()` on timers/subscribers

❌ **Invalidating timer but keeping strong reference**
```swift
// ❌ Wrong
timer?.invalidate()  // Stops firing but timer still referenced
// ❌ Should be:
timer?.invalidate()
timer = nil  // Release the reference
```

❌ **Assuming AnyCancellable auto-cleanup is automatic**
```swift
// ❌ Wrong - if cancellable goes out of scope, subscription ends immediately
func setupListener() {
    let cancellable = NotificationCenter.default
        .publisher(for: .myNotification)
        .sink { _ in }
    // cancellable is local, goes out of scope immediately
    // Subscription dies before any notifications arrive
}

// ✅ Right - store in property
@MainActor
class MyClass: ObservableObject {
    private var cancellables = Set<AnyCancellable>()

    func setupListener() {
        NotificationCenter.default
            .publisher(for: .myNotification)
            .sink { _ in }
            .store(in: &cancellables)  // Stored as property
    }
}
```

❌ **Not testing the fix**
- Apply fix → Assume it's correct → Deploy
- ALWAYS run Instruments after fix to confirm memory flat

❌ **Fixing the wrong leak first**
- Multiple leaks = fix largest first (biggest memory impact)
- Use Memory Graph to identify what's actually leaking

❌ **Adding deinit with only logging, no cleanup**
```swift
// ❌ Wrong - just logs, doesn't clean up
deinit {
    print("ViewModel deallocating")  // Doesn't stop timer!
}

// ✅ Right - actually stops the leak
deinit {
    timer?.invalidate()
    timer = nil
    NotificationCenter.default.removeObserver(self)
}
```

❌ **Using Instruments Memory template instead of Leaks**
- Memory template: Shows memory usage (not leaks)
- Leaks template: Detects actual leaks
- Use both: Memory for trend, Leaks for detection

## Instruments Quick Reference

| Scenario | Tool | What to Look For |
|----------|------|------------------|
| Progressive memory growth | Memory | Line steadily climbing = leak |
| Specific object leaking | Memory Graph | Purple/red circles = leak objects |
| Direct leak detection | Leaks | Red "! Leak" badge = confirmed leak |
| Memory by type | VM Tracker | Find objects consuming most memory |
| Cache behavior | Allocations | Find objects allocated but not freed |

## Real-World Impact

**Before:** 50+ PlayerViewModel instances created/destroyed
- Each uncleared timer fires every second
- Memory: 50MB → 100MB (1min) → 200MB (2min) → Crash (13min)
- Developer spends 2+ hours debugging

**After:** Timer properly invalidated in all view models
- One instance created/destroyed = memory flat
- No timer accumulation
- Memory: 50MB → 50MB → 50MB (stable for hours)

**Key insight:** 90% of leaks come from forgetting to stop timers, observers, or subscriptions. Always clean up in `deinit` or use reactive patterns that auto-cleanup.

---

**Last Updated**: 2025-11-28
**Frameworks**: UIKit, SwiftUI, Combine, Foundation
**Status**: Production-ready patterns for leak detection and prevention
