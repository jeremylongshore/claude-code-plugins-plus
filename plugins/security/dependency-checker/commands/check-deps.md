---
name: check-deps
description: Check dependencies for vulnerabilities and outdated packages
shortcut: depc
---
# Dependency Checker

Analyze project dependencies for known vulnerabilities, outdated packages, and license compliance issues.

## Analysis Process

1. **Detect Package Manager**
   - Identify package.json (npm/yarn/pnpm)
   - Identify requirements.txt/Pipfile (pip)
   - Identify composer.json (PHP)
   - Identify Gemfile (Ruby)
   - Identify go.mod (Go)

2. **Vulnerability Scanning**
   - Check against CVE databases
   - Identify known security advisories
   - Report CVSS scores
   - Check transitive dependencies

3. **Version Analysis**
   - Identify outdated packages
   - Check for available security patches
   - Report breaking vs. non-breaking updates
   - Suggest safe upgrade paths

4. **License Compliance**
   - Scan dependency licenses
   - Flag incompatible licenses
   - Report license obligations

## Report Output

Generate comprehensive dependency report with:
- Vulnerable packages with CVE details
- Outdated packages with available versions
- License compliance issues
- Recommended updates with impact analysis
- Upgrade commands for each package manager

## Best Practices

- Run before every deployment
- Update dependencies regularly
- Review transitive dependencies
- Use lock files (package-lock.json, Pipfile.lock)
- Test after updating dependencies
