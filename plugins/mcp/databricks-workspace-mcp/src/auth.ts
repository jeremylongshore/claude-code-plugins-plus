/**
 * Authentication for the Databricks control-plane MCP server.
 *
 * Three flows, one decision tree (per 013-AT-ADEC § "Three auth flows"):
 *
 *   1. PAT          — `DATABRICKS_TOKEN`. CLI mode only.
 *   2. OAuth U2M    — a user access token minted out-of-band by `databricks auth login`
 *                     (browser flow), supplied as `DATABRICKS_OAUTH_TOKEN`, optionally with a
 *                     refresh token. CLI mode.
 *   3. OAuth M2M    — service-principal client-credentials grant
 *                     (`DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`). The ONLY flow
 *                     supported when running as a Databricks App (PAT is explicitly rejected
 *                     there — Finding 5 in 013-AT-ADEC).
 *
 * Deployment mode is detected at startup; App mode rejects PAT cleanly rather than failing
 * mid-request. All three flows resolve to a single `TokenProvider.getToken()` so the REST
 * client never has to know which flow produced the bearer.
 */

import { DatabricksError } from "./errors.js";

export type AuthMode = "pat" | "u2m" | "m2m";
export type DeploymentMode = "cli" | "app";

export type FetchLike = (
  input: string | URL,
  init?: RequestInit,
) => Promise<Response>;

export interface TokenProvider {
  readonly mode: AuthMode;
  getToken(): Promise<string>;
}

export interface ResolvedAuth {
  /** Normalized workspace base URL, e.g. https://dbc-abc.cloud.databricks.com (no trailing slash). */
  host: string;
  deployment: DeploymentMode;
  provider: TokenProvider;
}

export interface ResolveAuthOptions {
  env?: NodeJS.ProcessEnv;
  /** Injectable fetch for testing the OAuth token endpoint without a network. */
  fetchImpl?: FetchLike;
  /** Force a deployment mode (otherwise auto-detected from env). */
  deployment?: DeploymentMode;
  /** Clock injection for token-expiry testing. */
  now?: () => number;
}

/** Normalize a workspace host into `https://<host>` with no trailing slash. */
export function normalizeHost(raw: string): string {
  let h = raw.trim();
  if (!h) throw new DatabricksError({ kind: "config", message: "Empty Databricks host" });
  if (!/^https?:\/\//i.test(h)) h = `https://${h}`;
  return h.replace(/\/+$/, "");
}

/** Detect whether we are running inside a Databricks App (HTTP transport, OAuth-only). */
export function detectDeployment(env: NodeJS.ProcessEnv): DeploymentMode {
  // Databricks Apps run the server over HTTP and inject app-runtime env. We treat an explicit
  // mode override, or the presence of the App HTTP port, as the App signal.
  if (env.DATABRICKS_WORKSPACE_MCP_MODE === "app") return "app";
  if (env.DATABRICKS_APP_PORT || env.DATABRICKS_APP_URL) return "app";
  return "cli";
}

class PatTokenProvider implements TokenProvider {
  readonly mode = "pat" as const;
  constructor(private readonly token: string) {}
  async getToken(): Promise<string> {
    return this.token;
  }
}

class StaticOAuthTokenProvider implements TokenProvider {
  readonly mode = "u2m" as const;
  constructor(private readonly token: string) {}
  async getToken(): Promise<string> {
    return this.token;
  }
}

/**
 * Client-credentials (M2M) provider. Fetches and caches a short-lived access token from the
 * workspace OIDC token endpoint, refreshing ~60s before expiry.
 */
class M2mTokenProvider implements TokenProvider {
  readonly mode = "m2m" as const;
  private cached?: { token: string; expiresAt: number };

  constructor(
    private readonly host: string,
    private readonly clientId: string,
    private readonly clientSecret: string,
    private readonly fetchImpl: FetchLike,
    private readonly now: () => number,
  ) {}

  async getToken(): Promise<string> {
    if (this.cached && this.cached.expiresAt - 60_000 > this.now()) {
      return this.cached.token;
    }
    const url = `${this.host}/oidc/v1/token`;
    const basic = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString("base64");
    let resp: Response;
    try {
      resp = await this.fetchImpl(url, {
        method: "POST",
        headers: {
          Authorization: `Basic ${basic}`,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "grant_type=client_credentials&scope=all-apis",
      });
    } catch (err) {
      throw new DatabricksError({
        kind: "network",
        message: `OAuth token request failed: ${err instanceof Error ? err.message : String(err)}`,
        endpoint: "/oidc/v1/token",
        retriable: true,
      });
    }
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new DatabricksError({
        kind: "auth",
        message: `OAuth M2M token exchange failed (${resp.status}). Check DATABRICKS_CLIENT_ID/SECRET and that the service principal has workspace access. ${text}`.trim(),
        status: resp.status,
        endpoint: "/oidc/v1/token",
      });
    }
    const json = (await resp.json()) as { access_token?: string; expires_in?: number };
    if (!json.access_token) {
      throw new DatabricksError({
        kind: "auth",
        message: "OAuth M2M token response missing access_token",
        endpoint: "/oidc/v1/token",
      });
    }
    const ttlMs = (json.expires_in ?? 3600) * 1000;
    this.cached = { token: json.access_token, expiresAt: this.now() + ttlMs };
    return json.access_token;
  }
}

/**
 * Resolve credentials from the environment into a host + token provider.
 * Throws a structured `DatabricksError` (kind=auth/config) on any misconfiguration.
 */
export function resolveAuth(opts: ResolveAuthOptions = {}): ResolvedAuth {
  const env = opts.env ?? process.env;
  const fetchImpl = opts.fetchImpl ?? (globalThis.fetch as FetchLike);
  const now = opts.now ?? Date.now;
  const deployment = opts.deployment ?? detectDeployment(env);

  const rawHost = env.DATABRICKS_HOST ?? env.DATABRICKS_WORKSPACE_HOST;
  if (!rawHost) {
    throw new DatabricksError({
      kind: "config",
      message:
        "No workspace host. Set DATABRICKS_HOST (or DATABRICKS_WORKSPACE_HOST) to your workspace URL, e.g. https://dbc-xxxx.cloud.databricks.com",
    });
  }
  const host = normalizeHost(rawHost);

  const pat = env.DATABRICKS_TOKEN;
  const oauthToken = env.DATABRICKS_OAUTH_TOKEN;
  const clientId = env.DATABRICKS_CLIENT_ID;
  const clientSecret = env.DATABRICKS_CLIENT_SECRET;
  const hasM2m = Boolean(clientId && clientSecret);

  if (deployment === "app") {
    // Databricks Apps: OAuth M2M only. PAT is explicitly unsupported.
    if (pat && !hasM2m) {
      throw new DatabricksError({
        kind: "auth",
        message:
          "PAT auth (DATABRICKS_TOKEN) is not supported in Databricks App deployment mode. Provide a service principal via DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET (OAuth M2M).",
      });
    }
    if (!hasM2m) {
      throw new DatabricksError({
        kind: "auth",
        message:
          "Databricks App mode requires OAuth M2M: set DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET.",
      });
    }
    return {
      host,
      deployment,
      provider: new M2mTokenProvider(host, clientId!, clientSecret!, fetchImpl, now),
    };
  }

  // CLI mode precedence: PAT > U2M token > M2M.
  if (pat) {
    return { host, deployment, provider: new PatTokenProvider(pat) };
  }
  if (oauthToken) {
    return { host, deployment, provider: new StaticOAuthTokenProvider(oauthToken) };
  }
  if (hasM2m) {
    return {
      host,
      deployment,
      provider: new M2mTokenProvider(host, clientId!, clientSecret!, fetchImpl, now),
    };
  }

  throw new DatabricksError({
    kind: "auth",
    message:
      "No credentials. Provide one of: DATABRICKS_TOKEN (PAT), DATABRICKS_OAUTH_TOKEN (from `databricks auth login`), or DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET (OAuth M2M).",
  });
}
