---
name: Plugin Auditor
description: Automatically audits Claude Code plugins for security vulnerabilities, best practices, CLAUDE.md compliance, and quality standards when user mentions audit plugin, security review, or best practices check. Specific to claude-code-plugins repository standards.
allowed-tools: Read, Grep, Bash
---

# Plugin Auditor

## Purpose
Automatically audits Claude Code plugins for security vulnerabilities, best practice violations, CLAUDE.md compliance, and quality standards - optimized for claude-code-plugins repository requirements.

## Trigger Keywords
- "audit plugin"
- "security review" or "security audit"
- "best practices check"
- "plugin quality"
- "compliance check"
- "plugin security"

## Audit Categories

### 1. Security Audit

**Critical Checks:**
- ❌ No hardcoded secrets (passwords, API keys, tokens)
- ❌ No AWS keys (AKIA...)
- ❌ No private keys (BEGIN PRIVATE KEY)
- ❌ No dangerous commands (rm -rf /, eval(), exec())
- ❌ No command injection vectors
- ❌ No suspicious URLs (IP addresses, non-HTTPS)
- ❌ No obfuscated code (base64 decode, hex encoding)

**Security Patterns:**
```bash
# Check for hardcoded secrets
grep -r "password\s*=\s*['\"]" --exclude-dir=node_modules
grep -r "api_key\s*=\s*['\"]" --exclude-dir=node_modules
grep -r "secret\s*=\s*['\"]" --exclude-dir=node_modules

# Check for AWS keys
grep -r "AKIA[0-9A-Z]{16}" --exclude=README.md

# Check for private keys
grep -r "BEGIN.*PRIVATE KEY" --exclude=README.md

# Check for dangerous patterns
grep -r "rm -rf /" | grep -v "/var/" | grep -v "/tmp/"
grep -r "eval\s*\(" --exclude=README.md
```

### 2. Best Practices Audit

**Plugin Structure:**
- ✅ Proper directory hierarchy
- ✅ Required files present
- ✅ Semantic versioning (x.y.z)
- ✅ Clear, concise descriptions
- ✅ Proper LICENSE file (MIT/Apache-2.0)
- ✅ Comprehensive README
- ✅ At least 5 keywords

**Code Quality:**
- ✅ No TODO/FIXME without issue links
- ✅ No console.log() in production code
- ✅ No hardcoded paths (/home/, /Users/)
- ✅ Uses `${CLAUDE_PLUGIN_ROOT}` in hooks
- ✅ Scripts have proper shebangs
- ✅ All scripts are executable

**Documentation:**
- ✅ README has installation section
- ✅ README has usage examples
- ✅ README has clear description
- ✅ Commands have proper frontmatter
- ✅ Agents have model specified
- ✅ Skills have trigger keywords

### 3. CLAUDE.md Compliance

**Repository Standards:**
- ✅ Follows plugin structure from CLAUDE.md
- ✅ Uses correct marketplace slug
- ✅ Proper category assignment
- ✅ Valid plugin.json schema
- ✅ Marketplace catalog entry exists
- ✅ Version consistency

**Skills Compliance (if applicable):**
- ✅ SKILL.md has proper frontmatter
- ✅ Description includes trigger keywords
- ✅ allowed-tools specified (if restricted)
- ✅ Clear purpose and instructions
- ✅ Examples provided

### 4. Marketplace Compliance

**Catalog Requirements:**
- ✅ Plugin listed in marketplace.extended.json
- ✅ Source path matches actual location
- ✅ Version matches plugin.json
- ✅ Category is valid
- ✅ No duplicate plugin names
- ✅ Author information complete

### 5. Git Hygiene

**Repository Practices:**
- ✅ No large binary files
- ✅ No node_modules/ committed
- ✅ No .env files
- ✅ Proper .gitignore
- ✅ No merge conflicts
- ✅ Clean commit history

### 6. MCP Plugin Audit (if applicable)

**MCP-Specific Checks:**
- ✅ Valid package.json with @modelcontextprotocol/sdk
- ✅ TypeScript configured correctly
- ✅ dist/ in .gitignore
- ✅ Proper mcp/*.json configuration
- ✅ Build scripts present
- ✅ No dependency vulnerabilities

### 7. Performance Audit

**Efficiency Checks:**
- ✅ No unnecessary file reads
- ✅ Efficient glob patterns
- ✅ No recursive loops
- ✅ Reasonable timeout values
- ✅ No memory leaks (event listeners)

### 8. Accessibility & UX

**User Experience:**
- ✅ Clear error messages
- ✅ Helpful command descriptions
- ✅ Proper usage examples
- ✅ Good README formatting
- ✅ Working demo commands

## Audit Process

When activated, I will:

1. **Security Scan**
   ```bash
   # Run security checks
   grep -r "password\|secret\|api_key" plugins/plugin-name/
   grep -r "AKIA[0-9A-Z]{16}" plugins/plugin-name/
   grep -r "BEGIN.*PRIVATE KEY" plugins/plugin-name/
   grep -r "rm -rf /" plugins/plugin-name/
   grep -r "eval\(" plugins/plugin-name/
   ```

2. **Structure Validation**
   ```bash
   # Check required files
   test -f .claude-plugin/plugin.json
   test -f README.md
   test -f LICENSE

   # Check component directories
   ls -d commands/ agents/ skills/ hooks/ mcp/ 2>/dev/null
   ```

3. **Best Practices Check**
   ```bash
   # Check for TODO/FIXME
   grep -r "TODO\|FIXME" --exclude=README.md

   # Check for console.log
   grep -r "console\.log" --exclude=README.md

   # Check script permissions
   find . -name "*.sh" ! -perm -u+x
   ```

4. **Compliance Verification**
   ```bash
   # Check marketplace entry
   jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.extended.json

   # Verify version consistency
   plugin_version=$(jq -r '.version' .claude-plugin/plugin.json)
   market_version=$(jq -r '.plugins[] | select(.name == "plugin-name") | .version' .claude-plugin/marketplace.extended.json)
   ```

5. **Generate Audit Report**

## Audit Report Format

```
🔍 PLUGIN AUDIT REPORT
Plugin: plugin-name
Version: 1.0.0
Category: security
Audit Date: 2025-10-16

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 SECURITY AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ PASSED (7/7)
- No hardcoded secrets
- No AWS keys
- No private keys
- No dangerous commands
- No command injection vectors
- HTTPS URLs only
- No obfuscated code

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 BEST PRACTICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ PASSED (10/12)
- Proper directory structure
- Required files present
- Semantic versioning
- Clear descriptions
- Comprehensive README

⚠️  WARNINGS (2)
- 3 scripts missing execute permission
  Fix: chmod +x scripts/*.sh

- 2 TODO items without issue links
  Location: commands/scan.md:45, agents/analyzer.md:67
  Recommendation: Create GitHub issues or remove TODOs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CLAUDE.MD COMPLIANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ PASSED (6/6)
- Follows plugin structure
- Uses correct marketplace slug
- Proper category assignment
- Valid plugin.json schema
- Marketplace entry exists
- Version consistency

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 QUALITY SCORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Security:        10/10 ✅
Best Practices:   8/10 ⚠️
Compliance:      10/10 ✅
Documentation:   10/10 ✅

OVERALL SCORE: 9.5/10 (EXCELLENT)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: MEDIUM
1. Fix script permissions (2 min)
2. Resolve TODO items (10 min)

Optional Improvements:
- Add more usage examples in README
- Include troubleshooting section
- Add GIF/video demo

✅ AUDIT COMPLETE
Plugin is production-ready with minor improvements needed.
```

## Severity Levels

**Critical (🔴):**
- Security vulnerabilities
- Hardcoded secrets
- Dangerous commands
- Missing required files

**High (🟠):**
- Best practice violations
- Missing documentation
- Broken functionality
- Schema violations

**Medium (🟡):**
- Code quality issues
- Missing optional features
- Performance concerns
- UX improvements

**Low (🟢):**
- Style inconsistencies
- Minor documentation gaps
- Nice-to-have features

## Auto-Fix Capabilities

I can automatically fix:
- ✅ Script permissions
- ✅ JSON formatting
- ✅ Markdown formatting
- ✅ Version sync issues

## Repository-Specific Checks

**For claude-code-plugins repo:**
- Validates against CLAUDE.md standards
- Checks marketplace integration
- Verifies category structure
- Ensures quality for featured plugins
- Checks contributor guidelines compliance

## Examples

**User says:** "Audit the security-scanner plugin"

**I automatically:**
1. Run full security scan
2. Check best practices
3. Verify CLAUDE.md compliance
4. Generate comprehensive report
5. Provide recommendations

**User says:** "Is this plugin safe to publish?"

**I automatically:**
1. Security audit (critical)
2. Marketplace compliance
3. Quality score calculation
4. Publish readiness assessment

**User says:** "Quality review before featured status"

**I automatically:**
1. Full audit (all categories)
2. Higher quality thresholds
3. Featured plugin requirements
4. Recommendation: approve/reject
