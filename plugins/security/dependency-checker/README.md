# Dependency Checker Plugin

Check dependencies for known vulnerabilities, outdated packages, and license compliance across multiple package managers.

## Features

- **Multi-Language Support** - npm, pip, composer, gem, go modules
- **CVE Detection** - Known vulnerability scanning
- **Version Analysis** - Identify outdated packages
- **License Scanning** - Check license compatibility
- **Transitive Dependencies** - Scan entire dependency tree
- **Remediation Guidance** - Safe upgrade recommendations

## Installation

```bash
/plugin install dependency-checker@claude-code-plugins-plus
```

## Usage

```bash
# Check all dependencies
/check-deps

# Or use shortcut
/depcheck
```

## Supported Package Managers

- **Node.js**: npm, yarn, pnpm (package.json)
- **Python**: pip, pipenv, poetry (requirements.txt, Pipfile, pyproject.toml)
- **PHP**: composer (composer.json)
- **Ruby**: bundler (Gemfile)
- **Go**: go modules (go.mod)

## Report Structure

### 1. Vulnerability Summary
```
DEPENDENCY VULNERABILITIES
==========================
Total Packages: 150
Vulnerable: 5 (3.3%)
  - Critical: 1
  - High: 2
  - Medium: 2
```

### 2. Detailed Findings
```
CRITICAL: SQL Injection in sequelize
  Package: sequelize@5.21.3
  CVE: CVE-2023-22578
  CVSS: 9.8 (Critical)
  Fix: Upgrade to sequelize@6.28.0
  Command: npm install sequelize@6.28.0
```

### 3. Outdated Packages
```
OUTDATED PACKAGES
=================
express: 4.17.1 → 4.18.2 (patch, security fixes)
lodash: 4.17.19 → 4.17.21 (patch, security fixes)
react: 17.0.2 → 18.2.0 (major, breaking changes)
```

### 4. License Issues
```
LICENSE COMPLIANCE
==================
 GPL-3.0 dependencies found (3 packages)
  - my-gpl-package@1.0.0 (GPL-3.0)
  May conflict with MIT license
```

## Best Practices

- Run checks before deployments
- Update dependencies regularly (weekly/monthly)
- Test thoroughly after updates
- Use lock files for reproducible builds
- Monitor security advisories
- Document why specific versions are pinned

## Example Workflow

```bash
# 1. Check dependencies
/depcheck

# 2. Review vulnerability report

# 3. Update vulnerable packages
npm audit fix

# 4. Recheck to verify fixes
/depcheck

# 5. Run tests
npm test

# 6. Commit updated dependencies
git add package.json package-lock.json
git commit -m "fix: update vulnerable dependencies"
```

## Requirements

- Access to package manifest files
- Read access to lock files
- Network access for CVE database queries (optional)

## License

MIT License - See LICENSE file for details
