"""
Password hashing implementation.

This module provides password hashing using bcrypt algorithm.
Since we can't use external libraries, we implement a simplified
but secure password hashing using PBKDF2 (which is in standard library).
"""

import base64
import hashlib
import hmac
import secrets
from typing import Optional


class PasswordHasher:
    """
    Password hasher using PBKDF2.

    PBKDF2 is a secure key derivation function that's part of
    Python's standard library (via hashlib.pbkdf2_hmac).
    """

    def __init__(
        self,
        algorithm: str = "pbkdf2_sha256",
        iterations: int = 260000,
        salt_length: int = 16,
    ):
        """
        Initialize password hasher.

        Args:
            algorithm: Hashing algorithm name
            iterations: Number of iterations (higher = more secure, slower)
            salt_length: Salt length in bytes
        """
        self.algorithm = algorithm
        self.iterations = iterations
        self.salt_length = salt_length

    def _generate_salt(self) -> bytes:
        """
        Generate random salt.

        Returns:
            Random salt bytes
        """
        return secrets.token_bytes(self.salt_length)

    def hash(self, password: str) -> str:
        """
        Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password string (format: algorithm$iterations$salt$hash)
        """
        salt = self._generate_salt()

        # Hash password using PBKDF2
        password_bytes = password.encode("utf-8")
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt,
            self.iterations,
        )

        # Encode salt and hash
        salt_b64 = base64.b64encode(salt).decode("ascii")
        hash_b64 = base64.b64encode(hash_bytes).decode("ascii")

        # Return formatted string
        return f"{self.algorithm}${self.iterations}${salt_b64}${hash_b64}"

    def verify(self, password: str, hashed: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Plain text password
            hashed: Hashed password string

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Parse hash string
            parts = hashed.split("$")
            if len(parts) != 4:
                return False

            algorithm, iterations_str, salt_b64, hash_b64 = parts

            # Check algorithm
            if algorithm != self.algorithm:
                return False

            # Decode salt and hash
            salt = base64.b64decode(salt_b64)
            expected_hash = base64.b64decode(hash_b64)

            # Hash password with same salt and iterations
            iterations = int(iterations_str)
            password_bytes = password.encode("utf-8")
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password_bytes,
                salt,
                iterations,
            )

            # Compare hashes (constant-time comparison)
            return hmac.compare_digest(computed_hash, expected_hash)

        except (ValueError, TypeError, base64.binascii.Error):
            return False


# Global instance
_default_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a password using default hasher.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return _default_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash using default hasher.

    Args:
        password: Plain text password
        hashed: Hashed password string

    Returns:
        True if password matches, False otherwise
    """
    return _default_hasher.verify(password, hashed)
