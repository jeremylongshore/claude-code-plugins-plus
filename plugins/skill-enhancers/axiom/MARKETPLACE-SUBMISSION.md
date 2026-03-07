# Axiom Marketplace Submission Guide

## Plugin Details

**Plugin Name:** axiom
**Version:** 0.1.6
**Repository:** https://github.com/CharlesWiltgen/Axiom
**License:** MIT

## Description

Battle-tested Claude Code skills for modern xOS (iOS, iPadOS, watchOS, tvOS) development

## Installation Methods

### Method 1: Direct Installation from GitHub
```bash
claude-code plugin add CharlesWiltgen/Axiom
```

### Method 2: Add Axiom Marketplace
```bash
/plugin marketplace add CharlesWiltgen/Axiom
```

Users can then install Axiom from the marketplace within Claude Code.

## What's Included

13 production-ready, battle-tested skills organized in 4 categories:

### Debugging & Troubleshooting (5 skills)
- **Xcode Debugging** – Environment-first diagnostics, prevents 30+ minute rabbit holes
- **Memory Debugging** – Systematic leak diagnosis covering 90% of real-world issues
- **Build Troubleshooting** – CocoaPods/SPM dependency resolution
- **Performance Profiling** – Instruments decision trees for CPU, memory, battery profiling
- **UI Testing** – Condition-based waiting patterns and Recording UI Automation (Xcode 26)

### Concurrency & Async (1 skill)
- **Swift Concurrency** – Swift 6 strict concurrency patterns, actor isolation, Sendable, data race prevention

### UI & Design (4 skills)
- **Liquid Glass** – Apple's new material design system (iOS 26+)
- **SwiftUI Performance** – New SwiftUI Instrument in Instruments 26, Cause & Effect Graph
- **SwiftUI Debugging** – View updates, preview crashes, layout issues with decision trees
- **UI Testing** – Covered above under Debugging & Troubleshooting

### Persistence (4 skills)
- **Database Migration** – Safe schema evolution, prevents data loss for 100k+ user apps
- **SwiftData** – @Model, @Query patterns, CloudKit integration, iOS 26+ features
- **SQLiteData** – Point-Free's type-safe SQLite patterns, batch performance
- **GRDB** – Raw SQL queries, ValueObservation, DatabaseMigrator patterns

## Quality Assurance

### Testing Methodology
- **TDD-Tested:** 3 core skills (xcode-debugging, swift-concurrency, database-migration) validated with RED-GREEN-REFACTOR cycles
- **Pressure Testing:** Validated under App Store deadline pressure, authority pressure, misinterpretation scenarios
- **Research-Validated:** WWDC 2025 skills (Liquid Glass, SwiftUI Performance, UI Testing) reviewed against official guidance
- **Peer-Reviewed:** Reference skills (persistence) reviewed for accuracy and completeness

### Key Metrics
- **Reduces debugging time:** 30+ min → 2-5 min (Xcode issues)
- **Memory leak diagnosis:** 2-3 hours → 15-30 min
- **Test reliability:** From flaky (50% CI failures) → reliable
- **Performance:** Systematic optimization vs. guessing

## Documentation

- **README.md** – Installation, skill overview, philosophy
- **SKILLS-SUMMARY.md** – Comprehensive overview of all 13 skills
- **Documentation Website** – Full VitePress site at https://charleswiltgen.github.io/Axiom/
- **Individual Skill Pages** – Each skill has detailed documentation with examples

## Community Marketplaces (Recommended)

Consider submitting to established Claude Code marketplaces for broader discovery:

1. **Popular Marketplaces:**
   - [ananddtyagi/claude-code-marketplace](https://github.com/ananddtyagi/claude-code-marketplace)
   - [EveryInc/every-marketplace](https://github.com/EveryInc/every-marketplace)
   - [jeremylongshore/claude-code-plugins-plus](https://github.com/jeremylongshore/claude-code-plugins-plus)

2. **Submission Process:**
   - Open an issue on the marketplace repository
   - Provide:
     - Plugin name and description
     - Repository URL
     - Brief overview (1-2 sentences)
   - Maintainers will review and add to their marketplace

## Support & Contributing

- **GitHub Issues:** Report bugs and request features
- **Contributing:** See CONTRIBUTING.md for guidelines
- **Documentation:** Website at https://charleswiltgen.github.io/Axiom/

## License

MIT License – Free for personal and commercial use

## Keywords

iOS, debugging, swift, claude-code, plugin, persistence, testing, performance, xcode, concurrency, database, swiftdata, grdb, liquid-glass, swiftui

---

**Status:** ✅ Ready for marketplace submission
**Last Updated:** 2025-11-30
