"""Password and bearer-secret handling."""

import hashlib
import secrets

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
_dummy_password_hash = password_hash.hash("dummy-password-used-only-for-timing")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    return password_hash.verify(password, encoded_hash or _dummy_password_hash)


def new_secret() -> str:
    return secrets.token_urlsafe(32)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()
