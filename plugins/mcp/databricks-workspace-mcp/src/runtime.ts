/**
 * Wiring between auth resolution and the server's lazy client provider. The provider memoizes a
 * single client and re-throws the structured auth error on every call when credentials are
 * absent — so `tools/list` still works and only `tools/call` surfaces the misconfiguration.
 */

import { resolveAuth, type ResolveAuthOptions, type ResolvedAuth } from "./auth.js";
import { DatabricksClient, type DatabricksClientOptions } from "./client.js";
import type { ClientProvider } from "./server.js";

export function makeClientProvider(
  authOpts: ResolveAuthOptions = {},
  clientOpts: Partial<DatabricksClientOptions> = {},
): ClientProvider {
  let cached: DatabricksClient | null = null;
  return () => {
    if (cached) return cached;
    const auth: ResolvedAuth = resolveAuth(authOpts); // throws DatabricksError if unconfigured
    cached = new DatabricksClient({ auth, ...clientOpts });
    return cached;
  };
}

/** Best-effort auth probe for a startup log line. Returns null instead of throwing. */
export function probeAuth(authOpts: ResolveAuthOptions = {}): ResolvedAuth | null {
  try {
    return resolveAuth(authOpts);
  } catch {
    return null;
  }
}
