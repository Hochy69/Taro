import asyncio

from app.infrastructure.tasks import run_async


def test_run_async_reuses_event_loop():
  async def current_loop():
    return asyncio.get_event_loop()

  loop1 = run_async(current_loop())
  loop2 = run_async(current_loop())
  assert loop1 is loop2
  assert not loop1.is_closed()
