# ejentum-code

Cognitive scaffold for code generation, refactoring, or architecture tasks. Calls harness_code on the ejentum MCP server to retrieve a structured scaffold (failure pattern, procedure, correct-pattern example, verification step) the agent absorbs before generating. Requires ejentum-mcp and EJENTUM_API_KEY.

# Code Harness

When this skill triggers, call the `code` tool from the `ejentum` MCP server. Pass a 1-2 sentence framing of WHAT you are coding or reviewing as the `query` argument. Include the failure risk to avoid where possible.

Good query: `review a Python refactor that converts raise UserNotFound to silent default return; tests still pass`
Bad query: `look at this code`

The tool returns a structured scaffold containing:

- `[CODE FAILURE]`: engineering failure pattern to avoid
- `[ENGINEERING PROCEDURE]`: steps to follow
- `[REASONING TOPOLOGY]`: decision flow
- `[CORRECT PATTERN]`: shape correct code should take
- `[VERIFICATION]`: self-check
- `Amplify:` and `Suppress:` signals

Absorb internally. Do NOT echo bracket labels in the user-facing reply. Apply the scaffold's failure-pattern check against your draft before responding; if your code exhibits the named failure, rewrite.

If the API is unreachable, proceed with native engineering. The scaffold enhances; it is not a hard dependency.

Latency cost: ~1 second. Benefit: catches the kinds of behavioral changes and silent contract violations that look plausible but break under real conditions.


---

**Author:** Ejentum  
**Upstream:** [ejentum/ejentum-mcp](https://github.com/ejentum/ejentum-mcp)
  
**License:** MIT
