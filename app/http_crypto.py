import base64
import hashlib
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status

ALGORITHM = "AES-256-GCM"
AUTHENTICATED_DATA = None


def is_encrypted_payload(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("encrypted") is True
        and value.get("alg") == ALGORITHM
        and isinstance(value.get("iv"), str)
        and isinstance(value.get("data"), str)
    )


def encrypt_payload(value: Any) -> dict[str, Any]:
    iv = os.urandom(12)
    plaintext = json.dumps(
        value if value is not None else None,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    encrypted = AESGCM(_get_key()).encrypt(iv, plaintext, AUTHENTICATED_DATA)

    return {
        "encrypted": True,
        "alg": ALGORITHM,
        "iv": base64.b64encode(iv).decode("ascii"),
        "data": base64.b64encode(encrypted).decode("ascii"),
    }


def decrypt_payload(payload: dict[str, Any]) -> Any:
    try:
        iv = base64.b64decode(payload["iv"], validate=True)
        encrypted = base64.b64decode(payload["data"], validate=True)
        decrypted = AESGCM(_get_key()).decrypt(iv, encrypted, AUTHENTICATED_DATA)
        return json.loads(decrypted.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid encrypted payload.",
        ) from exc


def _get_key() -> bytes:
    secret = (os.getenv("HTTP_CRYPTO_SECRET") or os.getenv("APPLICATION_KEY") or "").strip()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HTTP crypto secret is not configured.",
        )

    return hashlib.sha256(secret.encode("utf-8")).digest()
