/**
 * features/steps/tier-shadow.ts — Step definitions for tier-shadow.feature.
 *
 * Exercises detectShadowing() in policy.ts — the cross-tier intersection
 * lint added in ccsc-4g8. Context carries the PolicyRule list as it grows
 * scenario-by-scenario and the resulting ShadowWarning[].
 *
 * Most steps use RegExp patterns so multiple scenarios share one handler
 * for "<tier>-tier <effect> rule on tool <name>" variations. The scenarios
 * are intentionally declarative; the handlers do the wiring.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { expect } from 'bun:test'
import { detectShadowing, type PolicyRule, type ShadowWarning } from '../../policy.ts'
import type { StepRegistry } from '../runner.ts'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type Tier = 'default' | 'workspace' | 'user' | 'admin'
type RuleEffect = 'auto_approve' | 'deny' | 'require_approval'

interface RuleSpec {
  tier: Tier
  effect: RuleEffect
  tool?: string
  channel?: string
  actor?: 'session_owner' | 'claude_process'
  pathPrefix?: string
  argEquals?: Record<string, unknown>
}

let ruleSeq = 0
function nextRuleId(): string {
  ruleSeq += 1
  return `rule-${ruleSeq}`
}

function buildRule(spec: RuleSpec): PolicyRule {
  const match: PolicyRule['match'] = { tier: spec.tier }
  if (spec.tool !== undefined) match.tool = spec.tool
  if (spec.channel !== undefined) match.channel = spec.channel
  if (spec.actor !== undefined) match.actor = spec.actor
  if (spec.pathPrefix !== undefined) match.pathPrefix = spec.pathPrefix
  if (spec.argEquals !== undefined) match.argEquals = spec.argEquals

  // The match refinement requires at least one non-tier field. Every
  // scenario provides one — assert here so a buggy step is loud.
  if (
    match.tool === undefined &&
    match.channel === undefined &&
    match.actor === undefined &&
    match.pathPrefix === undefined &&
    match.argEquals === undefined
  ) {
    throw new Error('buildRule: tier alone is not a valid match — provide tool/channel/etc.')
  }

  const id = nextRuleId()
  switch (spec.effect) {
    case 'auto_approve':
      return { id, priority: 100, effect: 'auto_approve', match }
    case 'deny':
      return { id, priority: 100, effect: 'deny', reason: 'test deny', match }
    case 'require_approval':
      return {
        id,
        priority: 100,
        effect: 'require_approval',
        ttlMs: 60_000,
        approvers: 1,
        match,
      }
  }
}

function pushRule(ctx: Record<string, unknown>, rule: PolicyRule): void {
  const list = (ctx.rules as PolicyRule[] | undefined) ?? []
  list.push(rule)
  ctx.rules = list
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

export function registerTierShadowSteps(registry: StepRegistry): void {
  // Background — reset state for each scenario.
  registry.register('an empty list of policy rules', (ctx) => {
    ctx.rules = []
    ctx.warnings = undefined
    ruleSeq = 0
    ctx.lastWorkspaceRuleId = undefined
    ctx.lastAdminRuleId = undefined
    ctx.firstAdminRuleId = undefined
    ctx.lastDefaultRuleId = undefined
  })

  // Given a <tier>-tier <effect> rule on tool "<name>"
  registry.register(
    /^(?:a |an )?(default|workspace|user|admin)-tier (auto_approve|deny|require_approval) rule on tool "([^"]+)"$/,
    (ctx, m) => {
      const tier = m[1] as Tier
      const effect = m[2] as RuleEffect
      const tool = m[3]
      const rule = buildRule({ tier, effect, tool })
      pushRule(ctx, rule)
      if (tier === 'admin' && effect === 'deny') {
        ctx.lastAdminRuleId = rule.id
        if (ctx.firstAdminRuleId === undefined) ctx.firstAdminRuleId = rule.id
        if (tool === 'Bash') ctx.bashAdminRuleId = rule.id
      }
      if (tier === 'workspace' && effect === 'auto_approve') ctx.lastWorkspaceRuleId = rule.id
      if (tier === 'default' && effect === 'auto_approve') ctx.lastDefaultRuleId = rule.id
    },
  )

  // Given a second <tier>-tier <effect> rule on tool "<name>"
  registry.register(
    /^(?:a )?second (default|workspace|user|admin)-tier (auto_approve|deny|require_approval) rule on tool "([^"]+)"$/,
    (ctx, m) => {
      const tier = m[1] as Tier
      const effect = m[2] as RuleEffect
      const tool = m[3]
      pushRule(ctx, buildRule({ tier, effect, tool }))
    },
  )

  // Given a <tier>-tier <effect> rule on tool "<name>" in channel "<id>"
  registry.register(
    /^(?:a |an )?(default|workspace|user|admin)-tier (auto_approve|deny|require_approval) rule on tool "([^"]+)" in channel "([^"]+)"$/,
    (ctx, m) => {
      pushRule(
        ctx,
        buildRule({
          tier: m[1] as Tier,
          effect: m[2] as RuleEffect,
          tool: m[3],
          channel: m[4],
        }),
      )
    },
  )

  // Given a <tier>-tier <effect> rule with pathPrefix "<path>"
  registry.register(
    /^(?:a |an )?(default|workspace|user|admin)-tier (auto_approve|deny|require_approval) rule with pathPrefix "([^"]+)"$/,
    (ctx, m) => {
      pushRule(
        ctx,
        buildRule({
          tier: m[1] as Tier,
          effect: m[2] as RuleEffect,
          pathPrefix: m[3],
        }),
      )
    },
  )

  // Given a <tier>-tier <effect> rule on tool "<name>" with argEquals <key> equal to "<value>"
  registry.register(
    /^(?:a |an )?(default|workspace|user|admin)-tier (auto_approve|deny|require_approval) rule on tool "([^"]+)" with argEquals (\w+) equal to "([^"]+)"$/,
    (ctx, m) => {
      pushRule(
        ctx,
        buildRule({
          tier: m[1] as Tier,
          effect: m[2] as RuleEffect,
          tool: m[3],
          argEquals: { [m[4]!]: m[5] },
        }),
      )
    },
  )

  // Given a <tier>-tier <effect> rule on tool "<name>" with actor "<actor>"
  registry.register(
    /^(?:a |an )?(default|workspace|user|admin)-tier (auto_approve|deny|require_approval) rule on tool "([^"]+)" with actor "([^"]+)"$/,
    (ctx, m) => {
      pushRule(
        ctx,
        buildRule({
          tier: m[1] as Tier,
          effect: m[2] as RuleEffect,
          tool: m[3],
          actor: m[4] as 'session_owner' | 'claude_process',
        }),
      )
    },
  )

  // When
  registry.register('the linter runs', (ctx) => {
    const rules = (ctx.rules as PolicyRule[]) ?? []
    ctx.warnings = detectShadowing(rules)
  })

  // Then it emits no warnings
  registry.register('it emits no warnings', (ctx) => {
    const warnings = ctx.warnings as ShadowWarning[]
    expect(warnings).toEqual([])
  })

  // Then it emits one cross-tier warning
  registry.register('it emits one cross-tier warning', (ctx) => {
    const warnings = ctx.warnings as ShadowWarning[]
    const crossTier = warnings.filter((w) => w.crossTier === true)
    expect(crossTier).toHaveLength(1)
  })

  // Then it emits one within-tier warning
  registry.register('it emits one within-tier warning', (ctx) => {
    const warnings = ctx.warnings as ShadowWarning[]
    const withinTier = warnings.filter((w) => w.crossTier === false)
    expect(withinTier).toHaveLength(1)
  })

  // Then the cross-tier warning names the workspace rule as later and the admin rule as earlier
  registry.register(
    'the cross-tier warning names the workspace rule as later and the admin rule as earlier',
    (ctx) => {
      const warnings = ctx.warnings as ShadowWarning[]
      const crossTier = warnings.find((w) => w.crossTier === true)
      expect(crossTier).toBeDefined()
      expect(crossTier!.later).toBe(ctx.lastWorkspaceRuleId as string)
      expect(crossTier!.earlier).toBe(ctx.lastAdminRuleId as string)
    },
  )

  // Then the cross-tier warning earlier id matches the bash admin rule
  registry.register('the cross-tier warning earlier id matches the bash admin rule', (ctx) => {
    const warnings = ctx.warnings as ShadowWarning[]
    const crossTier = warnings.find((w) => w.crossTier === true)
    expect(crossTier).toBeDefined()
    expect(crossTier!.earlier).toBe(ctx.bashAdminRuleId as string)
  })
}
