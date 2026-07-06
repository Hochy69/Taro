from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_admin_token(admin_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=3650)
    return jwt.encode(
        {"sub": str(admin_id), "role": "admin", "exp": expire},
        settings.admin_jwt_secret or settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, secret: str | None = None) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            secret or settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None


def verify_telegram_webapp_data(init_data: str, bot_token: str) -> dict[str, Any] | None:
    """Validate Telegram WebApp initData using HMAC-SHA256."""
    import hashlib
    import hmac
    import json
    from urllib.parse import parse_qsl

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        return None

    auth_date = parsed.get("auth_date")
    if not auth_date:
        return None
    try:
        age_seconds = datetime.now(timezone.utc).timestamp() - int(auth_date)
    except (TypeError, ValueError):
        return None
    if age_seconds < 0 or age_seconds > 3600:
        return None

    if "user" in parsed:
        parsed["user"] = json.loads(parsed["user"])
    return parsed
