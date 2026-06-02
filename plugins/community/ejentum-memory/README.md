# ejentum-memory

Cognitive scaffold for sharpening perceptions and observations across multi-turn context. Calls harness_memory on the ejentum MCP server to retrieve a perception scaffold (perception failure, detection procedure, suppression vectors) that sharpens an existing observation. Requires ejentum-mcp and EJENTUM_API_KEY.

# Memory Harness

When this skill triggers, you MUST observe first. Do not call the tool with an empty mind. If you have not formed an observation about conversation state, drift, or pattern, do not invoke this skill.

Once you have a raw observation, call the `memory` tool from the `ejentum` MCP server. Pass a 1-2 sentence framing in the format `"I noticed [observation]. This might mean [tentative interpretation]. Sharpen: [what I need help seeing deeper into]."` as the `query` argument.

Good query: `I noticed the user changed topic three times in this turn. This might mean they are avoiding the original question. Sharpen: whether the avoidance pattern is real or my projection.`
Bad query: `what does the user mean`

The tool returns a structured scaffold containing:

- `[PERCEPTION FAILURE]`: perceptual failure mode to avoid
- `[SHARPENING PROCEDURE]`: observe then classify steps
- `[PERCEPTION TOPOLOGY]`: DETECT-CLASSIFY flow
- `[CLEAR SIGNAL]`: what a sharpened perception looks like
- `[PERCEPTION CHECK]`: self-check
- `Amplify:` and `Suppress:` signals

Absorb internally. The scaffold sharpens an existing observation; it does not generate one. Do NOT echo bracket labels.

If the API is unreachable, proceed with your current perception. The scaffold enhances; it is not a hard dependency.

Latency cost: ~1 second. Benefit: distinguishes real cross-turn signals from projection.


---

**Author:** Ejentum  
**Upstream:** [ejentum/ejentum-mcp](https://github.com/ejentum/ejentum-mcp)
  
**License:** MIT
