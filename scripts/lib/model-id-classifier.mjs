/**
 * model-id-classifier.mjs — THE Claude-model-identifier classifier (blueprint
 * 727, Epic 3 bead 3.7; drafted inside E3.1's measurement, promoted here).
 *
 * Every occurrence of a `claude-…` token classifies into exactly one of three
 * disjoint roles:
 *
 *   bead-id     a beads issue handle (protected — migration tooling must
 *               NEVER rewrite one; the beads prefix in this repo IS `claude`)
 *   functional  the id configures behavior (a model:/"model"/--model
 *               assignment) — the class E3.8 replaces with model_class tiers
 *   prose       a mention in text — deliberately preserved (deleting accurate
 *               history is a truthfulness loss, not a portability gain)
 *
 * The committed exclusion list (schemas/canonical/v0/model-id-exclusions.json)
 * pins live bead handles by exact string on top of the shape rule, so even a
 * future handle that collides with a model-family shape stays protected.
 *
 * ONE classifier: measure-canonical-surface.mjs (E3.1) and every migration
 * tool (E3.8's rewriter, E3.10's gate) import from here. A second
 * implementation of these semantics is the drift this bead exists to end.
 */

import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..', '..');

/** Concrete model-family ids ONLY — the bead-id shape must not match. */
export const MODEL_ID =
  /\bclaude-(?:opus|sonnet|haiku|fable|instant|[1-9](?:[-.][0-9])?)(?:-[a-z0-9.]+)*\b/gi;

/** A beads handle: claude-<3-5 alnum hash>(.child)*. */
export const BEAD_ID = /^claude-[a-z0-9]{3,5}(?:\.[0-9]+)*$/;

/**
 * The numeric arm requires a generation boundary ("claude-3", "claude-3-5…",
 * "claude-2.1") so a digit-led bead handle like "claude-4laa" never
 * prefix-matches a model family.
 */
export const MODEL_FAMILY = /^claude-(?:opus|sonnet|haiku|fable|instant|[1-9](?:[-.]|$))/;

export const FUNCTIONAL_LINE = /(?:^|[^a-z])(?:model|models|MODEL)["']?\s*[:=]|--model[= ]/;

let exclusions;
export function loadExclusions() {
  if (!exclusions) {
    exclusions = JSON.parse(
      readFileSync(join(ROOT, 'schemas', 'canonical', 'v0', 'model-id-exclusions.json'), 'utf-8'),
    );
  }
  return exclusions;
}

/**
 * Classify one token in the context of its line.
 * Order is load-bearing: exclusion-list and bead-shape checks run BEFORE any
 * model-family logic, so protection wins every tie.
 */
export function classifyModelToken(token, line, excl = loadExclusions()) {
  if (excl.protected_handles.includes(token)) return 'bead-id';
  if (BEAD_ID.test(token) && !MODEL_FAMILY.test(token)) return 'bead-id';
  if (FUNCTIONAL_LINE.test(line)) return 'functional';
  return 'prose';
}

/**
 * Bead-handle-shaped scan for a whole line. The trailing (?!-) keeps a
 * hyphen-continued model id (claude-fable-5) from leaking its prefix
 * (claude-fable) into the bead scan as a phantom token.
 */
export const BEAD_ID_SCAN = /\bclaude-[a-z0-9]{3,5}(?:\.[0-9]+)*\b(?!-)/g;

/** All claude-shaped tokens on a line (model-family or bead-handle shaped). */
export function claudeTokensOnLine(line) {
  const modelTokens = line.match(MODEL_ID) || [];
  const beadTokens = (line.match(BEAD_ID_SCAN) || []).filter((t) => !modelTokens.includes(t));
  return [...modelTokens, ...beadTokens];
}
