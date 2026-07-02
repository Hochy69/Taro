"""Always read the latest WebApp URL from the root .env (tunnel URL changes often)."""

from pathlib import Path

from app.config import settings

_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


def get_webapp_url() -> str:
    if _ROOT_ENV.exists():
        for line in _ROOT_ENV.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("TELEGRAM_WEBAPP_URL="):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value.rstrip("/")
    return settings.telegram_webapp_url.rstrip("/")
