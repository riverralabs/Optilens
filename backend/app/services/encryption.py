"""AES-256 encryption for OAuth tokens stored in the database.

All OAuth tokens (GA4, GSC, GitHub) are encrypted before storage
and decrypted only when needed for API calls.
"""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings


def _get_fernet() -> Fernet:
    """Derive a Fernet key from the ENCRYPTION_KEY env var using PBKDF2."""
    settings = get_settings()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"optilens-token-encryption",  # Static salt — key rotation handled via ENCRYPTION_KEY change
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
    return Fernet(key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string, returning a base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext back to the original token."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
