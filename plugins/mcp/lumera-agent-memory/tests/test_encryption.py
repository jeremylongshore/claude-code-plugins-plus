"""
Test client-side encryption roundtrip.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from security.encrypt import encrypt_data, decrypt_data


def test_encrypt_decrypt_roundtrip():
    """Basic encryption roundtrip should work."""
    plaintext = "This is secret session data"

    # Encrypt
    crypto_result = encrypt_data(plaintext)

    assert crypto_result.algorithm == "AES-256-GCM"
    assert crypto_result.key_id == "default"
    assert len(crypto_result.ciphertext) > 0
    assert crypto_result.ciphertext != plaintext.encode('utf-8')

    # Decrypt
    decrypted = decrypt_data(
        crypto_result.ciphertext,
        expected_ciphertext_sha256=crypto_result.ciphertext_sha256
    )

    assert decrypted == plaintext


def test_encrypt_large_data():
    """Encryption should handle large payloads."""
    plaintext = "x" * 100000  # 100KB

    crypto_result = encrypt_data(plaintext)
    decrypted = decrypt_data(crypto_result.ciphertext)

    assert decrypted == plaintext


def test_decrypt_integrity_check_fails():
    """Decryption with wrong integrity hash should fail."""
    plaintext = "secret data"
    crypto_result = encrypt_data(plaintext)

    # Tamper with expected hash
    wrong_hash = "0" * 64

    with pytest.raises(ValueError) as exc_info:
        decrypt_data(
            crypto_result.ciphertext,
            expected_ciphertext_sha256=wrong_hash
        )

    assert "integrity check failed" in str(exc_info.value).lower()


def test_decrypt_tampered_ciphertext_fails():
    """Decrypting tampered ciphertext should fail."""
    plaintext = "secret data"
    crypto_result = encrypt_data(plaintext)

    # Tamper with ciphertext
    tampered = bytearray(crypto_result.ciphertext)
    tampered[-1] ^= 1  # Flip last bit

    with pytest.raises(Exception):  # Should raise crypto exception
        decrypt_data(bytes(tampered))


def test_plaintext_sha256_matches():
    """Plaintext SHA-256 should match actual plaintext hash."""
    import hashlib

    plaintext = "test data"
    crypto_result = encrypt_data(plaintext)

    expected_hash = hashlib.sha256(plaintext.encode('utf-8')).hexdigest()
    assert crypto_result.plaintext_sha256 == expected_hash


def test_different_keys_cant_decrypt():
    """Data encrypted with one key can't be decrypted with another."""
    plaintext = "secret"

    crypto_result = encrypt_data(plaintext, key_id="key1")

    # This will fail because decrypt uses key1 but we're simulating a different key scenario
    # In practice, the key_id mismatch would be caught at a higher level
    decrypted = decrypt_data(crypto_result.ciphertext, key_id="key1")
    assert decrypted == plaintext  # Same key works

    # Different key would fail (but we need to create a new encryption first)
    crypto_result2 = encrypt_data(plaintext, key_id="key2")
    with pytest.raises(Exception):
        # Try to decrypt key2-encrypted data with key1
        decrypt_data(crypto_result2.ciphertext, key_id="key1")
