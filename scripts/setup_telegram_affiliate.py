#!/usr/bin/env python3
"""
Enable Telegram Affiliate Program (Star Ref) for @best1tarolog_bot.

Requires the BOT OWNER's user account (MTProto), NOT the bot token.
Method: bots.updateStarRefProgram

Setup:
  pip install telethon
  set TELEGRAM_API_ID=...       (from https://my.telegram.org)
  set TELEGRAM_API_HASH=...
  set TELEGRAM_BOT_USERNAME=best1tarolog_bot
  set AFFILIATE_COMMISSION_PERMILLE=250   # 25%
  set AFFILIATE_DURATION_MONTHS=3

First run: interactive phone login → session saved to affiliate_session.session

To terminate program: AFFILIATE_COMMISSION_PERMILLE=0
Note: after lowering commission you must terminate (0) and wait ~24h before creating new program.
"""

from __future__ import annotations

import asyncio
import os
import sys

COMMISSION = int(os.getenv("AFFILIATE_COMMISSION_PERMILLE", "250"))
DURATION = int(os.getenv("AFFILIATE_DURATION_MONTHS", "3"))
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "best1tarolog_bot").lstrip("@")
API_ID = os.getenv("TELEGRAM_API_ID", "")
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION = os.getenv("AFFILIATE_SESSION_FILE", "affiliate_session")


def _print_ui_fallback() -> None:
    pct = COMMISSION / 10
    print(
        f"""
Telethon not configured or import failed.
Enable affiliate program manually in Telegram:

  1. Open bot profile @{BOT_USERNAME} → Edit → Affiliate program
  2. Commission: {pct:g}% ({COMMISSION} permille)
  3. Duration: {DURATION} months
  4. Save

Docs: docs/telegram-affiliate-program.md
"""
    )


async def main() -> int:
    if not API_ID or not API_HASH:
        print("TELEGRAM_API_ID and TELEGRAM_API_HASH are required for API setup.", file=sys.stderr)
        _print_ui_fallback()
        return 1

    try:
        from telethon import TelegramClient
        from telethon.tl.functions.bots import UpdateStarRefProgramRequest
    except ImportError:
        print("Install telethon: pip install telethon", file=sys.stderr)
        _print_ui_fallback()
        return 1

    client = TelegramClient(SESSION, int(API_ID), API_HASH)
    await client.start()
    print(f"Logged in. Configuring affiliate for @{BOT_USERNAME}...")
    print(f"  commission_permille={COMMISSION} ({COMMISSION / 10:g}%)")
    print(f"  duration_months={DURATION}")

    result = await client(
        UpdateStarRefProgramRequest(
            bot=BOT_USERNAME,
            commission_permille=COMMISSION,
            duration_months=DURATION,
        )
    )
    print("Success:", result)
    await client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
