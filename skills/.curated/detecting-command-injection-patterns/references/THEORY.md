# Command-Injection Theory

## The recurring shape

Application calls out to a binary for some task: image processing,
archive extraction, video conversion, DNS resolution, network ping,
"call this one CLI tool." The naive implementation builds a string,
passes it to a shell-invocation API. The shell parses the string
with full shell semantics: `;`, `|`, `&`, `$()`, backticks,
redirection.

The fix is universal: don't go through the shell. Most APIs have
a list-of-arguments form that bypasses the shell entirely, treating
each list element as a literal argument to the binary's `execve()`.

## Why `shell=True` is the default footgun

Python's `subprocess.run(["ls", "-la"])` is safe — `argv` is passed
to `execve()` directly. `subprocess.run("ls -la", shell=True)` is
NOT safe because the string goes through `/bin/sh -c`.

The footgun: the list form looks more verbose. New engineers
default to the string form because it reads like the shell
command they're used to typing. `shell=True` becomes a
convenience reflex, then becomes a habit, then ships.

Same pattern in every language:

- Node `exec("cmd arg")` (shell) vs `spawn("cmd", ["arg"])` (no shell)
- Ruby `` `cmd #{var}` `` (shell) vs `Open3.capture3("cmd", var)` (no shell)
- Go `exec.Command("sh", "-c", cmd)` (shell) vs `exec.Command("cmd", arg)` (no shell)
- Java `Runtime.exec(String)` (shell-tokenized) vs `Runtime.exec(String[])` (no shell)
- PHP `system($cmd)` (shell) vs `pcntl_exec($cmd, [$arg])` (no shell)

## The argument-vector vs command-string distinction

When the OS executes a process via `execve()`, it takes an
**argument vector** — an array of strings. The first element is the
program path; subsequent elements are arguments.

A shell-interpreted command string gets tokenized into argv by the
shell, applying shell rules: word splitting on whitespace, glob
expansion, variable substitution, command substitution, quoting,
escape sequences, control operators.

The injection vector is exactly this tokenization step. If you
build a string `convert input.jpg output.png` and the attacker
controls `input.jpg`, they substitute `input.jpg; rm -rf /`. The
shell sees two commands separated by `;`.

If you build an argv `["convert", input_filename, output_filename]`
and pass it to `execve()` directly, the attacker substituting
`input.jpg; rm -rf /` as `input_filename` results in a single
argv element with a literal semicolon in it. `convert` receives
that as a filename argument, sees no such file, returns an error.
No second command runs.

## When you DO need a shell (rare)

Some legitimate use cases require shell semantics:

1. **Pipe between two commands.** `cmd1 | cmd2` requires a shell
   to set up the pipe. Use the list-form Popen with `stdin=` /
   `stdout=` to chain processes without a shell.

2. **Shell glob expansion.** `cmd /tmp/*.log` requires shell to
   expand the glob. Better: use Python's `glob.glob()` /
   Node's `glob` package / etc. to expand to a list, then pass
   that list as argv.

3. **Environment variable expansion in the command string.**
   `cmd $HOME/foo` requires shell. Better: read the env var in
   your application code, pass the expanded string as an argv
   element.

In every "I need shell semantics" case, the right fix is to move
the shell-semantic operation into your application code, then
call out to the binary with explicit argv.

## Per-language idioms

### Python — `subprocess` is the right module

```python
import subprocess

# UNSAFE — shell builds the string
subprocess.run(f"convert {filename} out.png", shell=True)

# SAFE — argv list, no shell
subprocess.run(["convert", filename, "out.png"])

# SAFE — input/output redirection via subprocess args, not shell
with open("out.txt", "w") as f:
    subprocess.run(["my-command"], stdout=f)
```

`subprocess.run()` and `subprocess.Popen()` both accept a list
argument and default to `shell=False`. Use them.

### Node.js — `child_process.spawn` over `exec`

```javascript
const { spawn, execFile } = require('child_process');

// UNSAFE — shell builds the string
const child = exec(`convert ${filename} out.png`);

// SAFE — argv list, no shell
const child = spawn('convert', [filename, 'out.png']);

// SAFE — execFile is also no-shell by default
execFile('convert', [filename, 'out.png'], (err, stdout) => { ... });
```

### Ruby — `Open3.capture3` over backticks

```ruby
require 'open3'

# UNSAFE — backticks invoke shell
output = `convert #{filename} out.png`

# SAFE — argv list
stdout, stderr, status = Open3.capture3('convert', filename, 'out.png')

# SAFE — Process.spawn list form
pid = Process.spawn('convert', filename, 'out.png')
```

### Go — `exec.Command` with explicit args

```go
import "os/exec"

// UNSAFE — shell wrapper
cmd := exec.Command("sh", "-c", fmt.Sprintf("convert %s out.png", filename))

// SAFE — argv form (Command's default)
cmd := exec.Command("convert", filename, "out.png")
```

### Java — `ProcessBuilder` with array

```java
import java.lang.ProcessBuilder;

// UNSAFE — Runtime.exec(String) tokenizes via shell-like rules
Runtime.getRuntime().exec("convert " + filename + " out.png");

// SAFE — ProcessBuilder with explicit list
ProcessBuilder pb = new ProcessBuilder("convert", filename, "out.png");
Process p = pb.start();
```

### PHP — `escapeshellarg` or `proc_open` with explicit argv

PHP's standard shell-invocation APIs (`system`, `exec`, `passthru`,
`shell_exec`) all go through the shell. Either escape every argument
or use `proc_open` with bypass_shell.

```php
// UNSAFE
system("convert $filename out.png");

// PARTIAL FIX — escapeshellarg quotes special chars
system("convert " . escapeshellarg($filename) . " out.png");

// SAFER — proc_open with bypass_shell
$descriptors = [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
$process = proc_open(
    ['convert', $filename, 'out.png'],  // PHP 7.4+ supports array form
    $descriptors,
    $pipes
);
```

## False-positive patterns

Pre-validated allow-lists make the shell-string call safe by
construction:

```python
ALLOWED_OUTPUT_FORMATS = {"png", "jpg", "webp"}
if output_format not in ALLOWED_OUTPUT_FORMATS:
    raise ValueError()
# `output_format` is now constrained to a known-safe set
subprocess.run(f"convert {filename} out.{output_format}", shell=True)
```

The `shell=True` is still flagged by the regex scanner, but the
finding is a false positive after allow-list validation. The
scanner can't reason about allow-list validation; the human
reader can.

That said: even with allow-list validation, the no-shell form is
strictly safer. There's no operational reason to keep the
shell-wrapper if the no-shell form works.

## Primary sources

- [CWE-78 Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- [OWASP A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [OWASP Command Injection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)
- [Python subprocess docs — Security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [Node.js child_process docs](https://nodejs.org/api/child_process.html)
