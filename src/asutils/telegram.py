def get_user_tg_url(username: str):
    """Return Telegram URL for given username."""
    cleaned = username.lstrip("@")
    return f"https://t.me/{cleaned}"
