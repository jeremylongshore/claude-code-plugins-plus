# Memory Debugging

Systematic memory leak diagnosis with Instruments. 5 leak patterns covering 90% of real-world issues.

**When to use**: App memory grows over time, seeing multiple instances of same class, crashes with memory limit exceeded, Instruments shows retain cycles

## Key Features

- 5 comprehensive leak patterns
  - Delegate retain cycles
  - Closure capture cycles
  - Observer leaks
  - Cache accumulation
  - View controller leaks
- Instruments workflow (Leaks + Allocations)
- Stack trace analysis
- Quick diagnostic questions
- Reduces debugging from 2-3 hours to 15-30 min

**Philosophy**: Memory leaks follow predictable patterns. Systematic diagnosis is faster than trial-and-error.

## Example Prompts

These are real questions developers ask that this skill answers:

- **"My app crashes after 10-15 minutes of use but there are no error messages."**
  → Covers systematic Instruments workflows to identify memory leaks vs normal memory pressure

- **"I'm seeing memory jump from 50MB to 200MB+. Is this a leak or normal caching?"**
  → Distinguishes between progressive leaks (continuous growth) and temporary spikes (caches that stabilize)

- **"View controllers don't seem to be deallocating after dismiss. How do I find the retain cycle?"**
  → Demonstrates Memory Graph Debugger to identify objects holding strong references

- **"I have timers/observers and think they're leaking. How do I verify?"**
  → Covers the 5 diagnostic patterns including timer and observer leak signatures

- **"My app uses 200MB and I don't know if that's normal or multiple leaks."**
  → Provides Instruments decision tree to distinguish normal memory use from actual leaks
