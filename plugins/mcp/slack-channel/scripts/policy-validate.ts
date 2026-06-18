#!/usr/bin/env bun
// Policy-rule validator used by the `/slack-channel:policy` skill. Thin wrapper
// around the real loaders in policy.ts so the skill can surface parse errors,
// shadow warnings, and broad-auto-approve warnings BEFORE the operator writes
// access.json and restarts the server.
//
// Usage:
//   bun scripts/policy-validate.ts <path-to-access.json>
//   bun scripts/policy-validate.ts --rules <path-to-rules.json>   (bare array)
//   bun scripts/policy-validate.ts --stdin                         (bare array on stdin)
//
// Exit codes:
//   0 — parse + uniqueness OK (shadow / broad-auto-approve warnings, if any,
//       are carried inside the stdout JSON — see shape below)
//   1 — parse failure (Zod error), duplicate rule id, or bad CLI args
//
// stdout shape (always a single line of valid JSON):
//   { "ok": true,  "source": "...", "count": N, "shadows": [...], "broads": [...] }
//   { "ok": false, "error": "<message>" }

import { readFileSync } from 'node:fs'
import {
  assertUniqueRuleIds,
  detectBroadAutoApprove,
  detectShadowing,
  type PolicyRule,
  parsePolicyRules,
} from '../policy.ts'

function die(msg: string): never {
  process.stdout.write(`${JSON.stringify({ ok: false, error: msg })}\n`)
  process.exit(1)
}

function readInput(): { source: string; raw: unknown } {
  const args = process.argv.slice(2)
  const firstArg = args[0]
  if (!firstArg) die('usage: policy-validate.ts <access.json> | --rules <file> | --stdin')

  if (firstArg === '--stdin') {
    const body = readFileSync(0, 'utf8')
    try {
      return { source: '<stdin>', raw: JSON.parse(body) }
    } catch (err) {
      die(`invalid JSON on stdin: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  if (firstArg === '--rules') {
    const rulesPath = args[1]
    if (!rulesPath) die('--rules requires a path argument')
    try {
      return { source: rulesPath, raw: JSON.parse(readFileSync(rulesPath, 'utf8')) }
    } catch (err) {
      die(`cannot read ${rulesPath}: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  // Default: treat arg as access.json and pull its `policy` field.
  try {
    const body: unknown = JSON.parse(readFileSync(firstArg, 'utf8'))
    const policy =
      typeof body === 'object' && body !== null && 'policy' in body
        ? (body as { policy?: unknown }).policy
        : undefined
    return { source: firstArg, raw: policy ?? [] }
  } catch (err) {
    die(`cannot read ${firstArg}: ${err instanceof Error ? err.message : String(err)}`)
  }
}

const { source, raw } = readInput()

let parsed: PolicyRule[]
try {
  parsed = parsePolicyRules(raw)
} catch (err) {
  die(`parse failed for ${source}: ${err instanceof Error ? err.message : String(err)}`)
}

// Shared with server.ts loadPolicy() so the skill and the server use one
// code path for the duplicate-id fatal check (ccsc-kx8 closed the drift).
// The thrown message already starts with "duplicate rule id(s): …", so
// prepend the source without repeating the prefix.
try {
  assertUniqueRuleIds(parsed)
} catch (err) {
  die(`${err instanceof Error ? err.message : String(err)} (in ${source})`)
}

const shadows = detectShadowing(parsed)
const broads = detectBroadAutoApprove(parsed)

process.stdout.write(
  `${JSON.stringify({
    ok: true,
    source,
    count: parsed.length,
    shadows: shadows.map((w) => ({ later: w.later, earlier: w.earlier, message: w.message })),
    broads: broads.map((w) => ({ ruleId: w.ruleId, message: w.message })),
  })}\n`,
)
