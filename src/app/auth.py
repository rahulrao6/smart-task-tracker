"""User authentication module.

Provides password hashing/verification and a simple in-memory user store
for demonstration purposes.  The store can be swapped for a real database
layer without changing the public API.

Public API
----------
hash_password(plain: str) -> str
    Return a salted SHA-256 hex digest for ``plain``.

verify_password(plain: str, hashed: str) -> bool
    Return True iff hash_password(plain) matches ``hashed``.

create_user(username: str, password: str, *, store=None) -> UserRecord
    Register a new user; raises ValueError on duplicate username or
    invalid credentials.

authenticate_user(username: str, password: str, *, store=None) -> UserRecord
    Return the matching UserRecord or raise AuthenticationError.

generate_token(username: str) -> str
    Generate a URL-safe random token bound to ``username``.

validate_token(token: str, *, store=None) -> str
    Return the username for a valid token or raise InvalidTokenError.

revoke_token(token: str, *, store=None) -> None
    Invalidate a token (no-op if it does not exist).
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AuthenticationError(Exception):
    """Raised when credentials are invalid."""


class InvalidTokenError(Exception):
    """Raised when a token is missing or has been revoked."""


class UserNotFoundError(Exception):
    """Raised when a requested user does not exist."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class UserRecord:
    username: str
    hashed_password: str
    is_active: bool = True
    roles: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default in-memory stores (module-level singletons for convenience)
# ---------------------------------------------------------------------------

_DEFAULT_USER_STORE: Dict[str, UserRecord] = {}
_DEFAULT_TOKEN_STORE: Dict[str, str] = {}  # token -> username


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a salted SHA-256 hex digest for *plain*.

    Format: ``<16-byte-salt-hex>:<sha256-hex>``
    """
    if not isinstance(plain, str):
        raise TypeError("Password must be a string")
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + plain).encode()).hexdigest()
    return f"{salt}:{digest}"


def verify_password(plain: str, hashed: str) -> bool:
    """Return True iff *plain* matches the *hashed* password."""
    if not isinstance(plain, str) or not isinstance(hashed, str):
        return False
    try:
        salt, digest = hashed.split(":", 1)
    except ValueError:
        return False
    expected = hashlib.sha256((salt + plain).encode()).hexdigest()
    return secrets.compare_digest(expected, digest)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def create_user(
    username: str,
    password: str,
    *,
    roles: Optional[list[str]] = None,
    store: Optional[Dict[str, UserRecord]] = None,
) -> UserRecord:
    """Register a new user.

    Raises
    ------
    ValueError
        If *username* is empty, *password* is too short (< 8 chars), or
        the username is already taken.
    """
    if store is None:
        store = _DEFAULT_USER_STORE

    if not username or not username.strip():
        raise ValueError("Username must not be empty")
    username = username.strip()

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if username in store:
        raise ValueError(f"Username '{username}' is already taken")

    record = UserRecord(
        username=username,
        hashed_password=hash_password(password),
        roles=list(roles) if roles else [],
    )
    store[username] = record
    return record


def get_user(
    username: str,
    *,
    store: Optional[Dict[str, UserRecord]] = None,
) -> UserRecord:
    """Return the UserRecord for *username* or raise UserNotFoundError."""
    if store is None:
        store = _DEFAULT_USER_STORE
    try:
        return store[username]
    except KeyError:
        raise UserNotFoundError(f"User '{username}' not found")


def authenticate_user(
    username: str,
    password: str,
    *,
    store: Optional[Dict[str, UserRecord]] = None,
) -> UserRecord:
    """Return the UserRecord if credentials are valid.

    Raises
    ------
    AuthenticationError
        If the username does not exist, the password is wrong, or the
        account is inactive.
    """
    if store is None:
        store = _DEFAULT_USER_STORE

    record = store.get(username)
    if record is None:
        raise AuthenticationError("Invalid username or password")
    if not record.is_active:
        raise AuthenticationError("Account is inactive")
    if not verify_password(password, record.hashed_password):
        raise AuthenticationError("Invalid username or password")
    return record


def deactivate_user(
    username: str,
    *,
    store: Optional[Dict[str, UserRecord]] = None,
) -> None:
    """Mark a user as inactive."""
    user = get_user(username, store=store)
    user.is_active = False


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

def generate_token(
    username: str,
    *,
    token_store: Optional[Dict[str, str]] = None,
) -> str:
    """Generate and store a URL-safe random token bound to *username*."""
    if token_store is None:
        token_store = _DEFAULT_TOKEN_STORE
    token = secrets.token_urlsafe(32)
    token_store[token] = username
    return token


def validate_token(
    token: str,
    *,
    token_store: Optional[Dict[str, str]] = None,
) -> str:
    """Return the username for a valid *token*.

    Raises
    ------
    InvalidTokenError
        If the token is not present in the store.
    """
    if token_store is None:
        token_store = _DEFAULT_TOKEN_STORE
    username = token_store.get(token)
    if username is None:
        raise InvalidTokenError("Token is invalid or has been revoked")
    return username


def revoke_token(
    token: str,
    *,
    token_store: Optional[Dict[str, str]] = None,
) -> None:
    """Remove *token* from the store (no-op if absent)."""
    if token_store is None:
        token_store = _DEFAULT_TOKEN_STORE
    token_store.pop(token, None)
