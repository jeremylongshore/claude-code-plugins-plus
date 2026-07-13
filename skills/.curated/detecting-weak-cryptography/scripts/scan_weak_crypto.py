#!/usr/bin/env python3
"""Static-analysis scan for weak cryptography usage.

References:
    CWE-327 Use of a Broken or Risky Cryptographic Algorithm
    CWE-330 Use of Insufficiently Random Values
    CWE-329 Not Using a Random IV with CBC Mode
    CWE-295 Improper Certificate Validation
    CWE-916 Use of Password Hash With Insufficient Computational Effort
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "detecting-weak-cryptography"

PY_PATTERNS = [
    ("Python hashlib.md5 (collision-broken)", Severity.HIGH, "CWE-327", r"\bhashlib\.md5\s*\(", "python"),
    ("Python hashlib.sha1 (collision-broken)", Severity.HIGH, "CWE-327", r"\bhashlib\.sha1\s*\(", "python"),
    (
        "Python random.random for crypto context",
        Severity.CRITICAL,
        "CWE-330",
        r"\brandom\.(?:random|randint|choice|sample)\s*\([^)]*\)[^=\n]*(?:key|token|secret|password|nonce|iv|salt)",
        "python",
    ),
    ("Python ssl verify=False", Severity.CRITICAL, "CWE-295", r"\bverify\s*=\s*False\b", "python"),
    ("Python urllib3.disable_warnings", Severity.HIGH, "CWE-295", r"\burllib3\.disable_warnings\s*\(", "python"),
    (
        "Python requests.get with verify=False",
        Severity.CRITICAL,
        "CWE-295",
        r"requests\.(?:get|post|put|delete|patch|head|options|request)\s*\([^)]*verify\s*=\s*False",
        "python",
    ),
    ("Python Cryptodome ECB mode", Severity.CRITICAL, "CWE-327", r"MODE_ECB", "python"),
    (
        "Python hashlib.sha256 for password (no KDF)",
        Severity.HIGH,
        "CWE-916",
        r"\bhashlib\.sha256\s*\([^)]*password",
        "python",
    ),
    (
        "Python Cryptodome DES / 3DES",
        Severity.CRITICAL,
        "CWE-327",
        r"from\s+Cryptodome\.Cipher\s+import\s+DES|from\s+Crypto\.Cipher\s+import\s+DES",
        "python",
    ),
]
JS_PATTERNS = [
    ("JS crypto.createHash('md5')", Severity.HIGH, "CWE-327", r"createHash\s*\(\s*['\"]md5['\"]\s*\)", "javascript"),
    ("JS crypto.createHash('sha1')", Severity.HIGH, "CWE-327", r"createHash\s*\(\s*['\"]sha1['\"]\s*\)", "javascript"),
    (
        "JS Math.random for crypto purposes",
        Severity.CRITICAL,
        "CWE-330",
        r"Math\.random\s*\(\s*\)[^=\n]*(?:key|token|secret|password|nonce|iv|salt|sessionId)",
        "javascript",
    ),
    (
        "JS axios with rejectUnauthorized:false",
        Severity.CRITICAL,
        "CWE-295",
        r"rejectUnauthorized\s*:\s*false",
        "javascript",
    ),
    (
        "JS Node tls with rejectUnauthorized:false in agent",
        Severity.CRITICAL,
        "CWE-295",
        r"new\s+https?\.Agent\s*\(\s*\{[^}]*rejectUnauthorized\s*:\s*false",
        "javascript",
    ),
    (
        "JS NODE_TLS_REJECT_UNAUTHORIZED env disable",
        Severity.CRITICAL,
        "CWE-295",
        r"NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0",
        "javascript",
    ),
    (
        "JS Cipher with 'des' / 'des-ede' / 'rc4'",
        Severity.CRITICAL,
        "CWE-327",
        r"createCipheriv?\s*\(\s*['\"](?:des|3des|des-ede|des-ede3|rc4|arc4|bf|cast)['\"]",
        "javascript",
    ),
    (
        "JS Cipher with ECB mode",
        Severity.CRITICAL,
        "CWE-327",
        r"createCipheriv?\s*\(\s*['\"][a-z0-9-]+-ecb['\"]",
        "javascript",
    ),
]
JAVA_PATTERNS = [
    ("Java MessageDigest MD5", Severity.HIGH, "CWE-327", r'MessageDigest\.getInstance\s*\(\s*"MD5"', "java"),
    ("Java MessageDigest SHA-1", Severity.HIGH, "CWE-327", r'MessageDigest\.getInstance\s*\(\s*"SHA-?1"', "java"),
    (
        "Java Cipher DES / DESede",
        Severity.CRITICAL,
        "CWE-327",
        r'Cipher\.getInstance\s*\(\s*"(?:DES|DESede)(?:/|")',
        "java",
    ),
    ("Java Cipher RC4", Severity.CRITICAL, "CWE-327", r'Cipher\.getInstance\s*\(\s*"(?:RC4|ARCFOUR)', "java"),
    ("Java Cipher ECB mode", Severity.CRITICAL, "CWE-327", r'Cipher\.getInstance\s*\(\s*"[^/]+/ECB/', "java"),
    (
        "Java new Random() (use SecureRandom for crypto)",
        Severity.HIGH,
        "CWE-330",
        r"new\s+java\.util\.Random\s*\(",
        "java",
    ),
    (
        "Java X509TrustManager always-true",
        Severity.CRITICAL,
        "CWE-295",
        r"public\s+void\s+check(?:Server|Client)Trusted\s*\([^)]*\)\s*\{\s*\}",
        "java",
    ),
    (
        "Java HostnameVerifier always-true",
        Severity.CRITICAL,
        "CWE-295",
        r"public\s+boolean\s+verify\s*\([^)]*\)\s*\{\s*return\s+true",
        "java",
    ),
]
GO_PATTERNS = [
    ("Go md5.New() for security", Severity.HIGH, "CWE-327", r"\bmd5\.New\s*\(\s*\)", "go"),
    ("Go sha1.New() for security", Severity.HIGH, "CWE-327", r"\bsha1\.New\s*\(\s*\)", "go"),
    ("Go InsecureSkipVerify: true", Severity.CRITICAL, "CWE-295", r"InsecureSkipVerify\s*:\s*true", "go"),
    ("Go DES cipher", Severity.CRITICAL, "CWE-327", r"des\.(?:NewCipher|NewTripleDESCipher)\s*\(", "go"),
    ("Go RC4 cipher", Severity.CRITICAL, "CWE-327", r"rc4\.NewCipher\s*\(", "go"),
    ("Go math/rand for crypto context", Severity.CRITICAL, "CWE-330", r'"math/rand"', "go"),
]
PHP_PATTERNS = [
    (
        "PHP md5 / sha1 for password",
        Severity.HIGH,
        "CWE-916",
        r"\b(?:md5|sha1)\s*\(\s*\$(?:password|passwd|pwd)",
        "php",
    ),
    (
        "PHP DES / 3DES cipher",
        Severity.CRITICAL,
        "CWE-327",
        r"openssl_encrypt\s*\([^,]+,\s*['\"](?:des|des-ede|des-ede3|rc4)",
        "php",
    ),
    (
        "PHP ECB cipher mode",
        Severity.CRITICAL,
        "CWE-327",
        r"openssl_encrypt\s*\([^,]+,\s*['\"][a-z0-9-]+-ecb['\"]",
        "php",
    ),
    (
        "PHP curl CURLOPT_SSL_VERIFYPEER false",
        Severity.CRITICAL,
        "CWE-295",
        r"CURLOPT_SSL_VERIFYPEER[^,)]*,\s*(?:false|0)\b",
        "php",
    ),
    (
        "PHP rand() / mt_rand() for crypto",
        Severity.CRITICAL,
        "CWE-330",
        r"\b(?:mt_)?rand\s*\([^)]*\)[^;\n]*(?:key|token|secret|password|nonce|salt)",
        "php",
    ),
]
CSHARP_PATTERNS = [
    ("C# MD5CryptoServiceProvider", Severity.HIGH, "CWE-327", r"\bMD5(?:CryptoServiceProvider|Cng)?\b", "csharp"),
    (
        "C# SHA1CryptoServiceProvider",
        Severity.HIGH,
        "CWE-327",
        r"\bSHA1(?:CryptoServiceProvider|Managed|Cng)?\b",
        "csharp",
    ),
    (
        "C# DESCryptoServiceProvider",
        Severity.CRITICAL,
        "CWE-327",
        r"\bDES(?:CryptoServiceProvider|TripleCryptoServiceProvider)?\b",
        "csharp",
    ),
    ("C# RC4 (rare; via Rijndael in ECB)", Severity.CRITICAL, "CWE-327", r"\bRC4Managed\b", "csharp"),
    ("C# Cipher mode ECB", Severity.CRITICAL, "CWE-327", r"CipherMode\.ECB", "csharp"),
    (
        "C# ServerCertificateValidationCallback returning true",
        Severity.CRITICAL,
        "CWE-295",
        r"ServicePointManager\.ServerCertificateValidationCallback\s*[=+]?=\s*(?:delegate|\([^)]*\)\s*=>\s*true)",
        "csharp",
    ),
    (
        "C# new Random() for crypto",
        Severity.HIGH,
        "CWE-330",
        r"new\s+Random\s*\(\s*\)\s*\.\s*(?:Next|NextBytes|NextDouble)\s*\([^)]*(?:key|token|secret|salt|nonce|iv)",
        "csharp",
    ),
]


LANG_EXT_MAP = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
    "java": {".java", ".kt", ".scala"},
    "go": {".go"},
    "php": {".php"},
    "csharp": {".cs"},
}
LANG_PATTERNS = {
    "python": PY_PATTERNS,
    "javascript": JS_PATTERNS,
    "java": JAVA_PATTERNS,
    "go": GO_PATTERNS,
    "php": PHP_PATTERNS,
    "csharp": CSHARP_PATTERNS,
}
SKIP_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "target",
    ".cache",
    ".pnpm-store",
    ".venv",
    "venv",
    "__pycache__",
    ".astro",
    ".next",
    ".nuxt",
    "vendor",
}
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def should_skip_path(path: Path, include_tests: bool) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    if not include_tests and parts & TEST_DIRS:
        return True
    return False


def detect_language(path: Path, langs: set[str]) -> str | None:
    suf = path.suffix.lower()
    for lang in langs:
        if suf in LANG_EXT_MAP[lang]:
            return lang
    return None


def scan_file(file_path: Path, repo_root: Path, langs: set[str], allow_md5_checksums: bool) -> list[Finding]:
    findings = []
    lang = detect_language(file_path, langs)
    if lang is None:
        return findings
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return findings
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        return findings
    try:
        rel = str(file_path.relative_to(repo_root))
    except ValueError:
        rel = str(file_path)

    for title, sev, cwe, pattern, _lang in LANG_PATTERNS[lang]:
        if allow_md5_checksums and "md5" in title.lower():
            # Heuristic: if the file path or function name suggests
            # checksum / cache / dedup, skip MD5 findings
            if re.search(r"(checksum|cache|dedup|content[_-]?hash|etag)", rel, re.I):
                continue
        for m in re.finditer(pattern, text, re.MULTILINE):
            line_no = text[: m.start()].count("\n") + 1
            snippet = text.splitlines()[line_no - 1].strip()[:160]
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"{title} at {rel}:{line_no}",
                    severity=sev,
                    target=f"{rel}:{line_no}",
                    detail=(
                        f"File {rel} line {line_no} uses {title}: `{snippet}`. "
                        "See references/THEORY.md for the algorithm's break-status "
                        "and references/PLAYBOOK.md for the modern replacement."
                    ),
                    remediation=_remediation_for(title),
                    cwe_id=cwe,
                    affected_control="OWASP A02:2021",
                    evidence=(("file", rel), ("line", line_no), ("language", lang), ("snippet", snippet)),
                )
            )
    return findings


def _remediation_for(title: str) -> str:
    if "MD5" in title or "SHA-1" in title or "sha1" in title.lower():
        return (
            "Replace MD5/SHA-1 with SHA-256 (general hashing) or "
            "BLAKE2b/SHA-3 (preferred for new code). For passwords: "
            "use bcrypt / argon2id / scrypt with a per-user salt."
        )
    if "DES" in title or "RC4" in title:
        return (
            "Replace DES / 3DES / RC4 with AES-256-GCM. The legacy "
            "ciphers are cryptographically broken; the migration is "
            "one library call away in every language."
        )
    if "ECB" in title:
        return (
            "Replace ECB mode with GCM (authenticated) or CBC + HMAC "
            "(authenticated). ECB leaks plaintext structure because "
            "identical blocks encrypt to identical ciphertext."
        )
    if "Random" in title or "rand" in title.lower():
        return (
            "Replace non-crypto random with the crypto-grade primitive. "
            "Python: `secrets.token_bytes(n)`. Node: `crypto.randomBytes(n)`. "
            "Java: `SecureRandom`. Go: `crypto/rand`. C#: "
            "`RandomNumberGenerator.Create()`. PHP: `random_bytes(n)`."
        )
    if "verify" in title.lower() or "Skip" in title or "rejectUnauthorized" in title:
        return (
            "Re-enable TLS certificate verification. If you need to "
            "trust a custom CA, install its root cert at the OS level "
            "or via the language's trust-store API. Disabling "
            "verification defeats TLS entirely."
        )
    if "password" in title.lower() and "KDF" in title:
        return (
            "Replace SHA-256(password) with bcrypt / argon2id / scrypt. "
            "Modern password hashes are designed to be expensive, "
            "salted, and resistant to GPU brute-force."
        )
    return "See references/PLAYBOOK.md for the per-language safe replacement."


def walk_repo(root: Path, include_tests: bool, langs: set[str]) -> list[Path]:
    out = []
    valid_exts = set()
    for lang in langs:
        valid_exts |= LANG_EXT_MAP[lang]
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if should_skip_path(p, include_tests):
            continue
        if p.suffix.lower() not in valid_exts:
            continue
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weak-cryptography scanner")
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--languages", default="all")
    parser.add_argument(
        "--allow-md5-checksums",
        action="store_true",
        help="Skip MD5 findings on files that look like checksum/cache code",
    )
    args = parser.parse_args(argv)

    if args.languages == "all":
        langs = set(LANG_PATTERNS.keys())
    else:
        langs = {lang.strip() for lang in args.languages.split(",") if lang.strip() in LANG_PATTERNS}

    root = args.path.resolve()
    if not root.exists():
        sys.stderr.write(f"ERROR: path does not exist: {root}\n")
        return 2

    files = walk_repo(root, args.include_tests, langs)
    findings: list[Finding] = []
    for f in files:
        findings.extend(scan_file(f, root, langs, args.allow_md5_checksums))

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, str(root))
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
