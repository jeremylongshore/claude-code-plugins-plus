# Eval / Exec Theory

## Why this is the highest-impact injection class

SQL injection (skill #11) gives the attacker control over a database
query. Command injection (skill #12) gives the attacker control over
a shell process. Eval injection gives the attacker control over the
application's own interpreter, in the application's own process,
with the application's own permissions.

There's no privilege boundary between "user-supplied string" and
"arbitrary code in the application." `eval()` collapses them. Any
filtering, allow-list, or input validation that the application
does happens BEFORE the eval; the eval's interpreter sees the
filtered string and executes it. If the attacker's payload uses
language constructs the filter didn't anticipate, the filter is
bypassed by definition.

This is why "don't eval user input" is the only safe rule. There's
no "but with these escapes it's safe" version.

## When eval seems necessary

Three legitimate use cases drive the temptation:

1. **Formula evaluators.** Spreadsheet-like `=SUM(A1:A5)` cells,
   custom alerting expressions ("alert when latency > 100ms"),
   pricing-rule engines.

2. **Plugin systems.** Users supply small scripts that the
   application runs on their behalf. Examples: Lambda@Edge, Cloudflare
   Workers, custom log processors.

3. **Configuration as code.** Rare but real: a config file that's
   actually a Python / JS source file evaluated at startup.

For case 1: use a sandboxed expression library. `simpleeval` for
Python, `expr-eval` or `mathjs` for JS, `Dentaku` for Ruby. These
libraries parse a restricted grammar (math + comparison + a curated
function set) and execute it on a value model that doesn't have
filesystem / network / process access.

For case 2: run user scripts in a real sandbox: WASM
(WebAssembly with no system imports), V8 isolate (Node's vm
module with strict no-globals setup), Lua with stripped-down libs,
or a containerized worker. Don't run untrusted code in the same
process as the application.

For case 3: don't. Use JSON/YAML/TOML config. The "config as code"
flexibility argument is rarely worth the eval-injection surface.

## Why even allow-list filtering fails

A common attempt: "allow only alphanumeric + math operators in the
evaluated string."

```python
import re
if re.match(r"^[\d\+\-\*/\(\)\s\.]+$", user_input):
    result = eval(user_input)
```

This looks safe. It's not. Python's eval can:

- Use `__import__` and `__builtins__` accessors via attribute
  lookup (`().__class__.__bases__[0].__subclasses__()[X]`)
- Trigger arbitrary code through `__getattr__` on numeric types
- Call `compile()` on a sub-expression and execute that

Attackers have published "polyglot" payloads that look like pure
math but reach arbitrary functions via Python's metaprogramming.
The character-class filter is necessary-but-not-sufficient. The
ONLY safe approach is a separate interpreter that doesn't have
access to the language's full surface.

`ast.literal_eval` is safe — it ONLY parses literals (numbers,
strings, lists, dicts, tuples, booleans, None). No function calls,
no name references. Use it when you need to evaluate user-supplied
literal values; don't use it (or anything like it) for
expression evaluation more generally.

## Per-language safe patterns

### Python — simpleeval for expressions

```python
from simpleeval import simple_eval

# Safe: only basic math + curated function set
result = simple_eval("latency * 1.5 + 10", names={"latency": 80})
```

Or `asteval`:

```python
from asteval import Interpreter
aeval = Interpreter()
result = aeval("a + b * 2", symtable={"a": 1, "b": 2})
```

### JavaScript — expr-eval

```javascript
const { Parser } = require('expr-eval');
const parser = new Parser();
const expr = parser.parse('latency * 1.5 + 10');
const result = expr.evaluate({ latency: 80 });
```

### Ruby — Dentaku

```ruby
require 'dentaku'
calc = Dentaku::Calculator.new
calc.evaluate('latency * 1.5 + 10', latency: 80)
```

### Java — sandboxed Nashorn / GraalJS

```java
// GraalJS with restricted permissions
Context cx = Context.newBuilder("js")
    .allowHostAccess(HostAccess.NONE)
    .allowHostClassLookup(name -> false)
    .build();
Value result = cx.eval("js", "1 + 2");
```

## Avoid plugin-system eval

If users need to extend the application with custom logic, the
right model is:

1. Define a narrow API the plugin can call (e.g., "transform this
   payload, return a transformed version").
2. Run the plugin in an isolated sandbox: WASM with no system
   imports, V8 isolate, separate container, separate language
   runtime.
3. Apply timeouts, memory limits, syscall whitelists.

Don't `eval()` the plugin string in the application process. Even
"trusted" plugin scripts shouldn't have arbitrary access to the
host application's memory and modules.

## The pickle / serialization overlap

Python `pickle.loads()` is effectively eval-equivalent — pickle can
execute arbitrary code during deserialization. This is covered in
depth by skill #14 (`detecting-insecure-deserialization`); this
skill flags pickle usage as a cross-reference but the remediation
guidance lives in #14.

## Primary sources

- [CWE-95 Eval Injection](https://cwe.mitre.org/data/definitions/95.html)
- [Python ast.literal_eval docs](https://docs.python.org/3/library/ast.html#ast.literal_eval)
- [simpleeval — safe Python expression evaluation](https://github.com/danthedeckie/simpleeval)
- [Bandit B102 (exec_used) / B307 (eval)](https://bandit.readthedocs.io/en/latest/plugins/b102_exec_used.html)
- [OWASP Code Review Guide — Dynamic code execution](https://owasp.org/www-project-code-review-guide/)
