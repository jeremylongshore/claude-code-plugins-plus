---
name: uikit-animation-debugging
description: Use when CAAnimation completion handler doesn't fire, spring physics look wrong on device, animation duration mismatches actual time, gesture + animation interaction causes jank, or timing differs between simulator and real hardware - systematic CAAnimation diagnosis with CATransaction patterns, frame rate awareness, and device-specific behavior
---

# UIKit Animation Debugging

## Overview

CAAnimation issues manifest as missing completion handlers, wrong timing, or jank under specific conditions. **Core principle:** 90% of CAAnimation problems are CATransaction timing, layer state, or frame rate assumptions, not Core Animation bugs.

## Red Flags — Suspect CAAnimation Issue

If you see ANY of these, suspect animation logic not device behavior:
- Completion handler fires on simulator but not device
- Animation duration (0.5s) doesn't match visual duration (1.2s)
- Spring animation looks correct on iPhone 15 Pro but janky on older devices
- Gesture + animation together causes stuttering (fine separately)
- `[weak self]` in completion handler and you're not sure why
- ❌ **FORBIDDEN:** Hardcoding duration/values to "match what actually happens"
  - This ships device-specific bugs to users on different hardware
  - Do not rationalize this as a "temporary fix" or "good enough"

**Critical distinction:** Simulator often hides timing issues (60Hz only, no throttling). Real devices expose them (variable frame rate, CPU throttling, background pressure). **MANDATORY: Test on real device (oldest supported model) before shipping.**

## Mandatory First Steps

**ALWAYS run these FIRST** (before changing code):

```swift
// 1. Check if completion is firing at all
animation.completion = { [weak self] finished in
    print("🔥 COMPLETION FIRED: finished=\(finished)")
    guard let self = self else {
        print("🔥 SELF WAS NIL")
        return
    }
    // original code
}

// 2. Check actual duration vs declared
let startTime = Date()
let anim = CABasicAnimation(keyPath: "position.x")
anim.duration = 0.5  // Declared
layer.add(anim, forKey: "test")

DispatchQueue.main.asyncAfter(deadline: .now() + 0.51) {
    print("Elapsed: \(Date().timeIntervalSince(startTime))")  // Actual
}

// 3. Check what animations are active
if let keys = layer.animationKeys() {
    print("Active animations: \(keys)")
    for key in keys {
        if let anim = layer.animation(forKey: key) {
            print("\(key): duration=\(anim.duration), removed=\(anim.isRemovedOnCompletion)")
        }
    }
}

// 4. Check layer state
print("Layer speed: \(layer.speed)")  // != 1.0 means timing is scaled
print("Layer timeOffset: \(layer.timeOffset)")  // != 0 means animation is offset
```

**What this tells you:**
- **Completion print appears** → Handler fires, issue is in callback code
- **Completion print missing** → Handler not firing, check CATransaction/layer state
- **Elapsed time == declared** → Duration is correct, visual jank is from frames
- **Elapsed time != declared** → CATransaction wrapping is changing duration
- **layer.speed != 1.0** → Something is slowing animation
- **Active animations list is long** → Multiple animations competing

**MANDATORY INTERPRETATION:**

Before changing ANY code, you must identify which ONE diagnostic is the root cause:

1. If completion fires but elapsed time != declared duration → Apply Pattern 2 (CATransaction)
2. If completion doesn't fire AND isRemovedOnCompletion is true → Apply Pattern 3
3. If completion fires but visual is janky → **MUST profile with Instruments first**
   - You cannot guess "it's probably frames" - prove it with data
   - Profile > Core Animation instrument shows frame drops with certainty
   - If you skip Instruments, you're guessing

**If diagnostics are contradictory or unclear:**
- STOP. Do NOT proceed to patterns yet
- Add more print statements to narrow the cause
- Ask: "The diagnostics show X and Y but Z doesn't match. What am I missing?"
- Profile with Instruments > Core Animation if unsure

## Decision Tree

```
CAAnimation problem?
├─ Completion handler never fires?
│  ├─ On simulator only?
│  │  └─ Simulator timing is different (60Hz). Test on real device.
│  ├─ On real device only?
│  │  ├─ Check: isRemovedOnCompletion and fillMode
│  │  ├─ Check: CATransaction wrapping
│  │  └─ Check: app goes to background during animation
│  └─ On both simulator and device?
│     ├─ Check: completion handler is set BEFORE adding animation
│     └─ Check: [weak self] is actually captured (not nil before completion)
│
├─ Duration mismatch (declared != visual)?
│  ├─ Is layer.speed != 1.0?
│  │  └─ Something scaled animation duration. Find and fix.
│  ├─ Is animation wrapped in CATransaction?
│  │  └─ CATransaction.setAnimationDuration() overrides animation.duration
│  └─ Is visual duration LONGER than declared?
│     └─ Simulator (60Hz) vs device frame rate (120Hz). Recalculate for real hardware.
│
├─ Spring physics wrong on device?
│  ├─ Are values hardcoded for one device?
│  │  └─ Use device performance class, not model
│  ├─ Are damping/stiffness values swapped with mass/stiffness?
│  │  └─ Check CASpringAnimation parameter meanings
│  └─ Does it work on simulator but not device?
│     └─ Simulator uses 60Hz. Device may use 120Hz. Recalculate.
│
└─ Gesture + animation jank?
   ├─ Are animations competing (same keyPath)?
   │  └─ Remove old animation before adding new
   ├─ Is gesture updating layer while animation runs?
   │  └─ Use CADisplayLink for synchronized updates
   └─ Is gesture blocking the main thread?
      └─ Profile with Instruments > Core Animation
```

## Common Patterns

### Pattern Selection Rules (MANDATORY)

**Apply ONE pattern at a time, in this order:**

1. **Always start with Pattern 1** (Completion Handler Basics)
   - If completion NEVER fires → Pattern 1
   - Verify completion is set BEFORE add() with print statement (line 33)
   - Only proceed to Pattern 2 if completion FIRES but timing is wrong

2. **Then Pattern 2** (CATransaction duration mismatch)
   - Only if completion fires but elapsed time != declared duration
   - Check logs from Mandatory First Steps (line 40-47)

3. **Then Pattern 3** (isRemovedOnCompletion)
   - Only if animation completes but visual state reverts

4. **Patterns 4-7:** Apply based on specific symptom (see Decision Tree line 91+)

**FORBIDDEN:**
- ❌ Applying multiple patterns at once ("let me try Pattern 2 AND Pattern 4 together")
- ❌ Skipping Pattern 1 because "I already know it's not that"
- ❌ Combining patterns without understanding why each is needed
- ❌ Trying patterns randomly and hoping one works

### Pattern 1: Completion Handler Basics

**❌ WRONG (Handler set AFTER adding animation):**
```swift
layer.add(animation, forKey: "myAnimation")
animation.completion = { finished in  // ❌ Too late!
    print("Done")
}
```

**✅ CORRECT (Handler set BEFORE adding):**
```swift
animation.completion = { [weak self] finished in
    print("🔥 Animation finished: \(finished)")
    guard let self = self else { return }
    self.doNextStep()
}
layer.add(animation, forKey: "myAnimation")
```

**Why:** Completion handler must be set before animation is added to layer. Setting after does nothing.

---

### Pattern 2: CATransaction vs animation.duration

**❌ WRONG (CATransaction overrides animation duration):**
```swift
CATransaction.begin()
CATransaction.setAnimationDuration(2.0)  // ❌ Overrides all animations!
let anim = CABasicAnimation(keyPath: "position")
anim.duration = 0.5  // This is ignored
layer.add(anim, forKey: nil)
CATransaction.commit()  // Animation takes 2.0 seconds, not 0.5
```

**✅ CORRECT (Set duration on animation, not transaction):**
```swift
let anim = CABasicAnimation(keyPath: "position")
anim.duration = 0.5
layer.add(anim, forKey: nil)
// No CATransaction wrapping
```

**Why:** CATransaction.setAnimationDuration() affects ALL animations in the transaction block. Use it only if you want to change all animations uniformly.

---

### Pattern 3: isRemovedOnCompletion & fillMode

**❌ WRONG (Animation disappears after completion):**
```swift
let anim = CABasicAnimation(keyPath: "opacity")
anim.fromValue = 1.0
anim.toValue = 0.0
anim.duration = 0.5
layer.add(anim, forKey: nil)
// After 0.5s, animation is removed AND layer reverts to original state
```

**✅ CORRECT (Keep animation state):**
```swift
anim.isRemovedOnCompletion = false
anim.fillMode = .forwards  // Keep final state after animation
layer.add(anim, forKey: nil)
// After 0.5s, animation state is preserved
```

**Why:** By default, animations are removed and layer reverts. For permanent state changes, set `isRemovedOnCompletion = false` and `fillMode = .forwards`.

---

### Pattern 4: Weak Self in Completion (MANDATORY)

**❌ FORBIDDEN (Strong self creates retain cycle):**
```swift
anim.completion = { finished in
    self.property = "value"  // ❌ GUARANTEED retain cycle
}
```

**✅ MANDATORY (Always use weak self):**
```swift
anim.completion = { [weak self] finished in
    guard let self = self else { return }
    self.property = "value"  // Safe to access
}
```

**Why this is MANDATORY, not optional:**
- CAAnimation keeps completion handler alive until animation completes
- Completion handler captures self strongly (unless explicitly weak)
- Creates retain cycle: self → animation → completion → self
- Memory leak occurs even if animation is short-lived (0.3s doesn't prevent it)

**FORBIDDEN rationalizations:**
- ❌ "Animation is short, so no retain cycle risk"
- ❌ "I'll remove the animation manually, so it's fine"
- ❌ "This code path only runs once"

**ALWAYS use [weak self] in completion handlers. No exceptions.**

---

### Pattern 5: Multiple Animations (Same keyPath)

**❌ WRONG (Animations conflict):**
```swift
// Add animation 1
let anim1 = CABasicAnimation(keyPath: "position.x")
anim1.toValue = 100
layer.add(anim1, forKey: "slide")

// Later, add animation 2
let anim2 = CABasicAnimation(keyPath: "position.x")
anim2.toValue = 200
layer.add(anim2, forKey: "slide")  // ❌ Same key, replaces anim1!
```

**✅ CORRECT (Remove before adding):**
```swift
layer.removeAnimation(forKey: "slide")  // Remove old first

let anim2 = CABasicAnimation(keyPath: "position.x")
anim2.toValue = 200
layer.add(anim2, forKey: "slide")
```

Or use unique keys:
```swift
let anim1 = CABasicAnimation(keyPath: "position.x")
layer.add(anim1, forKey: "slide_1")

let anim2 = CABasicAnimation(keyPath: "position.x")
layer.add(anim2, forKey: "slide_2")  // Different key
```

**Why:** Adding animation with same key replaces previous animation. Either remove old animation or use unique keys.

---

### Pattern 6: CADisplayLink for Gesture + Animation Sync

**❌ WRONG (Gesture updates directly, animation updates at different rate):**
```swift
func handlePan(_ gesture: UIPanGestureRecognizer) {
    let translation = gesture.translation(in: view)
    view.layer.position.x = translation.x  // ❌ Syncing issue
}

// Separately:
let anim = CABasicAnimation(keyPath: "position.x")
view.layer.add(anim, forKey: nil)  // Jank from desync
```

**✅ CORRECT (Use CADisplayLink for synchronization):**
```swift
var displayLink: CADisplayLink?

func startSyncedAnimation() {
    displayLink = CADisplayLink(
        target: self,
        selector: #selector(updateAnimation)
    )
    displayLink?.add(to: .main, forMode: .common)
}

@objc func updateAnimation() {
    // Update gesture AND animation in same frame
    let gesture = currentGesture
    let position = calculatePosition(from: gesture)
    layer.position = position  // Synchronized update
}
```

**Why:** Gesture recognizer and CAAnimation may run at different frame rates. CADisplayLink syncs both to screen refresh rate.

---

### Pattern 7: Spring Animation Device Differences

**❌ WRONG (Hardcoded for one device):**
```swift
let springAnim = CASpringAnimation()
springAnim.damping = 0.7  // Hardcoded for iPhone 15 Pro
springAnim.stiffness = 100
layer.add(springAnim, forKey: nil)  // Janky on iPhone 12
```

**✅ CORRECT (Adapt to device performance):**
```swift
let springAnim = CASpringAnimation()

// Use device performance class, not model
if ProcessInfo.processInfo.processorCount >= 6 {
    // Modern A-series (A14+)
    springAnim.damping = 0.7
    springAnim.stiffness = 100
} else {
    // Older A-series
    springAnim.damping = 0.85
    springAnim.stiffness = 80
}

layer.add(springAnim, forKey: nil)
```

**Why:** Spring physics feel different at 60Hz vs 120Hz. Use device class (core count, GPU) not model.

---

## Quick Reference Table

| Issue | Check | Fix |
|-------|-------|-----|
| Completion never fires | Set handler BEFORE `add()` | Move `completion =` before `add()` |
| Duration mismatch | Is CATransaction wrapping? | Remove CATransaction or remove animation from it |
| Jank on older devices | Is value hardcoded? | Use `ProcessInfo` for device class |
| Animation disappears | `isRemovedOnCompletion`? | Set to `false`, use `fillMode = .forwards` |
| Gesture + animation jank | Synced updates? | Use `CADisplayLink` |
| Multiple animations conflict | Same key? | Use unique keys or `removeAnimation()` first |
| Weak self in handler | Completion captured correctly? | Always use `[weak self]` in completion |

## When You're Stuck After 30 Minutes

If you've spent >30 minutes and the animation is still broken:

**STOP. You either:**
1. Skipped a mandatory step (most common)
2. Misinterpreted diagnostic output
3. Applied wrong pattern for your symptom
4. Are in the 5% edge case requiring Instruments profiling

**MANDATORY checklist before claiming "skill didn't work":**

- [ ] I ran ALL 4 diagnostic blocks from Mandatory First Steps (lines 28-63)
- [ ] I pasted the EXACT output of diagnostics (logs, print statements)
- [ ] I identified ONE root cause from "What this tells you" (lines 66-72)
- [ ] I applied the FIRST matching pattern from Decision Tree (lines 91+)
- [ ] I tested the pattern on a REAL device, not just simulator
- [ ] I verified the pattern with print statements/logs showing the fix worked

**If ALL boxes are checked and still broken:**
- You MUST profile with Instruments > Core Animation
- Time cost: 30-60 minutes (unavoidable for edge cases)
- Hardcoding, asyncAfter, or "shipping and hoping" are FORBIDDEN
- Ask for guidance before adding any workarounds

**Time cost transparency:**
- Pattern 1: 2-5 minutes
- Pattern 2: 3-5 minutes
- Instruments profiling: 30-60 minutes (for edge cases only)
- Trying random fixes without profiling: 2-4 hours + risk of shipping broken

## Common Mistakes

❌ **Setting completion handler AFTER adding animation**
- Completion is not set in time
- Fix: Set completion BEFORE `layer.add()`

❌ **Assuming simulator timing = device timing**
- Simulator runs 60Hz, devices run 60Hz-120Hz
- Fix: Test on real device before tuning duration

❌ **Hardcoding device-specific values**
- "This value works on iPhone 15 Pro" → fails on iPhone 12
- Fix: Use `ProcessInfo.processInfo.processorCount` or test class

❌ **Wrapping animation in CATransaction.setAnimationDuration()**
- Overrides all animation durations in that transaction
- Fix: Set duration on animation, not transaction

❌ **FORBIDDEN: Using strong self in completion handler**
- GUARANTEED retain cycle: self → animation → completion → self
- Fix: ALWAYS use `[weak self]` with guard

❌ **Not removing old animation before adding new**
- Same keyPath replaces previous animation
- Fix: `layer.removeAnimation(forKey:)` first or use unique keys

❌ **Ignoring layer.speed and layer.timeOffset**
- These scale animation timing invisibly
- Fix: Check these values if timing is wrong

## Real-World Impact

**Before:** CAAnimation debugging 2-4 hours per issue
- Print everywhere, test on simulator, hardcode values, ship and hope
- "Maybe it's a device bug?"
- DispatchQueue.asyncAfter as fallback timer

**After:** 15-30 minutes with systematic diagnosis
- Check completion handler setup (2 min)
- Check CATransaction wrapping (3 min)
- Check layer state and duration mismatch (5 min)
- Identify root cause, apply pattern (5 min)
- Test on real device (varies)

**Key insight:** CAAnimation issues are almost always CATransaction, layer state, or frame rate assumptions, never Core Animation bugs.

---

**Last Updated**: 2025-11-30
**Status**: TDD-tested with pressure scenarios
**Framework**: UIKit CAAnimation

