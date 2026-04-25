"""Управління Human Handoff — зупинка/відновлення автовідповідей."""
import json
from pathlib import Path

HANDOFF_FILE = Path(__file__).parent.parent / "data" / "handoff_state.json"

def _load() -> dict:
    if HANDOFF_FILE.exists():
        with open(HANDOFF_FILE, "r") as f:
            return json.load(f)
    return {}

def _save(data: dict):
    with open(HANDOFF_FILE, "w") as f:
        json.dump(data, f)

def is_paused(chat_id: int) -> bool:
    return str(chat_id) in _load()

def pause_bot(chat_id: int, reason: str = ""):
    data = _load()
    data[str(chat_id)] = {"reason": reason}
    _save(data)

def resume_bot(chat_id: int):
    data = _load()
    data.pop(str(chat_id), None)
    _save(data)


# === Safe admin notify (handles cold PTB peer cache after restart) ===
import logging
_log = logging.getLogger("core.handoff")


async def safe_admin_send(ctx, admin_id: int, send_fn) -> bool:
    """Викликає send_fn(); при 'Chat not found' прогріває peer і повторює.

    send_fn — callable без аргументів, що робить власне відправку
    (наприклад: lambda: ctx.bot.send_message(admin_id, "...", reply_markup=...))

    Повертає True якщо відправлено, False якщо peer недоступний.
    """
    try:
        await send_fn()
        return True
    except Exception as e:
        msg = str(e)
        if "Chat not found" not in msg and "chat not found" not in msg.lower():
            _log.error(f"Admin {admin_id} notify error (non-peer): {e}")
            return False
        _log.warning(f"Admin {admin_id} peer not in cache, warming up...")
        try:
            await ctx.bot.send_chat_action(admin_id, "typing")
            await send_fn()
            _log.info(f"Admin {admin_id} notified after warmup")
            return True
        except Exception as e2:
            _log.error(f"Admin {admin_id} unreachable after warmup: {e2}")
            return False
