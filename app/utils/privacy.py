import hashlib

def hash_ip(ip: str, salt: str) -> str:
    """Hash an IP address with a salt for privacy."""
    if not ip:
        return "unknown"
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()