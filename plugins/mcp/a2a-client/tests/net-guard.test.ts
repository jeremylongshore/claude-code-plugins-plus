import { describe, expect, it, vi } from 'vitest';
import {
  BlockedDestinationError,
  MAX_REDIRECTS,
  assertDestinationAllowed,
  configFromEnv,
  createGuardedFetch,
  isPrivateAddress,
  shouldSendCredential,
  type GuardConfig,
} from '../servers/net-guard.js';

function cfg(over: Partial<GuardConfig> = {}): GuardConfig {
  return {
    allowedHosts: new Set(),
    allowPrivateHosts: false,
    authHeaderName: 'Authorization',
    authHeaderValue: '',
    ...over,
  };
}

/** Resolver stub so tests never touch real DNS. */
const resolves = (map: Record<string, string[]>) => async (h: string) => {
  if (!(h in map)) throw new Error(`no stub for ${h}`);
  return map[h];
};

describe('isPrivateAddress', () => {
  it.each([
    '127.0.0.1',
    '10.1.2.3',
    '192.168.1.1',
    '172.16.0.1',
    '172.31.255.255',
    '169.254.169.254', // cloud instance metadata — the classic SSRF target
    '100.64.0.1', // carrier-grade NAT / tailnet range
    '0.0.0.0',
    '::1',
    'fe80::1',
    'fd00::1',
    '::ffff:10.0.0.1', // IPv4-mapped IPv6 must not be a bypass
  ])('flags %s as private', (addr) => {
    expect(isPrivateAddress(addr)).toBe(true);
  });

  it.each(['8.8.8.8', '1.1.1.1', '93.184.216.34', '172.32.0.1', '2606:4700::1111'])(
    'allows public %s',
    (addr) => {
      expect(isPrivateAddress(addr)).toBe(false);
    },
  );
});

describe('assertDestinationAllowed', () => {
  it('refuses a literal loopback address', async () => {
    await expect(
      assertDestinationAllowed(new URL('https://127.0.0.1/a2a'), cfg(), resolves({})),
    ).rejects.toBeInstanceOf(BlockedDestinationError);
  });

  it('refuses localhost by name without a DNS round trip', async () => {
    await expect(
      assertDestinationAllowed(new URL('https://localhost:8443/a2a'), cfg(), resolves({})),
    ).rejects.toThrow(/loopback hostname/);
  });

  it('refuses a public NAME that resolves inward — the rebinding-style bypass', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://evil.example.com/a2a'),
        cfg(),
        resolves({ 'evil.example.com': ['169.254.169.254'] }),
      ),
    ).rejects.toThrow(/resolves to a private or loopback address/);
  });

  it('refuses when ANY resolved address is private, not just the first', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://mixed.example.com/a2a'),
        cfg(),
        resolves({ 'mixed.example.com': ['93.184.216.34', '10.0.0.5'] }),
      ),
    ).rejects.toBeInstanceOf(BlockedDestinationError);
  });

  it('refuses when DNS fails rather than falling open', async () => {
    await expect(
      assertDestinationAllowed(new URL('https://nx.example.com/a2a'), cfg(), resolves({})),
    ).rejects.toThrow(/DNS resolution failed/);
  });

  it('allows a public destination', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://agents.example.com/a2a'),
        cfg(),
        resolves({ 'agents.example.com': ['93.184.216.34'] }),
      ),
    ).resolves.toBeUndefined();
  });

  it('permits private destinations only under the explicit opt-in', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('http://127.0.0.1:41777/a2a'),
        cfg({ allowPrivateHosts: true }),
        resolves({}),
      ),
    ).resolves.toBeUndefined();
  });
});

describe('shouldSendCredential — fail closed', () => {
  it('sends nothing when no credential is held', () => {
    expect(
      shouldSendCredential(new URL('https://a.example.com'), cfg({ allowedHosts: new Set(['a.example.com']) })),
    ).toBe(false);
  });

  it('sends nothing when a credential is held but NO allowlist is configured', () => {
    expect(
      shouldSendCredential(new URL('https://a.example.com'), cfg({ authHeaderValue: 'Bearer t' })),
    ).toBe(false);
  });

  it('does not send to a host outside the allowlist', () => {
    expect(
      shouldSendCredential(
        new URL('https://attacker.example.com'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(false);
  });

  it('sends to a nominated host', () => {
    expect(
      shouldSendCredential(
        new URL('https://partner.example.com/a2a'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(true);
  });

  it('matches host case-insensitively', () => {
    expect(
      shouldSendCredential(
        new URL('https://Partner.Example.com/a2a'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(true);
  });
});

describe('createGuardedFetch', () => {
  const ok = () => new Response('{}', { status: 200 });
  type FetchArgs = [Parameters<typeof fetch>[0], RequestInit | undefined];

  it('blocks the request before it reaches fetch', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(cfg(), inner as unknown as typeof fetch, resolves({}));
    await expect(g('https://10.0.0.9/a2a')).rejects.toBeInstanceOf(BlockedDestinationError);
    expect(inner).not.toHaveBeenCalled();
  });

  it('does NOT attach a credential to a non-nominated host', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({ authHeaderValue: 'Bearer secret', allowedHosts: new Set(['partner.example.com']) }),
      inner as unknown as typeof fetch,
      resolves({ 'attacker.example.com': ['93.184.216.34'] }),
    );
    await g('https://attacker.example.com/a2a');
    expect(inner).toHaveBeenCalledOnce();
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init!.headers).get('Authorization')).toBeNull();
  });

  it('attaches the credential to a nominated host', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({ authHeaderValue: 'Bearer secret', allowedHosts: new Set(['partner.example.com']) }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init!.headers).get('Authorization')).toBe('Bearer secret');
  });

  it('honours a custom auth header name', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({
        authHeaderName: 'X-Api-Key',
        authHeaderValue: 'k123',
        allowedHosts: new Set(['partner.example.com']),
      }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init!.headers).get('X-Api-Key')).toBe('k123');
  });

  // --- Redirect handling. Each of these fails if `redirect: 'manual'` and the
  // per-hop re-check are removed, which is exactly what they exist to pin.
  const redirectTo = (loc: string, status = 302) =>
    new Response(null, { status, headers: { location: loc } });

  it("never lets the runtime follow redirects — always requests redirect: 'manual'", async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(init?.redirect).toBe('manual');
  });

  it('refuses a redirect into cloud instance metadata (the 169.254.169.254 bypass)', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('http://169.254.169.254/latest/meta-data/'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
    // The hop was refused by the guard, never handed to fetch.
    expect(inner).toHaveBeenCalledOnce();
  });

  it('refuses a redirect to a host that resolves privately', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://rebind.example.com/x'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({
        'partner.example.com': ['93.184.216.34'],
        'rebind.example.com': ['10.0.0.9'],
      }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
  });

  it('drops the credential when a nominated host redirects to a non-nominated one', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://attacker.example.com/steal'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg({ authHeaderValue: 'Bearer secret', allowedHosts: new Set(['partner.example.com']) }),
      inner as unknown as typeof fetch,
      resolves({
        'partner.example.com': ['93.184.216.34'],
        'attacker.example.com': ['93.184.216.35'],
      }),
    );
    await g('https://partner.example.com/a2a');
    expect(inner).toHaveBeenCalledTimes(2);
    const [, first] = inner.mock.calls[0] as unknown as FetchArgs;
    const [, second] = inner.mock.calls[1] as unknown as FetchArgs;
    expect(new Headers(first!.headers).get('Authorization')).toBe('Bearer secret');
    expect(new Headers(second!.headers).get('Authorization')).toBeNull();
  });

  it('refuses a non-HTTP redirect scheme', async () => {
    const inner = vi.fn().mockResolvedValueOnce(redirectTo('file:///etc/passwd'));
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
  });

  it('caps redirect chains instead of looping forever', async () => {
    const inner = vi.fn(() => redirectTo('https://partner.example.com/next'));
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toThrow(/exceeded \d+ redirects/);
    expect(inner.mock.calls.length).toBeLessThanOrEqual(MAX_REDIRECTS + 1);
  });

  it('follows a permitted redirect and returns the final response', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://partner.example.com/moved'))
      .mockResolvedValue(new Response('{"ok":true}', { status: 200 }));
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    const res = await g('https://partner.example.com/a2a');
    expect(res.status).toBe(200);
    expect(inner).toHaveBeenCalledTimes(2);
  });

  it('degrades 303 to a bodyless GET', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://partner.example.com/result', 303))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a', { method: 'POST', body: '{"a":1}' });
    const [, second] = inner.mock.calls[1] as unknown as FetchArgs;
    expect(second?.method).toBe('GET');
    expect(second?.body).toBeUndefined();
  });
});

describe('configFromEnv', () => {
  it('defaults to fail-closed: no allowlist, no private hosts, no credential', () => {
    const c = configFromEnv({});
    expect(c.allowedHosts.size).toBe(0);
    expect(c.allowPrivateHosts).toBe(false);
    expect(c.authHeaderValue).toBe('');
  });

  it('parses a comma-separated allowlist, trimming and lowercasing', () => {
    const c = configFromEnv({ A2A_ALLOWED_HOSTS: ' Partner.example.com , b.example.com ' });
    expect([...c.allowedHosts]).toEqual(['partner.example.com', 'b.example.com']);
  });

  it('formats a bearer token and prefers it over a raw api key', () => {
    const c = configFromEnv({ A2A_BEARER_TOKEN: 't', A2A_API_KEY: 'k' });
    expect(c.authHeaderValue).toBe('Bearer t');
  });

  it('uses a raw api key when no bearer token is set', () => {
    expect(configFromEnv({ A2A_API_KEY: 'k' }).authHeaderValue).toBe('k');
  });

  it('only opts into private hosts on an exact "1"', () => {
    expect(configFromEnv({ A2A_ALLOW_PRIVATE_HOSTS: 'true' }).allowPrivateHosts).toBe(false);
    expect(configFromEnv({ A2A_ALLOW_PRIVATE_HOSTS: '1' }).allowPrivateHosts).toBe(true);
  });
});
