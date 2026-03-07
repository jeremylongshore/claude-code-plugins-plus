# Build Troubleshooting

Dependency resolution for CocoaPods and Swift Package Manager conflicts.

**When to use**: Dependency conflicts, CocoaPods/SPM resolution failures, "Multiple commands produce" errors, framework version mismatches

## Key Features

- CocoaPods conflict resolution
- SPM version resolution
- Multiple commands produce errors
- Framework version mismatches
- Clean build strategies

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I added a Swift Package but I'm getting 'No such module' errors even though it's in my project."**
  → Covers SPM resolution workflows, package cache clearing, and framework search path diagnostics

- **"The build is failing with 'Multiple commands produce' the same output file."**
  → Shows how to identify duplicate target membership and resolve file conflicts

- **"CocoaPods installed successfully but the build still fails."**
  → Covers Podfile.lock conflict resolution, linking errors, and version constraint debugging

- **"My build works on my Mac but fails on the CI server."**
  → Explains dependency caching differences, environment-specific paths, and reproducible build strategies

- **"I'm getting framework version conflicts and don't know which dependency is causing it."**
  → Demonstrates dependency graph analysis and version constraint resolution
