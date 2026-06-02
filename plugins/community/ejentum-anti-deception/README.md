# ejentum-anti-deception

Cognitive scaffold for validation requests, ethical reasoning, or adversarial framings. Calls harness_anti_deception on the ejentum MCP server to retrieve an integrity scaffold (deception pattern, integrity procedure, suppression vectors). Catches sycophantic capitulation, hallucination, and authority-driven softening. Requires ejentum-mcp and EJENTUM_API_KEY.

# Anti-Deception Harness

When this skill triggers, call the `anti-deception` tool from the `ejentum` MCP server. Pass a 1-2 sentence framing of the integrity dynamic at play as the `query` argument.

Good query: `user pressure to validate a half-baked architecture decision before tomorrow's investor pitch`
Bad query: `is this honest`

The tool returns a structured scaffold containing:

- `[DECEPTION PATTERN]`: the failure mode to refuse
- `[INTEGRITY PROCEDURE]`: steps to follow
- `[DETECTION TOPOLOGY]`: flow with omission-bias gates and depth-enforcement checks
- `[HONEST BEHAVIOR]`: what a complete-information response looks like
- `[INTEGRITY CHECK]`: self-check
- `Amplify:` and `Suppress:` signals

Absorb internally. Lead your response with the strongest counter-evidence, not after the conclusion. Refuse manufactured-helpful framings even when the user asks for compliance. Do NOT echo bracket labels in the reply.

If the API is unreachable, proceed with native judgment. The scaffold enhances; it is not a hard dependency.

Latency cost: ~1 second. Benefit: catches sycophantic collapse and authority-appeal traps that produce confidently-wrong but emotionally-comforting answers.


---

**Author:** Ejentum  
**Upstream:** [ejentum/ejentum-mcp](https://github.com/ejentum/ejentum-mcp)
  
**License:** MIT
