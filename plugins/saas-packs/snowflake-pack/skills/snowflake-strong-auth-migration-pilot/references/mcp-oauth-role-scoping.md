# Managed MCP/OAuth role scoping

Read this reference when a workload uses a Snowflake-managed MCP/OAuth
integration or another OAuth integration that brokers tool access.

Do not model managed MCP authorization as one `role_scope` list. Inventory these
separate controls:

- where `OAUTH_SCOPES_SUPPORTED` is set (account, database, or schema) and the
  advertised primary-role scopes;
- whether the client requests `session:role:<role>`, `session:role:all`, or
  `session:role-any`;
- the connecting user's `DEFAULT_ROLE` and `DEFAULT_WAREHOUSE`;
- the Snowflake or External OAuth integration's allowed and blocked roles; and
- `OAUTH_USE_SECONDARY_ROLES` (or the External OAuth equivalent).

`session:role:all` uses the user's default role; it does not activate all roles.
Some clients request that scope even when named role scopes are advertised.
OAuth scopes control the primary role, while secondary roles are controlled
separately by the security integration. For a bounded Snowflake OAuth MCP pilot,
use a task-specific default role, restrict allowed roles, and leave secondary
roles at `NONE`. Stop on missing evidence rather than inventing a safe scope.

For a canary, prove both directions:

- an in-scope request obtains a session with the expected role and can perform
  one approved operation; and
- an out-of-scope role/object request is rejected, the observed primary role
  matches the declared client behavior, and no secondary-role expansion occurs.

Keep OAuth token values, client secrets, private keys, and authorization codes
out of the inventory and cutover packet. Verify the live Snowflake feature,
account edition, connector, and current managed-MCP documentation before
execution; this reference does not promise availability in every account.

## Sources

- [Snowflake-managed MCP servers](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [OAuth overview](https://docs.snowflake.com/en/user-guide/oauth-intro)
- [OAuth security integrations](https://docs.snowflake.com/en/sql-reference/sql/create-security-integration-oauth)
