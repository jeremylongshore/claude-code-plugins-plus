/**
 * features/runner.ts — Lightweight Gherkin parser + step registry.
 *
 * Handles a strict subset of Gherkin:
 *   Feature / Background / Scenario / Given / When / Then / And / But
 * No Scenario Outline, no examples, no tags, no doc strings, no data tables.
 *
 * Step definitions are registered by exact string or RegExp. A step that
 * has no matching handler throws at registration time (via validate()) so
 * engineers see the missing step before any test runs.
 *
 * Per-scenario state is carried in a plain Context object that is reset
 * between scenarios by the runner.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

// ---------------------------------------------------------------------------
// Context — shared mutable state across steps in one scenario
// ---------------------------------------------------------------------------

/** Mutable bag of state shared across all steps in a single scenario.
 *  The runner resets this to a fresh object between scenarios. */
export type Context = Record<string, unknown>

// ---------------------------------------------------------------------------
// Step handler type
// ---------------------------------------------------------------------------

export type StepFn = (ctx: Context, match: RegExpMatchArray) => void | Promise<void>

interface StepEntry {
  pattern: RegExp
  fn: StepFn
}

// ---------------------------------------------------------------------------
// StepRegistry — accumulates definitions and matches text to a handler
// ---------------------------------------------------------------------------

export class StepRegistry {
  private readonly steps: StepEntry[] = []

  /** Register a step by exact string (anchored match) or RegExp. */
  register(pattern: string | RegExp, fn: StepFn): void {
    const re = typeof pattern === 'string' ? new RegExp(`^${escapeRegExp(pattern)}$`) : pattern
    this.steps.push({ pattern: re, fn })
  }

  /** Find the handler for `text`. Returns the fn + match groups, or null. */
  match(text: string): { fn: StepFn; match: RegExpMatchArray } | null {
    for (const entry of this.steps) {
      const m = text.match(entry.pattern)
      if (m) return { fn: entry.fn, match: m }
    }
    return null
  }
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// ---------------------------------------------------------------------------
// Gherkin AST types
// ---------------------------------------------------------------------------

export interface Step {
  keyword: 'Given' | 'When' | 'Then' | 'And' | 'But'
  text: string
}

export interface Scenario {
  name: string
  steps: Step[]
}

export interface Feature {
  name: string
  backgroundSteps: Step[]
  scenarios: Scenario[]
}

// ---------------------------------------------------------------------------
// Parser — minimal Gherkin line-by-line state machine
// ---------------------------------------------------------------------------

const KEYWORD_RE = /^(Feature|Background|Scenario|Given|When|Then|And|But):\s*(.*)/

export function parseFeature(source: string): Feature {
  const lines = source.split('\n')
  const feature: Feature = { name: '', backgroundSteps: [], scenarios: [] }
  let currentScenario: Scenario | null = null
  let inBackground = false

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue

    const m = line.match(KEYWORD_RE)
    if (!m) continue

    const [, keyword, rest] = m as [string, string, string]

    switch (keyword) {
      case 'Feature':
        feature.name = rest
        break

      case 'Background':
        inBackground = true
        currentScenario = null
        break

      case 'Scenario': {
        inBackground = false
        currentScenario = { name: rest, steps: [] }
        feature.scenarios.push(currentScenario)
        break
      }

      case 'Given':
      case 'When':
      case 'Then':
      case 'And':
      case 'But': {
        const step: Step = {
          keyword: keyword as Step['keyword'],
          text: rest,
        }
        if (inBackground) {
          feature.backgroundSteps.push(step)
        } else if (currentScenario) {
          currentScenario.steps.push(step)
        }
        break
      }
    }
  }

  return feature
}

// ---------------------------------------------------------------------------
// Runner helpers
// ---------------------------------------------------------------------------

/** Execute a single step against the registry. Throws if unmatched. */
export async function runStep(registry: StepRegistry, step: Step, ctx: Context): Promise<void> {
  const result = registry.match(step.text)
  if (!result) {
    throw new Error(`No step definition for: "${step.keyword}: ${step.text}"`)
  }
  await result.fn(ctx, result.match)
}

/** Validate that every step in every scenario (including background) has
 *  a registered handler. Throws on the FIRST missing step so the engineer
 *  sees a clear message without running any test. */
export function validateRegistry(feature: Feature, registry: StepRegistry): void {
  const allSteps: Step[] = [...feature.backgroundSteps]
  for (const s of feature.scenarios) {
    allSteps.push(...s.steps)
  }
  const missing: string[] = []
  const seen = new Set<string>()
  for (const step of allSteps) {
    if (seen.has(step.text)) continue
    seen.add(step.text)
    if (!registry.match(step.text)) {
      missing.push(`  "${step.keyword}: ${step.text}"`)
    }
  }
  if (missing.length > 0) {
    throw new Error(`Missing step definitions in feature "${feature.name}":\n${missing.join('\n')}`)
  }
}

/** Build a bun:test-compatible runner for a parsed feature.
 *
 *  Returns an async function `run(describe, test, beforeEach)` that
 *  registers the feature's scenarios as bun:test tests. Kept separate
 *  from the bun:test imports so runner.ts itself stays free of test
 *  framework imports and unit-testable. */
export function buildRunner(
  feature: Feature,
  registry: StepRegistry,
): (
  describeFn: (name: string, fn: () => void) => void,
  testFn: (name: string, fn: () => Promise<void>) => void,
  beforeEachFn: (fn: () => void) => void,
) => void {
  return (describeFn, testFn, beforeEachFn) => {
    describeFn(`Feature: ${feature.name}`, () => {
      const ctx: Context = {}

      beforeEachFn(() => {
        // Reset context between scenarios
        for (const k of Object.keys(ctx)) delete ctx[k]
      })

      for (const scenario of feature.scenarios) {
        const scenarioName = scenario.name
        testFn(`Scenario: ${scenarioName}`, async () => {
          // Run background steps first
          for (const step of feature.backgroundSteps) {
            await runStep(registry, step, ctx)
          }
          // Then scenario-specific steps
          for (const step of scenario.steps) {
            await runStep(registry, step, ctx)
          }
        })
      }
    })
  }
}
