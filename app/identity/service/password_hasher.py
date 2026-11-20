PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16

import secrets
import hashlib
import hmac

def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )

    return f"{salt}${derived_key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
        if not salt or len(expected) != hashlib.sha256().digest_size * 2:
            return False
        bytes.fromhex(expected)
    except (AttributeError, ValueError):
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PBKDF2_ITERATIONS,
    ).hex()

    return hmac.compare_digest(derived, expected)