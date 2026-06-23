#!/usr/bin/env node
/**
 * databricks-workspace-mcp — stdio entry (CLI / `.mcp.json` consumption).
 *
 * Resolves Databricks credentials from the environment (PAT / OAuth U2M token / OAuth M2M),
 * builds a lazy client provider, and serves the control-plane tools over stdio. Credentials are
 * resolved lazily: the server starts and lists tools even when unconfigured, and only a tool
 * *call* returns a structured auth error — so the consuming skill can detect "MCP present but
 * not authenticated" and degrade cleanly.
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer, SERVER_NAME, SERVER_VERSION } from "./server.js";
import { makeClientProvider, probeAuth } from "./runtime.js";

async function main(): Promise<void> {
  const getClient = makeClientProvider();
  const server = createServer(getClient);
  await server.connect(new StdioServerTransport());

  const auth = probeAuth();
  if (auth) {
    console.error(
      `${SERVER_NAME} v${SERVER_VERSION} running (${auth.deployment} mode, ${auth.provider.mode} auth) -> ${auth.host}`,
    );
  } else {
    console.error(
      `${SERVER_NAME} v${SERVER_VERSION} running UNAUTHENTICATED — set DATABRICKS_HOST + a credential (DATABRICKS_TOKEN / DATABRICKS_OAUTH_TOKEN / DATABRICKS_CLIENT_ID+SECRET). tools/list works; tools/call will return an auth error until configured.`,
    );
  }
}

main().catch((err) => {
  console.error(`[${SERVER_NAME}] fatal:`, err instanceof Error ? err.message : err);
  process.exit(1);
});
