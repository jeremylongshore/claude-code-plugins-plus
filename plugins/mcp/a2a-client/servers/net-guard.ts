/**
 * Outbound network guard — the single choke point every A2A request passes through.
 *
 * Two problems this solves, both raised in review of the first cut and both of which
 * contradicted this plugin's own stated posture:
 *
 *  1. **Credential egress.** A configured `A2A_BEARER_TOKEN` was attached to whatever
 *     `baseUrl` the caller passed. A prompt-injected or mistaken call to an
 *     attacker-chosen host handed that host the operator's credential.
 *  2. **SSRF.** A `baseUrl` — or an interface URL named by a remote agent card — could
 *     point at loopback, link-local, or private-range addresses reachable from the
 *     Claude Code host. The card audit *reported* those, but the protocol client used
 *     them anyway, so "report, never adopt" was true of the audit and false of the wire.
 *
 * The rules, both fail-closed:
 *
 *  - **Destination.** Private, loopback, link-local, and carrier-grade-NAT addresses are
 *    refused unless `A2A_ALLOW_PRIVATE_HOSTS=1`. Hostnames are resolved and every
 *    returned address is checked, so a public name that resolves inward is refused too.
 *  - **Credentials.** A credential is attached ONLY to a host listed in
 *    `A2A_ALLOWED_HOSTS`. With no allowlist configured, no credential is ever sent —
 *    the operator must nominate where their token may go.
 *
 * Residual risk, stated rather than papered over: the address check happens before the
 * request, so a name that changes resolution between the check and the connect (DNS
 * rebinding) is not covered. Closing that needs a pinned-IP dialer, which the SDK's
 * `fetch` seam does not expose.
 */

import { lookup } from 'node:dns/promises';
import { isIP } from 'node:net';

export interface GuardConfig {
  /** Hosts a credential may be sent to. Empty means no credential is ever sent. */
  allowedHosts: Set<string>;
  /** Permit loopback/private/link-local destinations (local development only). */
  allowPrivateHosts: boolean;
  /** Header name for the credential, e.g. `Authorization`. */
  authHeaderName: string;
  /** The credential value, already formatted (e.g. `Bearer xyz`). Empty means none held. */
  authHeaderValue: string;
}

export function configFromEnv(env: NodeJS.ProcessEnv = process.env): GuardConfig {
  const bearer = env.A2A_BEARER_TOKEN ?? '';
  const apiKey = env.A2A_API_KEY ?? '';
  return {
    allowedHosts: new Set(
      (env.A2A_ALLOWED_HOSTS ?? '')
        .split(',')
        .map((h) => h.trim().toLowerCase())
        .filter(Boolean),
    ),
    allowPrivateHosts: env.A2A_ALLOW_PRIVATE_HOSTS === '1',
    authHeaderName: env.A2A_AUTH_HEADER_NAME ?? 'Authorization',
    authHeaderValue: bearer ? `Bearer ${bearer}` : apiKey,
  };
}

/** IPv4/IPv6 ranges that must not be reachable from a caller-supplied or card-named URL. */
export function isPrivateAddress(addr: string): boolean {
  const a = addr.toLowerCase().replace(/^\[|\]$/g, '');

  if (isIP(a) === 6) {
    if (a === '::' || a === '::1') return true;
    if (a.startsWith('fe80')) return true; // link-local
    if (/^f[cd]/.test(a)) return true; // unique-local fc00::/7
    // IPv4-mapped (::ffff:10.0.0.1) — check the embedded v4 address.
    const mapped = a.match(/^::ffff:(\d+\.\d+\.\d+\.\d+)$/);
    if (mapped) return isPrivateAddress(mapped[1]);
    return false;
  }

  const parts = a.split('.').map(Number);
  if (parts.length !== 4 || parts.some((n) => !Number.isInteger(n) || n < 0 || n > 255)) {
    return false;
  }
  const [p0, p1] = parts;
  if (p0 === 0) return true; // "this network"
  if (p0 === 10) return true; // private
  if (p0 === 127) return true; // loopback
  if (p0 === 169 && p1 === 254) return true; // link-local (incl. cloud metadata 169.254.169.254)
  if (p0 === 172 && p1 >= 16 && p1 <= 31) return true; // private
  if (p0 === 192 && p1 === 168) return true; // private
  if (p0 === 100 && p1 >= 64 && p1 <= 127) return true; // carrier-grade NAT
  if (p0 >= 224) return true; // multicast + reserved
  return false;
}

export class BlockedDestinationError extends Error {
  constructor(host: string, reason: string) {
    super(
      `a2a-client refused an outbound request to "${host}": ${reason}. ` +
        `Set A2A_ALLOW_PRIVATE_HOSTS=1 to permit private destinations (local development only).`,
    );
    this.name = 'BlockedDestinationError';
  }
}

/** Resolve a hostname and refuse if ANY returned address is private. */
export async function assertDestinationAllowed(
  url: URL,
  cfg: GuardConfig,
  resolver: (host: string) => Promise<string[]> = defaultResolve,
): Promise<void> {
  if (cfg.allowPrivateHosts) return;
  const host = url.hostname.toLowerCase();

  if (isIP(host)) {
    if (isPrivateAddress(host)) throw new BlockedDestinationError(host, 'private or loopback address');
    return;
  }
  if (host === 'localhost' || host.endsWith('.localhost') || host.endsWith('.local')) {
    throw new BlockedDestinationError(host, 'loopback hostname');
  }

  let addresses: string[];
  try {
    addresses = await resolver(host);
  } catch (e) {
    throw new BlockedDestinationError(host, `DNS resolution failed (${(e as Error).message})`);
  }
  const bad = addresses.find(isPrivateAddress);
  if (bad) {
    throw new BlockedDestinationError(host, `resolves to a private or loopback address (${bad})`);
  }
}

async function defaultResolve(host: string): Promise<string[]> {
  const results = await lookup(host, { all: true });
  return results.map((r) => r.address);
}

/** A credential is attached only to a host the operator explicitly nominated. */
export function shouldSendCredential(url: URL, cfg: GuardConfig): boolean {
  if (!cfg.authHeaderValue) return false;
  if (cfg.allowedHosts.size === 0) return false; // fail closed — nominate a host first
  return cfg.allowedHosts.has(url.hostname.toLowerCase());
}

/**
 * Wrap `fetch` so every outbound request — card resolution, protocol calls, and anything
 * the SDK does internally — passes the destination check, and carries a credential only
 * when the destination is nominated.
 */
export function createGuardedFetch(
  cfg: GuardConfig,
  fetchImpl: typeof fetch = fetch,
  resolver?: (host: string) => Promise<string[]>,
): typeof fetch {
  type FetchInput = Parameters<typeof fetch>[0];
  return async function guardedFetch(input: FetchInput, init?: RequestInit) {
    const raw =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.href
          : (input as { url: string }).url;
    const url = new URL(raw);

    await assertDestinationAllowed(url, cfg, resolver);

    if (!shouldSendCredential(url, cfg)) {
      return fetchImpl(input, init);
    }
    const headers = new Headers(
      init?.headers ?? (typeof input === 'object' && 'headers' in input ? input.headers : undefined),
    );
    headers.set(cfg.authHeaderName, cfg.authHeaderValue);
    return fetchImpl(input, { ...init, headers });
  } as typeof fetch;
}
