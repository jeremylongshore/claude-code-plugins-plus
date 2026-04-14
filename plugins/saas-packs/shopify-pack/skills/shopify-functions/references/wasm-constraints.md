Shopify Functions WASM sandbox constraints and workarounds.

## Hard Limits

| Constraint | Limit | Notes |
|-----------|-------|-------|
| Execution time | 11ms | Wall-clock time per invocation |
| Memory | 1MB | Linear memory available to WASM module |
| Binary size | 256KB | Compiled `.wasm` file maximum |
| Network access | None | No HTTP, no fetch, no external calls |
| File system | None | No disk reads or writes |
| Standard library | Limited | No threads, no async, no random |
| Input size | 64KB | Serialized input from the input query |
| Output size | 64KB | Serialized FunctionRunResult |

## What This Means in Practice

### No Network Calls
Functions cannot call external APIs at runtime. All configuration must be pre-loaded via:
- **Metafields** on the discount/customization node (set by app, read in input query)
- **Input query data** from the cart, customer, and product graph

### No Large Dependencies
Libraries like `lodash`, `moment`, or `date-fns` will blow the 256KB limit. Alternatives:
- Write vanilla TypeScript/JavaScript utilities
- Use Rust for smaller binary sizes (~50-100KB typical vs ~150-200KB for JS via Javy)
- Tree-shake aggressively: import only what you need

### Memory Constraints
```typescript
// BAD: Allocating large arrays
const allVariants = input.cart.lines.flatMap(l => /* ... */);  // Could exceed 1MB

// GOOD: Process line by line
for (const line of input.cart.lines) {
  // Process each line individually
}
```

## Language Comparison

| Factor | TypeScript (Javy) | Rust |
|--------|-------------------|------|
| Binary size | 150-200KB typical | 50-100KB typical |
| Compile speed | Fast | Slower |
| Ecosystem | Familiar to most devs | Smaller community |
| Performance | Good | Better (native WASM) |
| Debugging | Source maps available | WASM debug info |
| Shopify CLI support | Full (`shopify app function build`) | Full (Cargo-based) |

## Workarounds for Common Patterns

### Dynamic Configuration
```typescript
// Store config in metafields, read via input query
// input.graphql:
// discountNode { metafield(namespace: "$app:config", key: "rules") { value } }

const config = JSON.parse(input.discountNode?.metafield?.value ?? "{}");
// { "min_quantity": 3, "percentage": "15.0", "excluded_tags": ["final-sale"] }
```

### Complex Logic That Exceeds Limits
If your logic is too complex for the WASM sandbox:
1. Pre-compute results in your app backend on a schedule
2. Store computed values as metafields on products/variants
3. Function reads pre-computed metafields via input query (simple lookup, fast execution)

### Testing Locally
```bash
# Generate test input matching your input query
shopify app function run --input test-input.json

# Run with verbose output
shopify app function run --input test-input.json --export run

# Profile execution time
time shopify app function run --input test-input.json
```

### Debugging Size Issues
```bash
# Check WASM binary size after build
ls -la dist/function.wasm

# If using Rust, check what's contributing to size
cargo bloat --release --wasm

# If using TypeScript, check bundled dependencies
npx source-map-explorer dist/function.js
```
