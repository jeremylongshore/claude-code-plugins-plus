"""
Client-side encryption using AES-256-GCM with user-controlled keys.
"""

import hashlib
import os
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass
class CryptoResult:
    """Encryption result with metadata."""
    ciphertext: bytes
    algorithm: str
    key_id: str
    plaintext_sha256: str
    ciphertext_sha256: str


# In-memory key store (production would use proper key management)
_KEY_STORE = {}


def _get_or_create_key(key_id: str = "default") -> bytes:
    """Get or create encryption key."""
    if key_id not in _KEY_STORE:
        # Generate new 256-bit key
        _KEY_STORE[key_id] = AESGCM.generate_key(bit_length=256)
    return _KEY_STORE[key_id]


def encrypt_data(plaintext: str, key_id: str = "default") -> CryptoResult:
    """
    Encrypt data using AES-256-GCM.

    Args:
        plaintext: Data to encrypt (string)
        key_id: Key identifier

    Returns:
        CryptoResult with encrypted data and metadata
    """
    # Get encryption key
    key = _get_or_create_key(key_id)
    aesgcm = AESGCM(key)

    # Generate random nonce (96 bits for GCM)
    nonce = os.urandom(12)

    # Encrypt
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext_without_nonce = aesgcm.encrypt(nonce, plaintext_bytes, None)

    # Prepend nonce to ciphertext for storage
    ciphertext = nonce + ciphertext_without_nonce

    # Compute hashes
    plaintext_sha256 = hashlib.sha256(plaintext_bytes).hexdigest()
    ciphertext_sha256 = hashlib.sha256(ciphertext).hexdigest()

    return CryptoResult(
        ciphertext=ciphertext,
        algorithm="AES-256-GCM",
        key_id=key_id,
        plaintext_sha256=plaintext_sha256,
        ciphertext_sha256=ciphertext_sha256
    )


def decrypt_data(
    ciphertext: bytes,
    key_id: str = "default",
    expected_ciphertext_sha256: str = None
) -> str:
    """
    Decrypt AES-256-GCM encrypted data.

    Args:
        ciphertext: Encrypted data (with nonce prepended)
        key_id: Key identifier
        expected_ciphertext_sha256: Optional integrity check

    Returns:
        Decrypted plaintext string
    """
    # Verify ciphertext integrity
    if expected_ciphertext_sha256:
        actual_sha256 = hashlib.sha256(ciphertext).hexdigest()
        if actual_sha256 != expected_ciphertext_sha256:
            raise ValueError(
                f"Ciphertext integrity check failed. "
                f"Expected: {expected_ciphertext_sha256}, Got: {actual_sha256}"
            )

    # Get decryption key
    key = _get_or_create_key(key_id)
    aesgcm = AESGCM(key)

    # Extract nonce (first 12 bytes)
    nonce = ciphertext[:12]
    ciphertext_only = ciphertext[12:]

    # Decrypt
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_only, None)

    return plaintext_bytes.decode('utf-8')
