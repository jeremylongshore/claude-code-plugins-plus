# Xcode Debugging

Environment-first diagnostics for mysterious Xcode issues. Prevents 30+ minute rabbit holes by checking build environment before debugging code.

**When to use**: BUILD FAILED, test crashes, simulator hangs, stale builds, zombie xcodebuild processes, "Unable to boot simulator", "No such module" after SPM changes, mysterious test failures

## Key Features

- Mandatory environment checks (Derived Data, processes, simulators)
- Quick fix workflows for common issues
- Decision tree for diagnosing problems
- Crash log analysis patterns
- Time cost transparency (prevents rabbit holes)

**Philosophy**: 80% of "mysterious" Xcode issues are environment problems, not code bugs. Check environment BEFORE debugging code.

**TDD Tested**: 6 refinements from pressure testing with Superpowers framework

## Example Prompts

These are real questions developers ask that this skill answers:

- **"My build is failing with 'BUILD FAILED' but no error details. I haven't changed anything."**
  → Shows environment-first diagnostics: clean Derived Data, check simulator states, identify zombie processes

- **"Tests passed yesterday with no code changes, but now they're failing."**
  → Explains stale Derived Data and intermittent failures, shows the 2-5 minute fix

- **"My app builds fine but it's running the old code from before my changes."**
  → Demonstrates that Derived Data caches old builds, shows how deletion forces a clean rebuild

- **"The simulator says 'Unable to boot simulator' and I can't run tests."**
  → Covers simulator state diagnosis with simctl and safe recovery patterns

- **"I'm getting 'No such module: SomePackage' errors after updating SPM dependencies."**
  → Explains SPM caching issues and the clean Derived Data workflow
