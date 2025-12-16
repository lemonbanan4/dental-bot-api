import hashlib
from typing import Optional

from app.config import settings


def hash_ip(ip: Optional[str], salt: Optional[str] = None) -> Optional[str]:
    """
    Hash IP with a static salt for pseudonymous tracking.
    Salt comes from `IP_HASH_SALT` env var unless explicitly provided.
    """
    if not ip:
        return None
    salt_value = salt if salt is not None else settings.ip_hash_salt
    return hashlib.sha256((salt_value + ip).encode("utf-8")).hexdigest()
