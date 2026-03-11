# Langfuse Upgrade Migration - Implementation Details

## Check Current Version and Updates

```bash
# Node.js
npm list langfuse
npm outdated langfuse

# Python
pip show langfuse
pip index versions langfuse
```

## Breaking Changes by Version

### v2.x -> v3.x (TypeScript)
- `Langfuse.trace()` returns `Trace` instead of `Promise<Trace>`
- `flushAsync()` replaces `flush()` (now async)
- `observeOpenAI()` moved to main package export
- Generation `completionTokens` -> `completionTokens` (was `completion_tokens`)

### v1.x -> v2.x (Python)
- `langfuse.trace()` now returns synchronously
- Decorator `@observe()` replaces `@langfuse.observe()`
- `flush()` is now synchronous, use `shutdown()` for cleanup

## TypeScript API Changes

```typescript
// BEFORE (v2.x)
import Langfuse from "langfuse";
const trace = await langfuse.trace({ name: "test" });
await langfuse.flush();

// AFTER (v3.x)
import { Langfuse } from "langfuse";  // Named export
const trace = langfuse.trace({ name: "test" });
await langfuse.flushAsync();  // Renamed method
```

## Python API Changes

```python
# BEFORE (v1.x)
@langfuse.observe()
def my_function():
    pass

# AFTER (v2.x)
from langfuse.decorators import observe, langfuse_context

@observe()  # New decorator (no langfuse prefix)
def my_function():
    langfuse_context.update_current_observation(metadata={"key": "value"})
```

## Migration Codemod Script

```typescript
// scripts/migrate-langfuse.ts
import { Project } from "ts-morph";

const project = new Project({ tsConfigFilePath: "./tsconfig.json" });

for (const sourceFile of project.getSourceFiles()) {
  let modified = false;

  // Update imports: default to named
  for (const importDecl of sourceFile.getImportDeclarations()) {
    if (importDecl.getModuleSpecifierValue() === "langfuse") {
      const defaultImport = importDecl.getDefaultImport();
      if (defaultImport?.getText() === "Langfuse") {
        importDecl.removeDefaultImport();
        importDecl.addNamedImport("Langfuse");
        modified = true;
      }
    }
  }

  // Update flush() to flushAsync()
  sourceFile.forEachDescendant((node) => {
    if (node.getText().includes(".flush()")) {
      // Replace .flush() with .flushAsync()
      modified = true;
    }
  });

  if (modified) sourceFile.saveSync();
}
```

## Migration Tests

```typescript
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { Langfuse } from "langfuse";

describe("Langfuse Migration Tests", () => {
  let langfuse: Langfuse;

  beforeAll(() => {
    langfuse = new Langfuse({
      publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
      secretKey: process.env.LANGFUSE_SECRET_KEY!,
    });
  });

  afterAll(async () => { await langfuse.shutdownAsync(); });

  it("should create trace with new API", () => {
    const trace = langfuse.trace({ name: "migration-test", metadata: { version: "3.x" } });
    expect(trace).toBeDefined();
    expect(trace.id).toBeDefined();
  });

  it("should create generation with correct usage format", () => {
    const trace = langfuse.trace({ name: "generation-test" });
    const generation = trace.generation({ name: "test-gen", model: "gpt-4", input: [{ role: "user", content: "test" }] });
    generation.end({
      output: "response",
      usage: { promptTokens: 10, completionTokens: 20 }, // camelCase
    });
    expect(generation.id).toBeDefined();
  });

  it("should flush with new async method", async () => {
    langfuse.trace({ name: "flush-test" });
    await expect(langfuse.flushAsync()).resolves.not.toThrow();
  });
});
```

## Rollback Plan

```bash
git checkout main
npm install langfuse@2.0.0  # Previous version

# Or with lock file
git checkout HEAD -- package-lock.json
npm ci
```
