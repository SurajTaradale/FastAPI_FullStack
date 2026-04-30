import hashlib
import random
import string
import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _is_bcrypt(hashed: str) -> bool:
    return isinstance(hashed, str) and hashed.startswith(("$2b$", "$2a$", "$2y$"))


def _is_sha256(hashed: str) -> bool:
    return (
        isinstance(hashed, str)
        and len(hashed) == 64
        and all(c in "0123456789abcdef" for c in hashed.lower())
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if _is_bcrypt(hashed_password):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False
    if _is_sha256(hashed_password):
        return (
            hashlib.sha256(plain_password.encode()).hexdigest()
            == hashed_password.lower()
        )
    return False


def needs_rehash(hashed_password: str) -> bool:
    return _is_sha256(hashed_password)


def generate_random_password(length: int = 12) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
