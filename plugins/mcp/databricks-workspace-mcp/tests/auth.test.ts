import { describe, expect, it } from "vitest";
import { resolveAuth, normalizeHost, detectDeployment } from "../src/auth.js";
import { DatabricksError } from "../src/errors.js";
import { jsonResponse, recordingFetch } from "./helpers.js";

const HOST = "https://dbc-test.cloud.databricks.com";

describe("normalizeHost", () => {
  it("adds https and strips trailing slashes", () => {
    expect(normalizeHost("dbc-x.cloud.databricks.com/")).toBe("https://dbc-x.cloud.databricks.com");
    expect(normalizeHost("https://dbc-x.cloud.databricks.com//")).toBe("https://dbc-x.cloud.databricks.com");
  });
  it("rejects empty host", () => {
    expect(() => normalizeHost("   ")).toThrow(DatabricksError);
  });
});

describe("detectDeployment", () => {
  it("defaults to cli", () => {
    expect(detectDeployment({})).toBe("cli");
  });
  it("detects app mode from explicit override or app port", () => {
    expect(detectDeployment({ DATABRICKS_WORKSPACE_MCP_MODE: "app" })).toBe("app");
    expect(detectDeployment({ DATABRICKS_APP_PORT: "8000" })).toBe("app");
  });
});

describe("resolveAuth — CLI flows", () => {
  it("PAT", async () => {
    const a = resolveAuth({ env: { DATABRICKS_HOST: HOST, DATABRICKS_TOKEN: "dapiX" } });
    expect(a.deployment).toBe("cli");
    expect(a.provider.mode).toBe("pat");
    expect(await a.provider.getToken()).toBe("dapiX");
  });

  it("OAuth U2M (supplied token)", async () => {
    const a = resolveAuth({ env: { DATABRICKS_HOST: HOST, DATABRICKS_OAUTH_TOKEN: "u2m-abc" } });
    expect(a.provider.mode).toBe("u2m");
    expect(await a.provider.getToken()).toBe("u2m-abc");
  });

  it("PAT wins over M2M when both present (CLI precedence)", () => {
    const a = resolveAuth({
      env: { DATABRICKS_HOST: HOST, DATABRICKS_TOKEN: "dapiX", DATABRICKS_CLIENT_ID: "id", DATABRICKS_CLIENT_SECRET: "sec" },
    });
    expect(a.provider.mode).toBe("pat");
  });

  it("throws structured config error when host missing", () => {
    try {
      resolveAuth({ env: { DATABRICKS_TOKEN: "dapiX" } });
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(DatabricksError);
      expect((e as DatabricksError).kind).toBe("config");
    }
  });

  it("throws structured auth error when no credentials", () => {
    try {
      resolveAuth({ env: { DATABRICKS_HOST: HOST } });
      expect.unreachable();
    } catch (e) {
      expect((e as DatabricksError).kind).toBe("auth");
    }
  });
});

describe("resolveAuth — OAuth M2M (client credentials)", () => {
  it("exchanges client credentials for a bearer and caches until expiry", async () => {
    const { fetchImpl, calls } = recordingFetch(() =>
      jsonResponse({ access_token: "m2m-token-1", expires_in: 3600, token_type: "Bearer" }),
    );
    let t = 0;
    const a = resolveAuth({
      env: { DATABRICKS_HOST: HOST, DATABRICKS_CLIENT_ID: "id", DATABRICKS_CLIENT_SECRET: "sec" },
      fetchImpl,
      now: () => t,
    });
    expect(a.provider.mode).toBe("m2m");
    expect(await a.provider.getToken()).toBe("m2m-token-1");
    // cached — no second token call
    expect(await a.provider.getToken()).toBe("m2m-token-1");
    expect(calls.length).toBe(1);
    expect(calls[0].url).toBe(`${HOST}/oidc/v1/token`);
    expect(calls[0].headers.authorization).toMatch(/^Basic /);
    expect(calls[0].body).toContain("grant_type=client_credentials");
    // advance past expiry -> refetch
    t = 3_600_000;
    await a.provider.getToken();
    expect(calls.length).toBe(2);
  });

  it("surfaces an auth error when the token endpoint rejects", async () => {
    const { fetchImpl } = recordingFetch(() => jsonResponse({ error: "invalid_client" }, { status: 401 }));
    const a = resolveAuth({
      env: { DATABRICKS_HOST: HOST, DATABRICKS_CLIENT_ID: "id", DATABRICKS_CLIENT_SECRET: "bad" },
      fetchImpl,
    });
    await expect(a.provider.getToken()).rejects.toMatchObject({ kind: "auth", status: 401 });
  });
});

describe("resolveAuth — App mode (OAuth M2M only)", () => {
  it("rejects PAT cleanly in app mode", () => {
    try {
      resolveAuth({ deployment: "app", env: { DATABRICKS_HOST: HOST, DATABRICKS_TOKEN: "dapiX" } });
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(DatabricksError);
      expect((e as DatabricksError).kind).toBe("auth");
      expect((e as DatabricksError).message).toMatch(/not supported in Databricks App/i);
    }
  });

  it("accepts M2M in app mode", () => {
    const a = resolveAuth({
      deployment: "app",
      env: { DATABRICKS_HOST: HOST, DATABRICKS_CLIENT_ID: "id", DATABRICKS_CLIENT_SECRET: "sec" },
    });
    expect(a.deployment).toBe("app");
    expect(a.provider.mode).toBe("m2m");
  });

  it("requires M2M creds in app mode", () => {
    expect(() => resolveAuth({ deployment: "app", env: { DATABRICKS_HOST: HOST } })).toThrow(DatabricksError);
  });
});
