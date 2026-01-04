# Advanced Usage

This reference covers advanced commands and performance tuning for `zai-cli`.

## Raw MCP Tools

Use these when you need schemas or direct tool invocation.

- `zai-cli tools [--filter <text>] [--full] [--typescript] [--no-vision]`
- `zai-cli tool <name> [--no-vision]`
- `zai-cli call <tool> [--json <json> | --file <path> | --stdin] [--dry-run] [--no-vision]`

### Examples

```bash
zai-cli tools --filter vision --full
zai-cli tool zai.zread.search_doc --no-vision
zai-cli call zai.search.webSearchPrime --json '{"search_query":"LLM tools"}'
```

## Code Mode (TypeScript tool chains)

```bash
zai-cli code run ./chain.ts
zai-cli code eval "await call('zai.search.webSearchPrime', { search_query: 'zai cli' })"
zai-cli code interfaces
```

## Performance Tuning

### Skip vision MCP startup

```bash
zai-cli tools --no-vision
zai-cli doctor --no-vision
```

### Tool discovery cache (speeds `tools`/`tool`/`doctor`)

Defaults: enabled, 24 hour TTL.

```bash
export ZAI_MCP_TOOL_CACHE=1
export ZAI_MCP_TOOL_CACHE_TTL_MS=300000
export ZAI_MCP_CACHE_DIR="$HOME/.cache/zai-cli"
```

### Retries for transient MCP failures

```bash
# Vision-only retries (default 2)
export ZAI_MCP_VISION_RETRY_COUNT=2

# Global retries for all tools
export ZAI_MCP_RETRY_COUNT=1
```

### Timeout

```bash
export Z_AI_TIMEOUT=300000  # milliseconds
```
