# Weak-Cryptography Theory

## Why "use the modern primitive" is the rule

Cryptographic primitives have a known break timeline. MD5 was
broken in 2004 (collisions in seconds on commodity hardware).
SHA-1 was broken in 2017 (shattered.io collision). DES has been
brute-forceable on dedicated hardware since the 1990s. ECB was
demonstrably insecure since the moment it was first analyzed.

Once a primitive is broken, two things follow:

1. **Attacks improve over time, never get worse.** Collision-finding
   complexity for MD5 went from 2^64 (theoretical, 2004) to 2^16
   (chosen-prefix collisions, 2010s) to "instant on a laptop"
   (multi-collision tools today).

2. **Migration becomes free.** Every modern library has the
   replacement primitive available. There's no engineering cost to
   using SHA-256 instead of MD5; both are one library call.

The fix is universally available. The only reason these
primitives still appear in source is operator inertia.

## Per-primitive break status

### MD5

Collision attacks are trivial. Length-extension attacks predate
SHA-2. Practical break in any security context: signing, integrity
verification against adversaries, password hashing.

OK uses: content-addressable storage where collisions only need to
be unlikely against benign input (not adversarial), checksums in
non-security protocols, debugging hashes.

Use SHA-256 (still no practical attacks) or BLAKE2b / SHA-3 (newer
primitives) instead.

### SHA-1

Shattered.io (2017) demonstrated chosen-prefix collisions. SHA-1
should be considered broken for all security uses.

OK uses: same as MD5 — non-security checksums.

Migrate to SHA-256.

### DES / 3DES

DES is brute-forceable on commodity hardware (effective key size:
56 bits). 3DES is computationally feasible to break with
billion-block plaintext (Sweet32 attack against 64-bit block size).
NIST disallowed 3DES for new applications in 2017.

Migrate to AES-256-GCM. Same library, different constructor.

### RC4

Multiple statistical biases in keystream make plaintext recovery
practical given enough ciphertext. Deprecated by RFC 7465 (2015).

Migrate to AES-GCM or ChaCha20-Poly1305.

### AES-ECB

Electronic Codebook mode encrypts each block independently with
the same key. Identical plaintext blocks produce identical
ciphertext blocks. The structure of the plaintext leaks through
the ciphertext (the canonical "ECB penguin" image demonstration).

Migrate to AES-GCM (authenticated encryption, single primitive),
or AES-CBC + HMAC-SHA-256 (encrypt-then-MAC pattern). GCM is
preferred for new code.

### Hardcoded IVs

CBC mode and CTR mode both require a random IV per encryption.
Reusing an IV with the same key:

- CBC: leaks whether two plaintexts share a prefix
- CTR: leaks the XOR of the two plaintexts (catastrophic)
- GCM: REPEATED IV BREAKS THE CIPHER — attacker can recover the
  authentication key

Generate a fresh random IV per encryption. Store the IV alongside
the ciphertext; it's not secret, but it must be unique-per-key.

### Custom XOR loops

The classic "I'll write my own crypto" trap. XOR-based "encryption"
with a repeating key is the Vigenère cipher with shorter alphabet;
breakable by frequency analysis with enough ciphertext.

There is no legitimate use case for hand-rolled crypto in 2026.
Use the language's library.

### Non-crypto random

`Math.random()` (JS), `random.random()` (Python without `secrets`
module), `java.util.Random` (Java), `math/rand` (Go), `rand()` /
`mt_rand()` (PHP), `new Random()` (.NET) all use deterministic
pseudo-random generators with predictable output given a small
amount of observed state.

Using these to generate:

- Session tokens → attacker predicts future tokens from one observed token
- Password reset tokens → attacker requests a reset on victim, predicts the token
- Encryption keys / IVs → attacker recreates the key from minimal observation
- CSRF tokens → attacker predicts a valid token

The fix: use the crypto-grade random API.

| Language | Crypto random |
|---|---|
| Python | `secrets.token_bytes(n)`, `secrets.token_urlsafe(n)` |
| Node | `crypto.randomBytes(n)`, `crypto.randomUUID()` |
| Java | `java.security.SecureRandom` |
| Go | `crypto/rand` (NOT `math/rand`) |
| PHP | `random_bytes(n)` |
| .NET | `RandomNumberGenerator.Create()` |
| Ruby | `SecureRandom.bytes(n)`, `SecureRandom.hex(n)` |
| Rust | `rand::thread_rng()` is NOT crypto-safe; use `rand::rngs::OsRng` or `getrandom` |

### Disabled certificate verification

`verify=False` (Python requests), `rejectUnauthorized: false`
(Node), `InsecureSkipVerify: true` (Go), custom-trust-everything
`X509TrustManager` (Java), `ServerCertificateValidationCallback`
returning true (.NET).

All of these turn HTTPS into HTTP — a network attacker can MITM
without the application noticing. There are roughly zero
legitimate production use cases for these flags.

The legitimate development use cases (testing against a self-
signed cert):

- Install the dev cert in the OS trust store (one-time setup)
- Use a tool like mkcert to generate a locally-trusted cert
- For ephemeral test environments, use a dedicated test CA

Production code with `verify=False` is a failure of the upstream
ops team to provision proper TLS, hardcoded as an application
choice. Fix the TLS setup, not the verification flag.

### Password hashing

`hashlib.sha256(password)` is a general-purpose hash function.
It's:

- Fast (designed to be fast — bad for password hashing)
- Unsalted by default (vulnerable to rainbow-table attacks)
- Single-iteration (no work factor — no way to slow down brute force)

Modern password hashing uses purpose-built KDFs:

- **bcrypt** — 1999, widely supported, decent
- **scrypt** — 2009, memory-hard (resistant to GPU/ASIC)
- **argon2id** — 2015, current PHC-recommended

All three have configurable work factors that tune to your hardware
and user-acceptable login latency. They incorporate salts
automatically; the salt is stored alongside the hash.

Modern recommendation: argon2id. Acceptable fallback: bcrypt with
cost factor ≥ 12.

## Why static-pattern scanning misses some weak crypto

This scanner detects API-level misuse. Some weaknesses require
deeper analysis:

- Custom protocol design errors (e.g., using a hash where a MAC
  is required) require semantic analysis the scanner can't do
- Insufficient key sizes (RSA-1024, etc.) detected via library
  API form (`RSA.generate(1024)`) but not always
- Padding-oracle vulnerabilities in CBC mode require behavioral
  testing, not static analysis

Treat the scanner as the obvious-cases pass. A full crypto audit
needs domain expertise + tools like Semgrep + cryptography-
specific reviewers.

## Primary sources

- [CWE-327 Use of Broken Cryptographic Algorithm](https://cwe.mitre.org/data/definitions/327.html)
- [CWE-330 Use of Insufficiently Random Values](https://cwe.mitre.org/data/definitions/330.html)
- [CWE-916 Insufficient Computational Effort](https://cwe.mitre.org/data/definitions/916.html)
- [CWE-295 Improper Certificate Validation](https://cwe.mitre.org/data/definitions/295.html)
- [NIST SP 800-131A Transitions of Cryptographic Algorithms](https://csrc.nist.gov/publications/detail/sp/800-131a/rev-2/final)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [Password Hashing Competition (PHC) — argon2 winner](https://www.password-hashing.net/)
