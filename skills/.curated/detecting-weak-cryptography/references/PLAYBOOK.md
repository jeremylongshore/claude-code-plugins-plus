# Weak-Cryptography Remediation Playbook

Per-language migrations from the canonical weak primitives to the
modern replacements.

## Python — `hashlib` + `cryptography` + `secrets`

### MD5 / SHA-1 → SHA-256

```python
# Before
import hashlib
h = hashlib.md5(data).hexdigest()

# After
h = hashlib.sha256(data).hexdigest()
# Even better: BLAKE2b
h = hashlib.blake2b(data).hexdigest()
```

### DES / 3DES / RC4 → AES-256-GCM

```python
# Before (Cryptodome DES)
from Cryptodome.Cipher import DES
c = DES.new(key, DES.MODE_CBC, iv)

# After (cryptography library AES-GCM)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = AESGCM.generate_key(bit_length=256)
aesgcm = AESGCM(key)
nonce = os.urandom(12)
ct = aesgcm.encrypt(nonce, plaintext, associated_data=None)
```

### ECB → GCM

```python
# Before
cipher = AES.new(key, AES.MODE_ECB)

# After (AEAD, no separate HMAC needed)
aesgcm = AESGCM(key)
ct = aesgcm.encrypt(nonce, plaintext, None)
```

### Password hashing

```python
# Before (insecure)
import hashlib
hash_ = hashlib.sha256(password.encode()).hexdigest()

# After (argon2id, recommended)
from argon2 import PasswordHasher
ph = PasswordHasher()
hash_ = ph.hash(password)  # includes salt + work factor in output
# Verify:
try:
    ph.verify(hash_, password)  # raises on mismatch
except VerifyMismatchError:
    ...

# Alternative: bcrypt (still acceptable)
import bcrypt
hash_ = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12))
bcrypt.checkpw(password.encode(), hash_)
```

### Crypto random

```python
# Before
import random
token = ''.join(random.choices('abc...', k=32))

# After
import secrets
token = secrets.token_urlsafe(32)
# Or for raw bytes:
random_bytes = secrets.token_bytes(32)
```

### TLS verification

```python
# Before
resp = requests.get(url, verify=False)

# After (default — verify=True is implicit)
resp = requests.get(url)

# If you need a custom CA:
resp = requests.get(url, verify="/path/to/ca-bundle.crt")
```

## Node.js — `crypto` module

### Hash migration

```javascript
// Before
const md5 = crypto.createHash('md5').update(data).digest('hex');

// After
const sha256 = crypto.createHash('sha256').update(data).digest('hex');
```

### Cipher migration

```javascript
// Before
const c = crypto.createCipheriv('des-ede3-cbc', key, iv);

// After (AES-256-GCM AEAD)
const iv = crypto.randomBytes(12);
const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
const authTag = cipher.getAuthTag();
// Store [iv, encrypted, authTag] together
```

### Crypto random

```javascript
// Before
const sessionId = Math.random().toString(36);  // NOT crypto-grade

// After
const sessionId = crypto.randomBytes(16).toString('hex');
// Or:
const sessionId = crypto.randomUUID();
```

### Password hashing

```javascript
// Before
const hash = crypto.createHash('sha256').update(password).digest('hex');

// After (bcrypt)
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
const ok = await bcrypt.compare(password, hash);

// After (argon2 — preferred)
const argon2 = require('argon2');
const hash = await argon2.hash(password, { type: argon2.argon2id });
const ok = await argon2.verify(hash, password);
```

### TLS verification (Node)

```javascript
// Before
const https = require('https');
const agent = new https.Agent({ rejectUnauthorized: false });
fetch(url, { agent });

// After: just don't pass the agent
fetch(url);  // verification on by default

// For custom CA:
const agent = new https.Agent({ ca: fs.readFileSync('/path/to/ca.crt') });
```

### Env var TLS bypass — REMOVE

```bash
# Before — anywhere in startup scripts
export NODE_TLS_REJECT_UNAUTHORIZED=0

# After: remove the line entirely
```

## Java — `java.security` + Bouncy Castle

### MessageDigest migration

```java
// Before
MessageDigest md = MessageDigest.getInstance("MD5");

// After
MessageDigest md = MessageDigest.getInstance("SHA-256");
```

### Cipher migration

```java
// Before
Cipher c = Cipher.getInstance("DES/CBC/PKCS5Padding");

// After (AES-256-GCM)
SecureRandom random = new SecureRandom();
byte[] iv = new byte[12];
random.nextBytes(iv);
GCMParameterSpec gcmSpec = new GCMParameterSpec(128, iv);
Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
c.init(Cipher.ENCRYPT_MODE, key, gcmSpec);
byte[] ciphertext = c.doFinal(plaintext);
```

### SecureRandom

```java
// Before
Random rand = new Random();
byte[] keyBytes = new byte[32];
rand.nextBytes(keyBytes);

// After
SecureRandom rand = new SecureRandom();
byte[] keyBytes = new byte[32];
rand.nextBytes(keyBytes);
```

### Password hashing (use Spring Security or library)

```java
// Spring Security 5.0+
PasswordEncoder encoder = new BCryptPasswordEncoder(12);
String hash = encoder.encode(rawPassword);
boolean ok = encoder.matches(rawPassword, hash);

// Argon2id via password4j
import com.password4j.Password;
String hash = Password.hash(rawPassword).withArgon2().getResult();
boolean ok = Password.check(rawPassword, hash).withArgon2();
```

### TrustManager — never trust everything

```java
// Before (DANGEROUS)
TrustManager[] trustAll = new TrustManager[] {
    new X509TrustManager() {
        public void checkClientTrusted(X509Certificate[] chain, String authType) {}
        public void checkServerTrusted(X509Certificate[] chain, String authType) {}
        public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
    }
};

// After: just use the default
SSLContext ctx = SSLContext.getInstance("TLS");
ctx.init(null, null, null);  // null = JVM default trust store

// For custom CA: load it into a KeyStore and pass to TrustManagerFactory.
```

## Go — `crypto/aes` + `crypto/rand` + `golang.org/x/crypto`

### Hash migration

```go
// Before
import "crypto/md5"
h := md5.Sum(data)

// After
import "crypto/sha256"
h := sha256.Sum256(data)
```

### Cipher migration

```go
// Before
import "crypto/des"
block, _ := des.NewTripleDESCipher(key)

// After (AES-GCM)
import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
)
block, _ := aes.NewCipher(key)  // key: 16, 24, or 32 bytes
gcm, _ := cipher.NewGCM(block)
nonce := make([]byte, gcm.NonceSize())
rand.Read(nonce)
ciphertext := gcm.Seal(nil, nonce, plaintext, nil)
```

### Crypto random

```go
// Before
import "math/rand"
b := make([]byte, 32)
rand.Read(b)  // PREDICTABLE

// After
import "crypto/rand"
b := make([]byte, 32)
rand.Read(b)  // crypto-grade
```

### Password hashing

```go
// bcrypt
import "golang.org/x/crypto/bcrypt"
hash, _ := bcrypt.GenerateFromPassword([]byte(password), 12)
err := bcrypt.CompareHashAndPassword(hash, []byte(password))

// argon2id
import "golang.org/x/crypto/argon2"
salt := make([]byte, 16)
rand.Read(salt)
hash := argon2.IDKey([]byte(password), salt, 1, 64*1024, 4, 32)
```

### TLS verification

```go
// Before
tr := &http.Transport{
    TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
}

// After: just don't set TLSClientConfig at all (defaults are safe)
client := &http.Client{}
// Or for a custom CA:
caCert, _ := os.ReadFile("ca.crt")
caPool := x509.NewCertPool()
caPool.AppendCertsFromPEM(caCert)
tr := &http.Transport{TLSClientConfig: &tls.Config{RootCAs: caPool}}
```

## PHP — `openssl_*` + `password_hash` + `random_bytes`

### Cipher migration

```php
// Before
$ct = openssl_encrypt($pt, 'des-ede-cbc', $key, 0, $iv);

// After
$iv = random_bytes(12);
$tag = '';
$ct = openssl_encrypt($pt, 'aes-256-gcm', $key, OPENSSL_RAW_DATA, $iv, $tag);
// Store [iv, ct, tag]
```

### Password hashing

```php
// Before
$hash = md5($password);

// After
$hash = password_hash($password, PASSWORD_BCRYPT);
// PHP 7.2+: argon2i; PHP 7.3+: argon2id
$hash = password_hash($password, PASSWORD_ARGON2ID);
$ok = password_verify($password, $hash);
```

### Crypto random

```php
// Before
$token = bin2hex(mt_rand(0, PHP_INT_MAX));

// After
$token = bin2hex(random_bytes(32));
```

### cURL TLS verification — REMOVE the disable

```php
// Before (DANGEROUS)
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);

// After: omit those calls. Defaults are verify=true.
// For custom CA:
curl_setopt($ch, CURLOPT_CAINFO, '/path/to/ca-bundle.crt');
```

## C# / .NET

### Hash migration

```csharp
// Before
using (var md5 = MD5.Create()) { var h = md5.ComputeHash(data); }

// After
using (var sha = SHA256.Create()) { var h = sha.ComputeHash(data); }
```

### Cipher migration

```csharp
// Before — DESCryptoServiceProvider deprecated
using var des = new DESCryptoServiceProvider();

// After — AES-GCM
using var aes = new AesGcm(key);
byte[] nonce = RandomNumberGenerator.GetBytes(12);
byte[] tag = new byte[16];
byte[] ciphertext = new byte[plaintext.Length];
aes.Encrypt(nonce, plaintext, ciphertext, tag);
```

### Crypto random

```csharp
// Before
var rand = new Random();
byte[] key = new byte[32];
rand.NextBytes(key);  // NOT crypto-grade

// After
byte[] key = RandomNumberGenerator.GetBytes(32);
```

### Password hashing

```csharp
// .NET: use BCrypt.Net or Konscious.Security.Cryptography for argon2id
using BCrypt.Net;
string hash = BCrypt.HashPassword(password, workFactor: 12);
bool ok = BCrypt.Verify(password, hash);
```

### ServerCertificateValidation — never always-true

```csharp
// Before (DANGEROUS)
ServicePointManager.ServerCertificateValidationCallback = (s, c, ch, e) => true;

// After: remove. Defaults verify.
// For custom CA:
HttpClientHandler handler = new HttpClientHandler();
handler.ServerCertificateCustomValidationCallback = (s, c, ch, e) => {
    // Real validation — verify against your own CA, not blind-true
};
```

## CI integration

```yaml
- name: Weak-crypto scan
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-weak-cryptography/scripts/scan_weak_crypto.py \
        . --min-severity high --format json --output crypto-scan.json
- run: |
    if jq 'length > 0' crypto-scan.json | grep -q true; then
      echo "::error::Weak cryptography detected"
      cat crypto-scan.json
      exit 1
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-weak-cryptography/scripts/scan_weak_crypto.py \
    /path/to/repo --min-severity medium
```

Expected: exit 0, zero MEDIUM-or-higher findings. LOW findings on
MD5/SHA-1 used in legitimate non-security contexts (content
addressing, dedup) are acceptable; document each.
