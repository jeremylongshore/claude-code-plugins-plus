/**
 * scripts/crap-score.ts — Cyclomatic-complexity scan for production TypeScript.
 *
 * Replaces the regex-based branches-per-function proxy used during the deep
 * /audit-tests pass (ccsc-ao9) with a real TypeScript AST walker. The skill's
 * upstream `crap-score.py` can't parse modern TS — it leans on the unmaintained
 * `complexity-report` JS-only tool. This file uses the TypeScript compiler API
 * (already a devDep) to count decision points properly, per-function, on each
 * production source file.
 *
 * Cyclomatic complexity formula (classic McCabe): 1 + count of decision nodes.
 * Counted nodes (per function body):
 *   - IfStatement (including else-if chains — each else-if is its own IfStatement)
 *   - WhileStatement, DoStatement, ForStatement, ForInStatement, ForOfStatement
 *   - CaseClause (not DefaultClause)
 *   - CatchClause
 *   - ConditionalExpression (`?:`)
 *   - BinaryExpression with && or || (short-circuit introduces a branch)
 *
 * Wall 5 (production) threshold: 30. Wall 6 (test) threshold: 15.
 * This script targets Wall 5 — production sources only.
 *
 * CRAP score proper is `cyclomatic^2 * (1 - coverage)^3 + cyclomatic`. With
 * repo coverage at 98%+, the first term is < 0.0001 of the second, so CRAP ≈
 * cyclomatic. That's the number we report; if coverage drops materially we can
 * wire the full CRAP formula via coverage-floor parsing.
 *
 * Usage:
 *   bun scripts/crap-score.ts [--threshold 30]
 *
 * Exit codes:
 *   0 — all functions under threshold
 *   1 — one or more functions exceed the threshold
 *   2 — CLI / parse error
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import ts from 'typescript'

// Production sources the audit tracks. New files added to the repo at top level
// should be added here if they contain runtime logic.
const PRODUCTION_FILES = [
  'lib.ts',
  'policy.ts',
  'manifest.ts',
  'journal.ts',
  'supervisor.ts',
  'server.ts',
] as const

const DEFAULT_THRESHOLD = 30

interface FunctionMetric {
  name: string
  line: number
  complexity: number
}

interface FileReport {
  path: string
  functions: FunctionMetric[]
  max: number
  mean: number
  overThreshold: FunctionMetric[]
}

/** Return the display name of a function-like node. Anonymous functions get
 *  a synthetic `<anon:line>` label. */
function functionName(node: ts.Node, source: ts.SourceFile): string {
  if (
    ts.isFunctionDeclaration(node) ||
    ts.isMethodDeclaration(node) ||
    ts.isFunctionExpression(node)
  ) {
    if (node.name && ts.isIdentifier(node.name)) return node.name.text
  }
  if (ts.isConstructorDeclaration(node)) return 'constructor'
  if ((ts.isFunctionExpression(node) || ts.isArrowFunction(node)) && node.parent) {
    const parent = node.parent
    if (ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name)) {
      return parent.name.text
    }
    if (ts.isPropertyAssignment(parent) && ts.isIdentifier(parent.name)) {
      return parent.name.text
    }
  }
  const { line } = source.getLineAndCharacterOfPosition(node.getStart(source))
  return `<anon:${line + 1}>`
}

/** Count decision points inside `node` without recursing into nested
 *  function-like declarations (those are counted separately). */
function countComplexity(node: ts.Node): number {
  let complexity = 1

  const visit = (n: ts.Node): void => {
    // Stop at nested function-like boundaries — they get their own score.
    if (
      n !== node &&
      (ts.isFunctionDeclaration(n) ||
        ts.isFunctionExpression(n) ||
        ts.isArrowFunction(n) ||
        ts.isMethodDeclaration(n) ||
        ts.isConstructorDeclaration(n))
    ) {
      return
    }

    switch (n.kind) {
      case ts.SyntaxKind.IfStatement:
      case ts.SyntaxKind.WhileStatement:
      case ts.SyntaxKind.DoStatement:
      case ts.SyntaxKind.ForStatement:
      case ts.SyntaxKind.ForInStatement:
      case ts.SyntaxKind.ForOfStatement:
      case ts.SyntaxKind.CaseClause:
      case ts.SyntaxKind.CatchClause:
      case ts.SyntaxKind.ConditionalExpression:
        complexity++
        break
      case ts.SyntaxKind.BinaryExpression: {
        const be = n as ts.BinaryExpression
        if (
          be.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken ||
          be.operatorToken.kind === ts.SyntaxKind.BarBarToken ||
          be.operatorToken.kind === ts.SyntaxKind.QuestionQuestionToken
        ) {
          complexity++
        }
        break
      }
    }
    n.forEachChild(visit)
  }
  node.forEachChild(visit)
  return complexity
}

function analyseFile(path: string, displayName: string): FileReport {
  const source = ts.createSourceFile(
    displayName,
    readFileSync(path, 'utf8'),
    ts.ScriptTarget.Latest,
    /*setParentNodes*/ true,
    ts.ScriptKind.TS,
  )
  const metrics: FunctionMetric[] = []

  const walk = (node: ts.Node): void => {
    if (
      ts.isFunctionDeclaration(node) ||
      ts.isFunctionExpression(node) ||
      ts.isArrowFunction(node) ||
      ts.isMethodDeclaration(node) ||
      ts.isConstructorDeclaration(node)
    ) {
      const { line } = source.getLineAndCharacterOfPosition(node.getStart(source))
      metrics.push({
        name: functionName(node, source),
        line: line + 1,
        complexity: countComplexity(node),
      })
    }
    node.forEachChild(walk)
  }
  walk(source)

  const complexities = metrics.map((m) => m.complexity)
  const max = complexities.length ? Math.max(...complexities) : 0
  const mean = complexities.length
    ? complexities.reduce((s, c) => s + c, 0) / complexities.length
    : 0
  return {
    path: displayName,
    functions: metrics,
    max,
    mean,
    overThreshold: [],
  }
}

function main(): number {
  const argv = process.argv.slice(2)
  let threshold = DEFAULT_THRESHOLD
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--threshold' && argv[i + 1]) {
      const n = Number(argv[i + 1])
      if (!Number.isFinite(n) || n < 1) {
        console.error(`crap-score: invalid threshold: ${argv[i + 1]}`)
        return 2
      }
      threshold = n
      i++
    } else if (argv[i] === '-h' || argv[i] === '--help') {
      console.log('Usage: bun scripts/crap-score.ts [--threshold N]')
      return 0
    } else {
      console.error(`crap-score: unknown flag: ${argv[i]}`)
      return 2
    }
  }

  const repoRoot = process.cwd()
  const reports: FileReport[] = []
  for (const f of PRODUCTION_FILES) {
    const absolutePath = join(repoRoot, f)
    try {
      const r = analyseFile(absolutePath, f)
      r.overThreshold = r.functions.filter((m) => m.complexity > threshold)
      reports.push(r)
    } catch (err) {
      console.error(`crap-score: failed to parse ${f}:`, err)
      return 2
    }
  }

  console.log(`crap-score: cyclomatic complexity scan (threshold ${threshold})`)
  console.log('─'.repeat(72))
  const pad = (s: string | number, w: number): string => String(s).padStart(w)
  const padEnd = (s: string, w: number): string => s.padEnd(w)

  let overallMax = 0
  let overallOver = 0
  for (const r of reports) {
    console.log(
      `  ${padEnd(r.path, 14)}: ${pad(r.functions.length, 3)} funcs · ` +
        `max=${pad(r.max, 3)} · ` +
        `mean=${pad(r.mean.toFixed(1), 5)} · ` +
        `over=${pad(r.overThreshold.length, 2)}`,
    )
    if (r.max > overallMax) overallMax = r.max
    overallOver += r.overThreshold.length
  }
  console.log('─'.repeat(72))
  console.log(
    `  overall max=${overallMax} · ${overallOver} function(s) over the ${threshold}-threshold`,
  )

  if (overallOver > 0) {
    console.log('')
    console.log('Functions over threshold:')
    for (const r of reports) {
      for (const fn of r.overThreshold) {
        console.log(`  ${r.path}:${fn.line} ${fn.name} (${fn.complexity})`)
      }
    }
    return 1
  }
  console.log('crap-score: OK')
  return 0
}

process.exit(main())
