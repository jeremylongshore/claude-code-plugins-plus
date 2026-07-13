# Command-Injection Remediation Playbook

The universal pattern: switch to the argument-vector form of your
language's process-spawn API. Specific snippets per language below.

## Python — subprocess (list form, shell=False)

### Before

```python
import subprocess
subprocess.run(f"convert {filename} out.png", shell=True)
```

### After

```python
import subprocess
subprocess.run(["convert", filename, "out.png"], check=True)
```

### Piping between commands without shell

```python
# Before (shell pipeline)
subprocess.run(f"cat {filename} | grep error", shell=True)

# After (Popen chain)
with subprocess.Popen(["cat", filename], stdout=subprocess.PIPE) as p1:
    subprocess.run(["grep", "error"], stdin=p1.stdout, check=True)
```

### Capturing output

```python
result = subprocess.run(
    ["convert", filename, "out.png"],
    capture_output=True, text=True, check=True,
)
print(result.stdout)
```

## Node.js — child_process spawn / execFile

### Before

```javascript
const { exec } = require('child_process');
exec(`convert ${filename} out.png`, (err, stdout) => {});
```

### After (execFile)

```javascript
const { execFile } = require('child_process');
execFile('convert', [filename, 'out.png'], (err, stdout) => {});
```

### After (spawn for streaming)

```javascript
const { spawn } = require('child_process');
const child = spawn('convert', [filename, 'out.png']);
child.stdout.on('data', chunk => process.stdout.write(chunk));
child.on('close', code => console.log(`exit ${code}`));
```

### TypeScript with promisify

```typescript
import { execFile as execFileCallback } from 'child_process';
import { promisify } from 'util';
const execFile = promisify(execFileCallback);

const { stdout } = await execFile('convert', [filename, 'out.png']);
```

## Ruby — Open3.capture3 / Process.spawn

### Before

```ruby
output = `convert #{filename} out.png`
```

### After (Open3 — best for capturing output)

```ruby
require 'open3'
stdout, stderr, status = Open3.capture3('convert', filename, 'out.png')
raise "convert failed: #{stderr}" unless status.success?
```

### After (Process.spawn for fire-and-forget)

```ruby
pid = Process.spawn('convert', filename, 'out.png')
Process.wait(pid)
```

### After (system with explicit args)

```ruby
# system with multiple args bypasses shell
system('convert', filename, 'out.png') or raise "convert failed"
```

## Go — exec.Command with argv

### Before

```go
cmd := exec.Command("sh", "-c", fmt.Sprintf("convert %s out.png", filename))
output, _ := cmd.CombinedOutput()
```

### After

```go
cmd := exec.Command("convert", filename, "out.png")
output, err := cmd.CombinedOutput()
if err != nil {
    return fmt.Errorf("convert failed: %w", err)
}
```

### With context (cancellation / timeout)

```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
cmd := exec.CommandContext(ctx, "convert", filename, "out.png")
```

## Java — ProcessBuilder with array

### Before

```java
Runtime.getRuntime().exec("convert " + filename + " out.png");
```

### After

```java
ProcessBuilder pb = new ProcessBuilder("convert", filename, "out.png");
pb.redirectErrorStream(true);
Process p = pb.start();
int exitCode = p.waitFor();
```

### With output capture

```java
try (BufferedReader reader = new BufferedReader(
        new InputStreamReader(p.getInputStream()))) {
    String line;
    while ((line = reader.readLine()) != null) {
        System.out.println(line);
    }
}
```

## PHP — proc_open with array form

PHP 7.4+ supports passing an array as the command to `proc_open`,
which bypasses shell entirely:

### Before

```php
$output = shell_exec("convert $filename out.png");
```

### After (PHP 7.4+)

```php
$descriptors = [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w'],
];
$process = proc_open(
    ['convert', $filename, 'out.png'],
    $descriptors,
    $pipes
);
$stdout = stream_get_contents($pipes[1]);
fclose($pipes[1]);
proc_close($process);
```

### Legacy PHP fallback (with escapeshellarg)

```php
$cmd = sprintf(
    "convert %s %s",
    escapeshellarg($filename),
    escapeshellarg($outputName)
);
$output = shell_exec($cmd);
```

`escapeshellarg()` wraps the argument in single quotes and escapes
any embedded single quotes. Defense-in-depth; the no-shell form
is still stricter.

## C# / .NET — Process.Start with ArgumentList

### Before

```csharp
Process.Start("cmd.exe", "/c convert " + filename + " out.png");
```

### After (.NET Core 2.1+)

```csharp
var psi = new ProcessStartInfo("convert")
{
    UseShellExecute = false,
    RedirectStandardOutput = true,
};
psi.ArgumentList.Add(filename);
psi.ArgumentList.Add("out.png");
var process = Process.Start(psi);
```

`ArgumentList` (not `Arguments` string) is the safe path.

## Rust — std::process::Command

```rust
use std::process::Command;

// Safe by design — Command takes args separately
let output = Command::new("convert")
    .arg(&filename)
    .arg("out.png")
    .output()
    .expect("convert failed");
```

`std::process::Command` doesn't have a shell-wrapped form. Even if
you wanted one, you'd have to explicitly invoke `sh -c` yourself.

## Pre-commit integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: scan-cmdi
        name: Scan for command-injection patterns
        entry: python3 plugins/security/penetration-tester/skills/detecting-command-injection-patterns/scripts/scan_cmdi.py
        language: system
        args: ['--min-severity', 'high']
        pass_filenames: false
```

## CI integration

```yaml
- name: Command-injection scan
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-command-injection-patterns/scripts/scan_cmdi.py \
        . --min-severity high --format json --output cmdi-scan.json
- run: |
    if jq 'length > 0' cmdi-scan.json | grep -q true; then
      echo "::error::Command-injection pattern detected"
      cat cmdi-scan.json
      exit 1
    fi
```

## Defense-in-depth additions

For code that legitimately shells out to a binary:

1. **Run the binary as a low-privilege user.** Container-isolated,
   no write access to host paths.
2. **Validate inputs against an allow-list before passing.**
   Filenames matching `^[\w.-]+\.(png|jpg|webp)$`; refuse anything
   else.
3. **Drop unused capabilities.** Linux: capset to drop network,
   raw-socket, etc. for the spawned process.
4. **Use a dedicated processing queue.** Untrusted file processing
   should run in a sandboxed worker, not the application server's
   main process.

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-command-injection-patterns/scripts/scan_cmdi.py \
    /path/to/repo --min-severity medium
```

Expected: exit 0, zero MEDIUM-or-higher findings. Remaining LOW
findings on `shell=True` with verified static-string arguments are
acceptable but should be migrated when the surrounding code is
touched anyway.
