# Agent Safety Preflight decision rules

Use these rules when the bundled scanner is unavailable or when a human asks how the receipt was classified.

## Green

Return Green only when git state is clean and no high-risk automation markers are present in the inspected local files.

## Yellow

Return Yellow when any of these are true:

- Git state is dirty or unavailable.
- Agent hooks, broad tool permissions, MCP server configuration, or other agent authority surfaces are present without destructive or credential-writing evidence.
- The scanner cannot inspect enough of the workspace to make a clean Green call.

## Red

Return Red and stop before editing when any of these are true:

- Destructive recursive delete patterns appear in scripts, hooks, commands, or agent-controlled paths.
- Credential-writing automation appears in an actual environment or secret-assignment context.
- Shell or network install chains run from agent-controlled paths without a clear local-only safety boundary.

## Evidence discipline

Report file paths and short markers only. Do not paste secrets, tokens, private source, environment values, or payment credentials into the receipt.
