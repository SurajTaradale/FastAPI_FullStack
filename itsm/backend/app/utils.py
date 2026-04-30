import hashlib
import random
import string
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt (new standard)."""
    return pwd_context.hash(password)


def _is_bcrypt(hashed: str) -> bool:
    """Return True if the hash looks like a bcrypt hash ($2b$, $2a$, $2y$)."""
    return isinstance(hashed, str) and hashed.startswith(("$2b$", "$2a$", "$2y$"))


def _is_sha256(hashed: str) -> bool:
    """Return True if the hash looks like a plain hex SHA256 (64 hex chars)."""
    return isinstance(hashed, str) and len(hashed) == 64 and all(c in "0123456789abcdef" for c in hashed.lower())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against either a bcrypt or legacy SHA256 hash.

    This supports a live migration path:
    - New passwords are stored as bcrypt (via hash_password).
    - Old passwords still stored as SHA256 will still pass verification here.
    - Callers should re-hash with hash_password() on successful SHA256 login
      so the account migrates to bcrypt transparently.
    """
    if not hashed_password:
        return False

    if _is_bcrypt(hashed_password):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    if _is_sha256(hashed_password):
        # Legacy SHA256 path — compare hex digests
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password.lower()

    # Unknown hash format — fail safe
    return False


def needs_rehash(hashed_password: str) -> bool:
    """Return True if the stored hash is legacy SHA256 and should be migrated to bcrypt."""
    return _is_sha256(hashed_password)


def generate_random_password(length: int = 12) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
