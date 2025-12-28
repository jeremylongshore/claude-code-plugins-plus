#!/usr/bin/env python3

"""
Example secure code snippets demonstrating how to remediate common vulnerabilities.

This module provides examples of secure coding practices to address various security concerns.
It includes functions demonstrating secure authentication, input validation, and more.
"""

import hashlib
import hmac
import os
import secrets
import re

def secure_password_hashing(password: str, salt: bytes = None) -> tuple[str, str]:
    """
    Hashes a password using a strong hashing algorithm (e.g., bcrypt or scrypt).

    Args:
        password: The password to hash.
        salt: Optional salt to use. If None, a new salt is generated.

    Returns:
        A tuple containing the salt (as a hex string) and the hash (as a hex string).
    """
    try:
        if salt is None:
            salt = secrets.token_bytes(16)  # Generate a 16-byte salt
        
        hashed_password = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=2**14,  # CPU/memory cost parameter
            r=8,      # Block size parameter
            p=1,      # Parallelization parameter
            dklen=64   # Desired key length
        )
        
        return salt.hex(), hashed_password.hex()
    except Exception as e:
        print(f"Error in secure_password_hashing: {e}")
        return None, None


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """
    Verifies a password against a stored hash and salt.

    Args:
        password: The password to verify.
        salt_hex: The salt used to hash the password (as a hex string).
        hash_hex: The stored hash of the password (as a hex string).

    Returns:
        True if the password matches the stored hash, False otherwise.
    """
    try:
        salt = bytes.fromhex(salt_hex)
        stored_hash = bytes.fromhex(hash_hex)
        
        hashed_password = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=2**14,  # CPU/memory cost parameter
            r=8,      # Block size parameter
            p=1,      # Parallelization parameter
            dklen=64   # Desired key length
        )

        return hmac.compare_digest(hashed_password, stored_hash)
    except ValueError as ve:
        print(f"ValueError in verify_password (likely invalid hex): {ve}")
        return False
    except Exception as e:
        print(f"Error in verify_password: {e}")
        return False


def sanitize_input(input_string: str) -> str:
    """
    Sanitizes user input to prevent common injection vulnerabilities.

    This function removes or escapes characters that could be used in SQL injection,
    cross-site scripting (XSS), or other injection attacks.

    Args:
        input_string: The string to sanitize.

    Returns:
        The sanitized string.
    """
    try:
        # Example: Escape HTML entities
        sanitized_string = input_string.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&#39;")

        # Example: Remove potentially dangerous characters (e.g., for SQL injection)
        sanitized_string = re.sub(r"[;'\"]", "", sanitized_string)

        return sanitized_string
    except Exception as e:
        print(f"Error in sanitize_input: {e}")
        return ""


def validate_email(email: str) -> bool:
    """
    Validates an email address using a regular expression.

    Args:
        email: The email address to validate.

    Returns:
        True if the email address is valid, False otherwise.
    """
    try:
        # A more robust email regex can be used
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None
    except Exception as e:
        print(f"Error in validate_email: {e}")
        return False


def secure_file_upload(filename: str, file_content: bytes, upload_dir: str) -> str:
    """
    Handles secure file uploads, preventing common vulnerabilities like path traversal.

    Args:
        filename: The original filename of the uploaded file.
        file_content: The content of the uploaded file as bytes.
        upload_dir: The directory to store the uploaded files.

    Returns:
        The path to the saved file, or None on error.
    """
    try:
        # Sanitize filename to prevent path traversal attacks
        sanitized_filename = os.path.basename(filename)  # Remove directory components
        sanitized_filename = re.sub(r"[^a-zA-Z0-9._-]", "", sanitized_filename) # Remove invalid characters

        if not sanitized_filename:
            print("Invalid filename.")
            return None

        filepath = os.path.join(upload_dir, sanitized_filename)

        # Ensure the upload directory exists
        os.makedirs(upload_dir, exist_ok=True)

        # Write the file content
        with open(filepath, "wb") as f:
            f.write(file_content)

        return filepath
    except OSError as ose:
        print(f"OSError in secure_file_upload: {ose}")
        return None
    except Exception as e:
        print(f"Error in secure_file_upload: {e}")
        return None

def generate_secure_random_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure random token.

    Args:
        length: The length of the token in bytes.

    Returns:
        A hex-encoded string representing the random token.
    """
    try:
        return secrets.token_hex(length)
    except Exception as e:
        print(f"Error in generate_secure_random_token: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    password = "my_secret_password"

    # Secure password hashing
    salt, password_hash = secure_password_hashing(password)
    if salt and password_hash:
        print(f"Salt: {salt}")
        print(f"Password Hash: {password_hash}")

        # Verify password
        is_valid = verify_password(password, salt, password_hash)
        print(f"Password is valid: {is_valid}")

        is_invalid = verify_password("wrong_password", salt, password_hash)
        print(f"Wrong password is valid: {is_invalid}")
    else:
        print("Password hashing failed.")

    # Input sanitization
    user_input = "<script>alert('XSS');</script>"
    sanitized_input = sanitize_input(user_input)
    print(f"Original input: {user_input}")
    print(f"Sanitized input: {sanitized_input}")

    # Email validation
    email = "test@example.com"
    is_valid_email = validate_email(email)
    print(f"Email '{email}' is valid: {is_valid_email}")

    invalid_email = "invalid-email"
    is_valid_invalid_email = validate_email(invalid_email)
    print(f"Email '{invalid_email}' is valid: {is_valid_invalid_email}")

    # Secure file upload (example)
    filename = "important.txt"
    file_content = b"This is some sensitive data."
    upload_dir = "uploads"
    filepath = secure_file_upload(filename, file_content, upload_dir)
    if filepath:
        print(f"File uploaded to: {filepath}")
    else:
        print("File upload failed.")

    # Generate secure random token
    token = generate_secure_random_token()
    print(f"Secure random token: {token}")