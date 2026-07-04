"""Always read the latest WebApp URL from the root .env (tunnel URL changes often)."""

import os
from pathlib import Path

from app.config import settings

_ROOT_ENV_CANDIDATES = (
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[1] / ".env",
)


def _read_url_from_env_file() -> str:
    for env_path in _ROOT_ENV_CANDIDATES:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("TELEGRAM_WEBAPP_URL="):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value.rstrip("/")
    return ""


def get_webapp_url() -> str:
    env_value = os.getenv("TELEGRAM_WEBAPP_URL", "").strip().strip('"').strip("'")
    if env_value:
        return env_value.rstrip("/")

    file_value = _read_url_from_env_file()
    if file_value:
        return file_value
    return settings.telegram_webapp_url.rstrip("/")
