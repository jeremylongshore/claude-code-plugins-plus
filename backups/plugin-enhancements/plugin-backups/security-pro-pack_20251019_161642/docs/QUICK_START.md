# Quick Start Guide - Security Pro Pack

**Get started with Security Pro Pack in under 10 minutes**

---

## Your First Security Scan (2 Minutes)

The fastest way to start is with a quick security scan of your current project:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Run quick security scan
/security-scan-quick
# or use shortcut:
/ss
```

**What happens:**
- Scans for hardcoded secrets (API keys, passwords)
- Checks dependencies for known CVEs
- Identifies insecure configurations
- Reports severity-rated findings (Critical → Low)

**Expected output:**
```
 Running Quick Security Scan...
 Project: my-app
 Files scanned: 127
⏱️  Scan duration: 4.2 seconds

Total Issues: 8
  Critical: 2 (Fix immediately)
  High: 3 (Fix before production)
  Medium: 3 (Improve security posture)
```

**Next steps:** Fix critical issues first, then re-run `/ss` to verify.

---

## Common Workflows

### Workflow 1: Pre-Deployment Security Check (5 Minutes)

Before deploying to production:

```bash
# Step 1: Quick scan
/ss

# Step 2: Docker container scan (if using containers)
/dss myapp:latest

# Step 3: API security audit (if building APIs)
/asa https://staging-api.example.com

# Step 4: Review findings
cat security-scan-report.md
```

**Pass Criteria:**
- Zero critical issues
- All high-severity issues resolved or documented
- Docker containers running as non-root
- APIs have rate limiting and authentication

---

### Workflow 2: Compliance Documentation (10 Minutes)

Generate compliance documentation for audit preparation:

```bash
# Generate HIPAA documentation
/compliance-docs-generate --framework hipaa

# Generate GDPR documentation
/compliance-docs-generate --framework gdpr

# Generate PCI DSS documentation
/compliance-docs-generate --framework pci

# Review generated files
ls -la compliance-docs/
```

**Output:** Complete policy and procedure documents ready for audit review.

---

### Workflow 3: Code Review for Security (15 Minutes)

Perform comprehensive security review of new code:

```bash
# Step 1: Ask Security Auditor Expert for OWASP review
# In Claude Code session:
```
> "Please perform a security audit using the Security Auditor Expert on the authentication module in src/auth/"

```bash
# Step 2: Review cryptography implementation
/ca src/crypto/

# Step 3: Threat model new features
# Ask Threat Modeler agent:
```
> "Can you threat model our new payment processing flow using STRIDE?"

**Result:** Comprehensive security analysis covering OWASP Top 10, cryptography, and architectural threats.

---

## Plugin Reference - Quick Access

### Commands (Use with `/` prefix)

| Command | Shortcut | Purpose | Time |
|---------|----------|---------|------|
| `/security-scan-quick` | `/ss` | Fast vulnerability scan | 2-5 min |
| `/compliance-docs-generate` | `/cdg` | Generate compliance docs | 15-30 min |
| `/crypto-audit` | `/ca` | Review cryptographic code | 10-20 min |
| `/docker-security-scan` | `/dss` | Scan container images | 5-10 min |
| `/api-security-audit` | `/asa` | Audit REST/GraphQL APIs | 15-30 min |

### Agents (Ask Claude to activate)

| Agent | Trigger Words | Purpose |
|-------|---------------|---------|
| **Security Auditor Expert** | "security audit", "OWASP" | Comprehensive vulnerability analysis |
| **Penetration Tester** | "pen test", "ethical hacking" | Offensive security testing |
| **Compliance Checker** | "HIPAA", "PCI DSS", "GDPR" | Regulatory compliance review |
| **Crypto Expert** | "encryption", "cryptography" | Cryptographic implementation guidance |
| **Threat Modeler** | "threat model", "STRIDE" | Architectural security design |

---

## Example: First Security Audit

**Scenario:** You're about to deploy a new feature and want to ensure it's secure.

**Step-by-Step:**

1. **Quick scan** to identify obvious issues:
   ```bash
   /ss src/features/new-feature/
   ```

2. **Ask Security Auditor Expert** for OWASP review:
   > "Please review src/features/new-feature/api.js for OWASP Top 10 vulnerabilities"

3. **Review cryptography** (if using crypto):
   ```bash
   /ca src/features/new-feature/
   ```

4. **Threat model** the feature:
   > "Can you threat model the new user authentication flow using STRIDE methodology?"

5. **Fix identified issues** based on findings

6. **Re-scan** to verify fixes:
   ```bash
   /ss src/features/new-feature/
   ```

**Time investment:** 20-30 minutes
**Value:** Prevent security vulnerabilities before production deployment

---

## Best Practices

### Daily Workflow

```bash
# Before committing code
/ss  # Quick scan

# If changes include crypto
/ca  # Crypto audit

# If changes include containers
/dss myapp:latest  # Docker scan
```

### Weekly Workflow

```bash
# Comprehensive security review
# Ask Security Auditor Expert:
```
> "Please perform a full security audit of the codebase covering OWASP Top 10"

```bash
# Review all containers
/dss --all-images
```

### Monthly Workflow

```bash
# Update compliance documentation
/cdg --framework all

# Full threat model review
# Ask Threat Modeler:
```
> "Review our entire application architecture for security threats using STRIDE"

---

## Tips for Effective Use

**1. Start Small**
- Begin with `/ss` (quick scan) on one directory
- Fix critical issues first
- Gradually expand to full codebase

**2. Use Shortcuts**
- `/ss` instead of `/security-scan-quick`
- `/ca` instead of `/crypto-audit`
- Saves time for frequent operations

**3. Integrate with CI/CD**
- Add `/ss` to pre-commit hooks
- Run `/dss` in Docker build pipeline
- Include `/asa` in deployment pipeline

**4. Ask Agents for Help**
- Use agents for complex analysis
- Commands for quick automated checks
- Combine both for comprehensive coverage

**5. Document Findings**
- Save reports: `/ss --output report.md`
- Track fixes in issue tracker
- Share with team for awareness

---

## Next Steps

Now that you're familiar with basic usage:

1. **Explore Use Cases** - See `USE_CASES.md` for 7 real-world scenarios
2. **Customize Workflows** - Adapt examples to your team's needs
3. **Integrate CI/CD** - Automate security scanning in deployment pipelines
4. **Train Team** - Share Quick Start with teammates

---

## Need Help?

- **Troubleshooting:** See `TROUBLESHOOTING.md`
- **Full Documentation:** See `README.md`
- **Support:** [email protected]

---

**You're all set!** Start securing your code with the Security Pro Pack. 
