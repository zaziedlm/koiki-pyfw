"""Stateless CSRF token utilities."""

from __future__ import annotations

import base64
import hmac
import secrets
import time
from hashlib import sha256
from typing import Optional


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    return digest


def create_csrf_token(
    subject: str,
    secret: str,
    ttl_seconds: int,
) -> str:
    """
    Create a stateless CSRF token bound to the given subject.

    Token format (before base64url encoding):
        subject:timestamp:nonce:signature
    """
    timestamp = int(time.time())
    nonce = secrets.token_hex(8)
    payload = f"{subject}:{timestamp}:{nonce}"
    signature = _sign(payload, secret)
    token_bytes = f"{payload}:{signature}".encode("utf-8")
    return base64.urlsafe_b64encode(token_bytes).decode("utf-8")


def validate_csrf_token(
    token: str,
    subject: str,
    secret: str,
    ttl_seconds: int,
) -> bool:
    """Validate token signature and TTL."""
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        token_subject, timestamp_str, nonce, signature = decoded.split(":")
    except Exception:
        return False

    if token_subject != subject:
        return False

    expected_payload = f"{token_subject}:{timestamp_str}:{nonce}"
    expected_signature = _sign(expected_payload, secret)
    if not hmac.compare_digest(signature, expected_signature):
        return False

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return False

    if int(time.time()) - timestamp > ttl_seconds:
        return False

    return True
