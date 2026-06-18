/**
 * RFC 8785 JCS interop test (ccsc-713)
 *
 * Pins the byte-exact output of `canonicalJson()` in journal.ts:668
 * against a fixture set drawn from RFC 8785 (the JSON Canonicalization
 * Scheme spec). Every vector is described in features/jcs-vectors.json
 * along with its provenance (which RFC 8785 section it exercises).
 *
 * Why this exists: journal v2 (ccsc-22l) signs the canonicalized bytes
 * of every event. For third-party verification to be possible, our
 * canonicalizer must produce byte-identical output to any other
 * RFC 8785 implementation on the same input. Without a pinned vector
 * suite, a future "innocent" refactor of canonicalJson could silently
 * diverge — breaking signature verification for everyone holding our
 * audit logs.
 *
 * The vector file is pinned in .harness-hash so an edit to it requires
 * an explicit hash re-init via `scripts/harness-hash.sh init` (same
 * tamper-evident discipline as the .feature files).
 *
 * Schema scope: the journal's canonicalJson() has a NARROWER input
 * domain than full RFC 8785 — only integers and BMP-only strings, no
 * non-finite numbers, no undefined/symbol/function/bigint. The "throws"
 * vectors document this narrower domain by asserting rejection.
 */

import { describe, expect, test } from 'bun:test'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { canonicalJson } from '../journal.ts'

interface SupportedVector {
  name: string
  origin: string
  input: unknown
  expected: string
}

interface ThrowsVector {
  name: string
  origin: string
  input: unknown
  errorContains: string
}

interface VectorFile {
  $schema_comment: string
  $ref: string
  supported: SupportedVector[]
  throws: ThrowsVector[]
}

const vectors: VectorFile = JSON.parse(
  readFileSync(join(import.meta.dir, 'jcs-vectors.json'), 'utf8'),
)

// Some throws-vectors use string placeholders for values that JSON cannot
// represent natively (Infinity / NaN / undefined). Resolve those at test
// time so the vector file stays valid JSON.
function resolveThrowsInput(input: unknown): unknown {
  if (input === '__INFINITY__') return Number.POSITIVE_INFINITY
  if (input === '__NAN__') return Number.NaN
  if (input === '__UNDEFINED__') return undefined
  return input
}

describe('RFC 8785 JCS interop — canonicalJson() supported vectors (ccsc-713)', () => {
  // Every supported vector must produce byte-exact canonical output.
  // We compare strings via toBe() which is referential equality on
  // primitives — UTF-16 code-unit equality.
  for (const vec of vectors.supported) {
    test(`${vec.name} [${vec.origin}]`, () => {
      const actual = canonicalJson(vec.input)
      expect(actual).toBe(vec.expected)
    })
  }
})

describe('RFC 8785 JCS interop — canonicalJson() throws on inputs outside the documented domain (ccsc-713)', () => {
  for (const vec of vectors.throws) {
    test(`${vec.name} [${vec.origin}]`, () => {
      const resolved = resolveThrowsInput(vec.input)
      expect(() => canonicalJson(resolved)).toThrow(vec.errorContains)
    })
  }
})

describe('RFC 8785 JCS interop — fixture file invariants (ccsc-713)', () => {
  test('vector file has at least 20 supported cases (rollout-plan minimum)', () => {
    expect(vectors.supported.length).toBeGreaterThanOrEqual(20)
  })

  test('vector file declares RFC 8785 as its reference', () => {
    expect(vectors.$ref).toContain('rfc8785')
  })

  test('every supported vector has the four required fields', () => {
    for (const vec of vectors.supported) {
      expect(typeof vec.name).toBe('string')
      expect(typeof vec.origin).toBe('string')
      expect(typeof vec.expected).toBe('string')
      // `input` can legitimately be null — only assert the property exists.
      expect('input' in vec).toBe(true)
    }
  })

  test('every throws-vector declares the expected error substring', () => {
    for (const vec of vectors.throws) {
      expect(typeof vec.errorContains).toBe('string')
      expect(vec.errorContains.length).toBeGreaterThan(0)
    }
  })

  test('object-key sort vectors actually exercise sorting (input keys are NOT already in canonical order)', () => {
    // Pin the test-of-the-test: if a vector author accidentally wrote
    // {"a":1,"b":2} as the input for a "sorted" case, the canonicalizer
    // would pass even if its sort logic was broken. This invariant
    // catches that by requiring at least one supported-vector input to
    // have keys NOT in canonical order.
    const sortVectors = vectors.supported.filter((v) => v.name.toLowerCase().includes('sort'))
    expect(sortVectors.length).toBeGreaterThan(0)
    const adversarialSortVectors = sortVectors.filter((v) => {
      if (typeof v.input !== 'object' || v.input === null || Array.isArray(v.input)) return false
      const keys = Object.keys(v.input as Record<string, unknown>)
      const sorted = [...keys].sort()
      return JSON.stringify(keys) !== JSON.stringify(sorted)
    })
    expect(adversarialSortVectors.length).toBeGreaterThan(0)
  })
})
