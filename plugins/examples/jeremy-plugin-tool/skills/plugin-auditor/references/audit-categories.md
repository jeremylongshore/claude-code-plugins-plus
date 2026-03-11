# Audit Categories

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
grep -r "rm -rf /" | grep -v "/var/" | grep -v "${CLAUDE_SKILL_DIR}/tmp/"
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