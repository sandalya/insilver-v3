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
