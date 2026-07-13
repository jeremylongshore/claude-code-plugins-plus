# Eval / Exec Remediation Playbook

The universal answer: replace dynamic-code execution with explicit
logic OR a sandboxed expression library. Per-language patterns
below.

## Python

### Before

```python
result = eval(user_expression)
```

### After (sandboxed expression eval)

```python
from simpleeval import simple_eval
result = simple_eval(user_expression, names={"x": 10, "y": 20})
```

### After (literal-only eval)

```python
import ast
# Only safe for literal values, NOT expressions
parsed = ast.literal_eval(user_input)  # raises on anything non-literal
```

### After (lookup table for choice)

```python
# Before: eval("function_" + name + "()")
# After: explicit dispatch
HANDLERS = {
    "process_a": process_a,
    "process_b": process_b,
}
handler = HANDLERS.get(name)
if handler is None:
    raise ValueError(f"Unknown handler: {name}")
result = handler()
```

### Dynamic class instantiation

```python
# Before: cls = eval(class_name); obj = cls()
# After:
ALLOWED_CLASSES = {
    "TypeA": TypeA,
    "TypeB": TypeB,
}
cls = ALLOWED_CLASSES[class_name]
obj = cls()
```

## JavaScript

### Before

```javascript
const result = eval(userInput);
```

### After (expression library)

```javascript
const { Parser } = require('expr-eval');
const result = Parser.evaluate(userInput, { x: 10, y: 20 });
```

### After (Function constructor → don't)

```javascript
// Before:
const fn = new Function('x', userBody);

// After: parse the function shape declaratively, never construct from string
const HANDLERS = {
    'double': (x) => x * 2,
    'square': (x) => x * x,
};
const fn = HANDLERS[userInput];
if (!fn) throw new Error('Unknown handler');
```

### setTimeout / setInterval — use function reference

```javascript
// Before
setTimeout("doThing()", 1000);

// After
setTimeout(doThing, 1000);
// or
setTimeout(() => doThing(arg), 1000);
```

### JSON parse instead of eval

```javascript
// Before
const data = eval('(' + jsonString + ')');

// After
const data = JSON.parse(jsonString);
```

## Ruby

### Before

```ruby
result = eval(user_expression)
```

### After (Dentaku for expressions)

```ruby
require 'dentaku'
calc = Dentaku::Calculator.new
result = calc.evaluate(user_expression, x: 10, y: 20)
```

### After (avoid instance_eval / class_eval on user strings)

```ruby
# Before
obj.instance_eval(user_code)

# After: define a narrow DSL, evaluate via method dispatch
ALLOWED_OPS = {
    'increment' => :increment,
    'reset' => :reset,
}
op = ALLOWED_OPS[user_input]
raise 'Unknown op' unless op
obj.send(op)
```

## PHP

### Before

```php
$result = eval($code);
```

### After: just don't

PHP's eval is uniquely dangerous because it injects into the
current scope. There's no sandboxed-eval alternative in the
standard library. Replace with explicit logic / dispatch table.

```php
$handlers = [
    'process_a' => 'process_a',
    'process_b' => 'process_b',
];
if (!isset($handlers[$name])) {
    throw new InvalidArgumentException("Unknown handler: $name");
}
$fn = $handlers[$name];
$result = $fn();
```

### assert as eval (legacy)

```php
// Before — yes really, this used to work as eval
assert($userString);

// After
// Remove. assert() now is a real assertion in PHP 7+, but old
// code that relied on the eval-form should be replaced with
// explicit dispatch as above.
```

### create_function — deprecated

```php
// Before (deprecated since PHP 7.2, removed PHP 8.0)
$fn = create_function('$x', $userBody);

// After: anonymous functions / closures with explicit body
$multiplier = function ($x) use ($factor) {
    return $x * $factor;
};
```

## Java — sandboxed scripting

### Before (Nashorn / GraalJS with full access)

```java
ScriptEngine engine = new ScriptEngineManager().getEngineByName("JavaScript");
Object result = engine.eval(userScript);
```

### After (GraalJS with restricted permissions)

```java
import org.graalvm.polyglot.*;
try (Context cx = Context.newBuilder("js")
        .allowHostAccess(HostAccess.NONE)
        .allowHostClassLookup(name -> false)
        .allowIO(false)
        .allowCreateProcess(false)
        .allowCreateThread(false)
        .build()) {
    Value result = cx.eval("js", userScript);
}
```

### Or: don't use scripting at all

For most use cases where Java code shells out to a script engine,
the right answer is to define a domain-specific configuration
format (JSON / YAML) parsed by your Java code, with the
operations dispatched via a sealed-class hierarchy.

## C# / .NET

### Avoid Type.GetType(str) for dynamic class loading

### Before

```csharp
Type t = Type.GetType(userTypeName);
object instance = Activator.CreateInstance(t);
```

### After

```csharp
// Allow-list of permitted types
static readonly IReadOnlyDictionary<string, Type> ALLOWED_TYPES =
    new Dictionary<string, Type> {
        { "TypeA", typeof(TypeA) },
        { "TypeB", typeof(TypeB) },
    };

if (!ALLOWED_TYPES.TryGetValue(userTypeName, out Type t)) {
    throw new ArgumentException($"Unknown type: {userTypeName}");
}
object instance = Activator.CreateInstance(t);
```

## Plugin system patterns (safe)

If you genuinely need to run user-supplied logic:

### Pattern 1 — WASM plugins

```rust
// Host runtime (Rust + Wasmer)
use wasmer::{Store, Module, Instance, imports};
let module = Module::new(&store, plugin_wasm_bytes)?;
let instance = Instance::new(&store, &module, &imports! {})?;
// Call exported functions; no system access by default
let result = instance.exports.get_function("process")?.call(&[input.into()])?;
```

### Pattern 2 — V8 isolate (Node.js)

```javascript
const vm = require('vm');
const context = vm.createContext({ /* explicit allow-list of globals */ });
const result = vm.runInContext(userCode, context, {
    timeout: 1000,  // hard timeout
    breakOnSigint: true,
});
```

Note: Node's `vm` module is NOT a true sandbox — there are escape
techniques. For true isolation, use a separate process or
`isolated-vm` library.

### Pattern 3 — Containerized worker

Spawn a Docker container with the user's code, read-only
filesystem, no network, memory + CPU limits, timeout. The
boundary is the container runtime, not the application process.

## Pre-commit / CI

Same pattern as previous skills:

```yaml
- name: eval/exec scan
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-eval-exec-usage/scripts/scan_eval.py \
        . --min-severity high
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-eval-exec-usage/scripts/scan_eval.py \
    /path/to/repo --min-severity medium
```

Expected: exit 0, zero MEDIUM-or-higher findings. Remaining LOW
findings (legitimate `ast.literal_eval` calls, GraalJS sandboxed
eval) are acceptable.
