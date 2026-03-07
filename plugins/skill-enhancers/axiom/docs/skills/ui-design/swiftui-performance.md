# SwiftUI Performance

Master SwiftUI performance optimization using the new SwiftUI Instrument in Instruments 26.

**When to use**: App feels less responsive, animations stutter, scrolling performance issues, profiling reveals SwiftUI bottlenecks

## Key Features

- **New SwiftUI Instrument walkthrough** – 4 track lanes, color-coding system, integration with Time Profiler
- **Cause & Effect Graph** – Visualize data flow and dependencies to eliminate unnecessary updates
- **Problem 1: Long View Body Updates**
  - Identifying long updates with Instruments
  - Time Profiler integration for finding bottlenecks
  - Common expensive operations (formatter creation, calculations, I/O, image processing)
  - Verification workflows
- **Problem 2: Unnecessary View Updates**
  - AttributeGraph and dependency tracking
  - Granular dependencies with per-item view models
  - Environment updates performance implications
- **Performance Optimization Checklist** – Systematic approach from profiling setup through verification
- Real-world impact examples from WWDC's Landmarks app

**Requirements**: Xcode 26+, iOS 26+ SDK for profiling

## WWDC References

- [Optimize SwiftUI performance with Instruments – Session 306](https://developer.apple.com/videos/play/wwdc2025/306/)

**Philosophy**: Ensure your view bodies update quickly and only when needed to achieve great SwiftUI performance.

## Example Prompts

These are real questions developers ask that this skill answers:

- **"My app has janky scrolling and animations stutter."**
  → Shows how to use the new SwiftUI Instrument to identify if SwiftUI is the bottleneck

- **"I see orange/red bars in the SwiftUI Instrument showing long updates."**
  → Covers Cause & Effect Graph patterns that show data flow and which state changes trigger expensive updates

- **"Some views are updating way too often even though their data hasn't changed."**
  → Demonstrates unnecessary update detection and Identity troubleshooting with visual timeline

- **"I have large data structures and complex view hierarchies."**
  → Covers performance patterns: breaking down hierarchies, minimizing body complexity, @Sendable optimization

- **"We have a performance deadline. What's slow in SwiftUI?"**
  → Provides decision tree for prioritizing optimizations with professional guidance for trade-offs
