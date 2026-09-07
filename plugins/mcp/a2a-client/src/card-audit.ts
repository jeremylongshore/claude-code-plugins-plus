/**
 * Pure agent-card auditing. No I/O, no network, no side effects — imported by the MCP
 * server and exercised directly by the tests.
 *
 * The governing rule: a card is an externally-authored manifest fetched from outside the
 * trust boundary. Everything here REPORTS what a card claims. Nothing here converts a
 * claim into local authority, and there is deliberately no trust score — a single number
 * would invite automating exactly the decision that has to stay with an operator.
 */

import { isIP } from 'node:net';
import { isPrivateAddress } from './net-guard.js';

export const REQUIRED_CARD_FIELDS = [
  'name',
  'description',
  'version',
  'supportedInterfaces',
  'capabilities',
  'defaultInputModes',
  'defaultOutputModes',
  'skills',
] as const;

export type Disposition = 'reported' | 'operator-decision-required';

export interface CardFinding {
  claim: string;
  value: string;
  finding: string;
  disposition: Disposition;
}

export interface CardAudit {
  structure: 'valid' | 'malformed';
  missingFields: string[];
  findings: CardFinding[];
  /** Three-valued in the spec. This module never verifies, so it never reports "verified". */
  signatureStatus: 'absent' | 'unverified';
  operatorDecisionsRequired: number;
}

type UnknownRecord = Record<string, unknown>;

function recordOf(value: unknown): UnknownRecord {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as UnknownRecord)
    : {};
}

function recordsOf(value: unknown): UnknownRecord[] {
  return Array.isArray(value) ? value.map(recordOf) : [];
}

function stringOf(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function cardHostIsNonPublic(hostname: string): boolean {
  const host = hostname
    .toLowerCase()
    .replace(/^\[|\]$/g, '')
    .replace(/\.$/, '')
    .split('%', 1)[0];
  return (
    host === 'localhost' ||
    host.endsWith('.localhost') ||
    host.endsWith('.local') ||
    (isIP(host) !== 0 && isPrivateAddress(host))
  );
}

function requiredFieldIsValid(field: (typeof REQUIRED_CARD_FIELDS)[number], value: unknown): boolean {
  if (field === 'name' || field === 'description' || field === 'version') {
    return typeof value === 'string' && value.length > 0;
  }
  if (field === 'capabilities') {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }
  if (!Array.isArray(value) || value.length === 0) return false;
  if (field === 'defaultInputModes' || field === 'defaultOutputModes') {
    return value.every((item) => typeof item === 'string' && item.length > 0);
  }
  if (field === 'supportedInterfaces') {
    return value.every((item) => {
      const iface = recordOf(item);
      return (
        stringOf(iface.url).length > 0 &&
        stringOf(iface.protocolBinding).length > 0 &&
        stringOf(iface.protocolVersion).length > 0
      );
    });
  }
  return value.every((item) => {
    const skill = recordOf(item);
    return stringOf(skill.id).length > 0 && stringOf(skill.name).length > 0;
  });
}

export function auditCard(card: unknown): CardAudit {
  const record = recordOf(card);
  const missingFields = REQUIRED_CARD_FIELDS.filter(
    (field) => !requiredFieldIsValid(field, record[field]),
  );

  const findings: CardFinding[] = [
    ...interfaceFindings(card),
    ...requiredExtensionFindings(card),
    ...skillOverrideFindings(card),
    ...fetchTargetFindings(card),
  ];

  return {
    structure: missingFields.length === 0 ? 'valid' : 'malformed',
    missingFields,
    findings,
    signatureStatus: recordsOf(record.signatures).length > 0 ? 'unverified' : 'absent',
    operatorDecisionsRequired: findings.filter(
      (f) => f.disposition === 'operator-decision-required',
    ).length,
  };
}

function interfaceFindings(card: unknown): CardFinding[] {
  const record = recordOf(card);
  const out: CardFinding[] = [];
  for (const [i, iface] of recordsOf(record.supportedInterfaces).entries()) {
    const claim = `supportedInterfaces[${i}].url`;
    const interfaceUrl = stringOf(iface.url);
    let host: string;
    try {
      host = new URL(interfaceUrl).hostname;
    } catch {
      out.push({
        claim,
        value: interfaceUrl,
        finding: 'URL does not parse as an absolute URL; may be a gRPC host:port or malformed.',
        disposition: 'operator-decision-required',
      });
      continue;
    }
    if (cardHostIsNonPublic(host)) {
      out.push({
        claim,
        value: interfaceUrl,
        finding: 'Directs traffic to a loopback or private-range host.',
        disposition: 'operator-decision-required',
      });
    } else if (!interfaceUrl.startsWith('https://')) {
      out.push({
        claim,
        value: interfaceUrl,
        finding: 'Non-HTTPS interface URL.',
        disposition: 'operator-decision-required',
      });
    }
  }
  return out;
}

function requiredExtensionFindings(card: unknown): CardFinding[] {
  const capabilities = recordOf(recordOf(card).capabilities);
  return recordsOf(capabilities.extensions)
    .filter((extension) => extension.required === true)
    .map((extension) => ({
      claim: 'capabilities.extensions[].required',
      value: stringOf(extension.uri),
      finding: 'Card requires the client to support this extension to interoperate.',
      disposition: 'operator-decision-required' as const,
    }));
}

/**
 * Per-skill securityRequirements OVERRIDE the agent-level list. A card that reads strict
 * at the top can still expose one skill behind a weaker requirement, so the audit runs at
 * the skill level rather than only the agent level.
 */
function schemeNames(requirements: unknown): string[] {
  return recordsOf(requirements).flatMap((requirement) =>
    Object.keys(recordOf(requirement.schemes)),
  );
}

function skillOverrideFindings(card: unknown): CardFinding[] {
  const record = recordOf(card);
  const agentSchemes = new Set(
    schemeNames(record.securityRequirements),
  );
  if (agentSchemes.size === 0) return [];

  const out: CardFinding[] = [];
  for (const skill of recordsOf(record.skills)) {
    const declared = recordsOf(skill.securityRequirements);
    if (declared.length === 0) continue; // no override — agent-level applies
    const skillSchemes = new Set(schemeNames(declared));
    const dropped = [...agentSchemes].filter((s) => !skillSchemes.has(s));
    if (dropped.length > 0) {
      out.push({
        claim: `skills[${stringOf(skill.id)}].securityRequirements`,
        value: skillSchemes.size ? [...skillSchemes].join(', ') : '(none)',
        finding: `Per-skill override drops agent-level scheme(s): ${dropped.join(', ')}.`,
        disposition: 'operator-decision-required',
      });
    }
  }
  return out;
}

/** Card-named fetch targets are reported as strings and never resolved on the card's say-so. */
function fetchTargetFindings(card: unknown): CardFinding[] {
  const record = recordOf(card);
  const out: CardFinding[] = [];
  for (const field of ['documentationUrl', 'iconUrl'] as const) {
    const value = stringOf(record[field]);
    if (value.length > 0) {
      out.push({
        claim: field,
        value,
        finding: 'Card-named fetch target. Reported as a string; not resolved by this server.',
        disposition: 'reported',
      });
    }
  }
  return out;
}

/** Claims are labelled and enumerated, never merged into a single verdict. */
export function claimsOf(card: unknown) {
  const record = recordOf(card);
  const provider = recordOf(record.provider);
  const capabilities = recordOf(record.capabilities);
  return {
    identity: {
      name: stringOf(record.name),
      version: stringOf(record.version),
      provider: stringOf(provider.organization) || undefined,
    },
    interfaces: recordsOf(record.supportedInterfaces).map((item, idx) => ({
      preference: idx === 0 ? 'preferred' : `fallback-${idx}`,
      url: stringOf(item.url),
      protocolBinding: stringOf(item.protocolBinding),
      protocolVersion: stringOf(item.protocolVersion),
      tenant: stringOf(item.tenant) || undefined,
    })),
    capabilitiesClaimed: {
      streaming: capabilities.streaming === true,
      pushNotifications: capabilities.pushNotifications === true,
      extendedAgentCard: capabilities.extendedAgentCard === true,
      extensions: recordsOf(capabilities.extensions).map((extension) => ({
        uri: stringOf(extension.uri),
        required: extension.required === true,
      })),
    },
    skillsClaimed: recordsOf(record.skills).map((skill) => ({
      id: stringOf(skill.id),
      name: stringOf(skill.name),
      tags: Array.isArray(skill.tags) ? skill.tags.map(stringOf) : [],
    })),
    securitySchemesClaimed: Object.keys(recordOf(record.securitySchemes)),
  };
}
