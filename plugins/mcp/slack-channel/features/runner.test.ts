/**
 * features/runner.test.ts — Gherkin runner entry point for bun:test.
 *
 * Discovers the five .feature files under features/, parses them, and
 * runs each scenario as a bun:test test. Step definitions live in
 * features/steps/*.ts. A step with no registered handler throws at
 * validation time (before any test runs) so missing definitions are
 * immediately visible.
 *
 * New tests added here: 10 (inbound_gate) + 8 (file_exfil_guard) +
 * 5 (outbound_reply_filter) + 7 (policy_evaluation) + 7 (audit_chain)
 * = 37 new scenarios.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterAll, beforeEach, describe, test } from 'bun:test'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { buildRunner, parseFeature, StepRegistry, validateRegistry } from './runner.ts'
import { registerAdminSteps } from './steps/admin.ts'
import { registerGateSteps } from './steps/gate.ts'
import { cleanupJournalFixtures, registerJournalSteps } from './steps/journal.ts'
import { registerOutboundSteps } from './steps/outbound.ts'
import { registerPolicySteps } from './steps/policy.ts'
import {
  createSendableFixtures,
  registerSendableSteps,
  type SendableFixtures,
} from './steps/sendable.ts'
import { registerTierShadowSteps } from './steps/tier-shadow.ts'

// ---------------------------------------------------------------------------
// Load .feature files
// ---------------------------------------------------------------------------

const FEATURES_DIR = join(import.meta.dir)

function loadFeature(filename: string) {
  const src = readFileSync(join(FEATURES_DIR, filename), 'utf8')
  return parseFeature(src)
}

// ---------------------------------------------------------------------------
// Cleanup hooks
// ---------------------------------------------------------------------------

let sendableFixtures: SendableFixtures | null = null

afterAll(() => {
  sendableFixtures?.cleanup()
  cleanupJournalFixtures()
})

// ---------------------------------------------------------------------------
// 1. Inbound gate — gate() from lib.ts
// ---------------------------------------------------------------------------

{
  const feature = loadFeature('inbound_gate.feature')
  const registry = new StepRegistry()
  registerGateSteps(registry)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}

// ---------------------------------------------------------------------------
// 2. File exfiltration guard — assertSendable() from lib.ts
// ---------------------------------------------------------------------------

{
  sendableFixtures = createSendableFixtures()

  const feature = loadFeature('file_exfiltration_guard.feature')
  const registry = new StepRegistry()
  registerSendableSteps(registry, sendableFixtures)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}

// ---------------------------------------------------------------------------
// 3. Outbound reply filter — assertOutboundAllowed() from lib.ts
// ---------------------------------------------------------------------------

{
  const feature = loadFeature('outbound_reply_filter.feature')
  const registry = new StepRegistry()
  registerOutboundSteps(registry)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}

// ---------------------------------------------------------------------------
// 4. Policy evaluation — evaluate() from policy.ts
// ---------------------------------------------------------------------------

{
  const feature = loadFeature('policy_evaluation.feature')
  const registry = new StepRegistry()
  registerPolicySteps(registry)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}

// ---------------------------------------------------------------------------
// 5. Audit chain verifier — verifyJournal() from journal.ts
// ---------------------------------------------------------------------------

{
  const feature = loadFeature('audit_chain_verifier.feature')
  const registry = new StepRegistry()
  registerJournalSteps(registry)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}

// ---------------------------------------------------------------------------
// 6. Tier-shadow detection — detectShadowing() in policy.ts (ccsc-4g8)
// ---------------------------------------------------------------------------

{
  const feature = loadFeature('tier-shadow.feature')
  const registry = new StepRegistry()
  registerTierShadowSteps(registry)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}

// ---------------------------------------------------------------------------
// 7. Admin commands — dispatchAdminCommand() in admin.ts (ccsc-3w0)
// ---------------------------------------------------------------------------

{
  const feature = loadFeature('admin_commands.feature')
  const registry = new StepRegistry()
  registerAdminSteps(registry)
  validateRegistry(feature, registry)

  const runFeature = buildRunner(feature, registry)
  runFeature(describe, test, beforeEach)
}
