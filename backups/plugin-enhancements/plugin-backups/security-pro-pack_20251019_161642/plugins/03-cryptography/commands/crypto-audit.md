---
description: Reviews cryptographic implementations for security vulnerabilities
shortcut: ca
category: security
difficulty: intermediate
estimated_time: 10-20 minutes
---

<!-- DESIGN DECISION: Crypto Audit as automated cryptographic code review -->
<!-- Identifies common crypto mistakes before they reach production -->
<!-- Complements Crypto Expert (guidance) with automated detection (audit) -->

<!-- VALIDATION: Tested against OWASP crypto vulnerabilities and CWE crypto weaknesses -->
<!-- Successfully detected weak algorithms, IV reuse, unauthenticated encryption -->

# Cryptography Audit

Automatically reviews cryptographic implementations in your codebase to identify weak algorithms, improper key management, and common cryptographic vulnerabilities.

## What This Command Does

**Automated Crypto Code Review:**
-  Detects weak or broken algorithms (MD5, SHA-1, DES, RC4)
-  Identifies insufficient key sizes (RSA <2048-bit, AES <128-bit)
-  Finds hardcoded keys and secrets
-  Checks for proper IV generation and usage
-  Verifies authenticated encryption usage
-  Validates TLS/SSL configurations

**Output:** Crypto audit report with severity-rated findings and remediation steps

**Time:** 10-20 minutes per codebase

---

## When to Use This Command

**Perfect For:**
- Pre-commit crypto review
- Security code review automation
- Compliance requirement (crypto standards)
- After adding crypto functionality
- Regular security audits

**Use This When:**
- Implementing encryption or hashing
- Reviewing third-party crypto code
- Preparing for security audit
- Responding to crypto vulnerabilities
- Onboarding new crypto libraries

---

## Usage

```bash
# Audit current directory
/crypto-audit

# Audit specific file
/crypto-audit src/crypto/encryption.js

# Audit with detailed output
/crypto-audit --verbose

# Audit and generate report
/crypto-audit --output crypto-report.md
```

**Shortcut:**
```bash
/ca  # Quick crypto audit
```

---

## What Gets Audited

### 1. Weak Algorithms (Critical)

**Detects:**
- MD5 hashing (completely broken)
- SHA-1 hashing (collision attacks)
- DES encryption (56-bit key, easily brute-forced)
- RC4 stream cipher (biases in keystream)
- ECB mode (pattern leakage)

**Example Finding:**
```python
#  CRITICAL: MD5 password hashing detected
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# Location: auth/password.py:45
# Severity: Critical
# CWE: CWE-327 (Use of Broken Crypto Algorithm)

# Impact: MD5 collisions can be generated in seconds
# Attacker can create password with same hash

# Remediation:
import argon2
password_hash = argon2.hash(password)
```

### 2. Insufficient Key Sizes (High)

**Checks:**
- RSA key size (minimum 2048-bit, recommend 3072-bit)
- AES key size (minimum 128-bit, recommend 256-bit)
- Elliptic curve key size (minimum 256-bit)

**Example Finding:**
```javascript
// ️ HIGH: RSA key size insufficient
const key = crypto.generateKeyPairSync('rsa', {
  modulusLength: 1024  // TOO SMALL! Easily factored
})

// Location: services/encryption.js:23
// Severity: High
// CWE: CWE-326 (Inadequate Encryption Strength)

// Fix: Increase to 3072-bit
const key = crypto.generateKeyPairSync('rsa', {
  modulusLength: 3072  // Secure for next 10+ years
})
```

### 3. Hardcoded Secrets (Critical)

**Finds:**
- Hardcoded encryption keys
- Embedded API keys
- Fixed salts or IVs
- Hardcoded passwords

**Example Finding:**
```javascript
//  CRITICAL: Hardcoded encryption key
const ENCRYPTION_KEY = "MySecretKey123456789012345678901"

// Location: config/crypto.js:12
// Severity: Critical
// CWE: CWE-798 (Hardcoded Credentials)

// Impact: If source code leaks, all encrypted data compromised

// Fix: Use environment variables
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY
if (!ENCRYPTION_KEY) throw new Error('Missing ENCRYPTION_KEY')
```

### 4. IV/Nonce Issues (High)

**Detects:**
- Reused initialization vectors
- Predictable IVs
- Missing IVs for CBC mode
- Zero IVs

**Example Finding:**
```python
# ️ HIGH: Fixed IV reuse
IV = b'1234567890123456'  # Same IV every time!

# Location: crypto/aes.py:34
# Severity: High
# CWE: CWE-329 (Not Using Random IV with CBC)

# Impact: Reveals patterns in encrypted data
# First block of identical plaintexts produce identical ciphertexts

# Fix: Generate random IV per encryption
IV = os.urandom(16)
```

### 5. Unauthenticated Encryption (High)

**Checks for:**
- AES-CBC without HMAC
- CTR mode without authentication
- Missing auth tags

**Example Finding:**
```javascript
// ️ HIGH: Encryption without authentication
const cipher = crypto.createCipheriv('aes-256-cbc', key, iv)

// Location: api/encrypt.js:56
// Severity: High
// CWE: CWE-353 (Missing Support for Integrity Check)

// Impact: Attacker can modify ciphertext without detection
// Padding oracle attacks possible

// Fix: Use GCM mode (authenticated encryption)
const cipher = crypto.createCipheriv('aes-256-gcm', key, iv)
```

### 6. Insecure Random (Critical)

**Detects:**
- Non-crypto random for security tokens
- Predictable random number generators
- Unseeded random

**Example Finding:**
```python
#  CRITICAL: Insecure random for crypto
import random
token = ''.join([random.choice(string.ascii_letters) for _ in range(32)])

# Location: auth/tokens.py:67
# Severity: Critical
# CWE: CWE-330 (Insufficient Randomness)

# Impact: Tokens are predictable, can be guessed by attacker

# Fix: Use cryptographically secure random
import secrets
token = secrets.token_urlsafe(32)
```

### 7. TLS/SSL Misconfigurations (Medium)

**Checks:**
- TLS version (minimum 1.2)
- Weak cipher suites
- Certificate validation disabled
- Self-signed certificates in production

**Example Finding:**
```javascript
//  MEDIUM: Certificate validation disabled
const https = require('https')

https.get('https://api.example.com', {
  rejectUnauthorized: false  // Dangerous!
}, callback)

// Location: api/client.js:89
// Severity: Medium
// CWE: CWE-295 (Certificate Validation Failure)

// Impact: Vulnerable to man-in-the-middle attacks

// Fix: Enable certificate validation
https.get('https://api.example.com', {
  rejectUnauthorized: true  // Default, but be explicit
}, callback)
```

---

## Example: Full Audit Report

```bash
$ /crypto-audit

 Running Cryptography Audit...

 Project: payment-processor
 Files scanned: 89
⏱️  Scan duration: 12.3 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CRITICAL FINDINGS (Fix Immediately)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Hardcoded Encryption Key
    File: config/encryption.js:15
    Severity: Critical
   CWE: CWE-798

   const AES_KEY = "hardcoded_key_32_chars_long!"

   ️  Impact: All encrypted data compromised if source code leaks

    Fix:
   - Move to environment variable: process.env.AES_KEY
   - Rotate encryption key immediately
   - Re-encrypt existing data with new key

2. MD5 Password Hashing
    File: auth/password.py:45
    Severity: Critical
   CWE: CWE-327

   password_hash = hashlib.md5(password.encode()).hexdigest()

   ️  Impact: Passwords easily cracked via rainbow tables

    Fix:
   import argon2
   password_hash = argon2.hash(password)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
️  HIGH SEVERITY FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. RSA Key Too Small (1024-bit)
    File: crypto/keys.js:23
    Severity: High

   modulusLength: 1024

   ️  Impact: Can be factored with current computing power

    Fix: Increase to 3072-bit minimum

4. AES-CBC Without Authentication
    File: services/encrypt.js:67
    Severity: High

   cipher = crypto.createCipheriv('aes-256-cbc', key, iv)

   ️  Impact: Padding oracle attacks, ciphertext tampering

    Fix: Use AES-256-GCM (authenticated encryption)

5. Fixed IV Reuse
    File: utils/crypto.py:34
    Severity: High

   IV = b'1234567890123456'

   ️  Impact: Reveals patterns in encrypted data

    Fix: Generate random IV: os.urandom(16)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MEDIUM SEVERITY FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. TLS 1.0 Enabled
    File: nginx.conf:45
    Severity: Medium

   ssl_protocols TLSv1 TLSv1.1 TLSv1.2;

   ️  Impact: Vulnerable to POODLE, BEAST attacks

    Fix: Disable TLS 1.0/1.1, enable only 1.2+

7. SHA-1 for Digital Signatures
    File: crypto/sign.js:89
    Severity: Medium

   .sign('sha1')

   ️  Impact: SHA-1 collisions possible (SHAttered attack)

    Fix: Use SHA-256 or SHA-512

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 AUDIT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Findings: 7
  Critical: 2 (Fix immediately)
  High: 3 (Fix within 1 week)
  Medium: 2 (Fix within 1 month)

Estimated Fix Time: 6-8 hours

Priority Actions:
1. Remove hardcoded keys (2 hours)
2. Upgrade password hashing (3 hours)
3. Increase RSA key size (1 hour)
4. Switch to GCM mode (2 hours)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Immediate Actions:
 Fix 2 critical issues within 24 hours
 Rotate compromised encryption keys
 Audit production data for exposure

Short-term:
 Address high-severity findings
 Update crypto libraries to latest versions
 Implement key management system (AWS KMS, Vault)

Long-term:
 Automated crypto auditing in CI/CD
 Regular crypto library updates
 Team cryptography training

 For detailed remediation help, ask Crypto Expert:
   "How do I migrate from MD5 to Argon2 for existing users?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Audit completed successfully! 
Report saved to: crypto-audit-2025-10-10.md
```

---

## Severity Levels

** Critical (Fix Within 24 Hours)**
- Hardcoded keys/secrets
- Completely broken algorithms (MD5, DES, RC4)
- No encryption where required (plaintext PHI, PCI)
- Insecure random for crypto

** High (Fix Within 1 Week)**
- Weak key sizes (RSA <2048, AES <128)
- Unauthenticated encryption
- IV reuse or predictable IVs
- SHA-1 in security-critical contexts

** Medium (Fix Within 1 Month)**
- Deprecated algorithms (TLS 1.0/1.1)
- Missing certificate validation
- SHA-1 in non-critical contexts
- Weak cipher suites

** Low (Improvement)**
- AES-128 (upgrade to AES-256)
- bcrypt cost factor <12
- Missing crypto documentation

---

## CI/CD Integration

```yaml
# GitHub Actions
name: Crypto Audit

on: [push, pull_request]

jobs:
  crypto_audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Crypto Audit
        run: /crypto-audit --output crypto-report.md

      - name: Fail on Critical Issues
        run: |
          if grep -q " Critical" crypto-report.md; then
            echo "Critical crypto issues found!"
            exit 1
          fi
```

---

## False Positives

**Test Crypto:**
```python
# Audit may flag test credentials
TEST_KEY = "test_key_only"  # Used in tests only

# Solution: Add comment
# CRYPTO_AUDIT_IGNORE: Test key, not used in production
TEST_KEY = "test_key_only"
```

**Legacy Code:**
```javascript
// Old code using MD5 for non-security purpose (checksums)
const checksum = crypto.createHash('md5').update(data).digest('hex')

// Solution: Clarify usage
// CRYPTO_AUDIT_IGNORE: MD5 for checksum only, not security
const checksum = crypto.createHash('md5').update(data).digest('hex')
```

---

## Related Commands

- `/security-scan-quick` - General security scan (includes crypto)
- Ask **Crypto Expert** - Detailed crypto guidance
- `/docker-security-scan` - Container crypto checks

---

## Support

**Found crypto vulnerabilities?**
1. Prioritize by severity (critical → high → medium)
2. For remediation help: Ask Crypto Expert
3. For complex issues: Email security team
4. Test fixes with: `/crypto-audit` (re-run after fixes)

---

**Time Investment:** 10-20 minutes per scan
**Value:** Prevent crypto vulnerabilities that lead to data breaches

**Audit crypto early. Fix vulnerabilities fast. Protect data properly.** 
