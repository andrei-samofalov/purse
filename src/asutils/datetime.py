from datetime import datetime, timezone


def utcnow():
    """Return current time in UTC."""
    return datetime.now(timezone.utc)
