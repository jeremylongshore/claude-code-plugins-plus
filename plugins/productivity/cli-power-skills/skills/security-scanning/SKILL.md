---
name: security-scanning
description: "Use when checking code for vulnerabilities, linting shell scripts, scanning containers or IaC for security issues, or managing encrypted secrets"
allowed-tools: [Bash(trivy*), Bash(shellcheck*), Bash(sops*), Read, Glob]
version: 1.0.0
author: ykotik
license: MIT
---

# Security Scanning

## When to Use
- Scanning a project directory for known vulnerabilities (CVEs)
- Scanning a container image before deployment
- Scanning Infrastructure-as-Code (Terraform, CloudFormation) for misconfigurations
- Linting shell scripts for bugs, pitfalls, and unsafe patterns
- Encrypting or decrypting secrets stored in YAML/JSON config files
- Checking dependencies for known security issues

## Tools

| Tool | Purpose | Structured output |
|------|---------|-------------------|
| **Trivy** | Vulnerability scanner for filesystems, containers, IaC | `--format json` or `--format sarif` |
| **ShellCheck** | Static analysis and linting for shell scripts | `-f json` for JSON output |
| **sops** | Encrypt/decrypt secrets in YAML, JSON, ENV files | Outputs decrypted file to stdout |

## Patterns

### Scan project directory for vulnerabilities
```bash
trivy fs --format json --output results.json .
```

### Scan project and show results in terminal
```bash
trivy fs --severity HIGH,CRITICAL .
```

### Scan a container image
```bash
trivy image --format json --output scan.json nginx:latest
```

### Scan Terraform files for misconfigurations
```bash
trivy config --format json .
```

### Scan a lockfile (package-lock.json, requirements.txt, etc.)
```bash
trivy fs --scanners vuln --format json package-lock.json
```

### Generate SARIF report for CI integration
```bash
trivy fs --format sarif --output report.sarif .
```

### Lint a shell script with JSON output
```bash
shellcheck -f json script.sh
```

### Lint all shell scripts in a directory
```bash
shellcheck -f json *.sh scripts/*.sh
```

### Lint with specific severity threshold
```bash
shellcheck -S warning -f json script.sh
```

### Encrypt a secrets file with sops (using age key)
```bash
sops --encrypt --age $(cat ~/.config/sops/age/keys.txt | grep "public key:" | awk '{print $NF}') secrets.yaml > secrets.enc.yaml
```

### Decrypt a secrets file to stdout
```bash
sops --decrypt secrets.enc.yaml
```

### Edit encrypted file in-place
```bash
sops secrets.enc.yaml
```

### Decrypt a single value
```bash
sops --decrypt --extract '["database"]["password"]' secrets.enc.yaml
```

## Pipelines

### Scan and summarize critical findings
```bash
trivy fs --format json . | jq '[.Results[] | .Vulnerabilities[]? | select(.Severity == "CRITICAL") | {id: .VulnerabilityID, pkg: .PkgName, title: .Title}]'
```
Each stage: Trivy scans and outputs JSON, jq filters to critical vulnerabilities and extracts key fields.

### Lint all shell scripts and count issues by severity
```bash
shellcheck -f json scripts/*.sh | jq 'group_by(.level) | map({level: .[0].level, count: length})'
```
Each stage: ShellCheck lints all scripts to JSON, jq groups and counts by severity level.

### Scan image and fail if critical vulns found
```bash
trivy image --format json myapp:latest | jq -e '[.Results[] | .Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length == 0'
```
Each stage: Trivy scans image, jq checks for critical vulns and exits non-zero if any found.

## Prefer Over
- Prefer **Trivy** over manual `npm audit` / `pip audit` — scans all ecosystems in one pass
- Prefer **ShellCheck** over manual review for shell scripts — catches subtle quoting, globbing, and portability bugs
- Prefer **sops** over storing plaintext secrets — encryption at rest with version control compatibility

## Do NOT Use When
- Reviewing business logic or application design flaws — these tools find known CVEs and script bugs, not logic errors
- Linting Python code — use Ruff (python-tooling skill) instead
- Linting JavaScript/TypeScript — use ESLint or Biome directly
- Managing runtime secrets (use Vault or environment variables for that)
