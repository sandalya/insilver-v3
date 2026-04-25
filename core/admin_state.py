"""Runtime state активних адмін-сесій.

Зберігається у data/admin_active.json. При старті бота файл очищується
(всі адміни виходять автоматично). Включається через /admin, виключається
повторним /admin.
"""
import json
import logging
from pathlib import Path
from typing import Set

log = logging.getLogger("core.admin_state")

STATE_FILE = Path(__file__).parent.parent / "data" / "admin_active.json"


def _load() -> Set[int]:
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding='utf-8'))
        return {int(uid) for uid in data}
    except Exception as e:
        log.warning(f"admin_active.json пошкоджений: {e}, скидаю")
        return set()


def _save(active: Set[int]):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(list(active)), encoding='utf-8')


def is_active(user_id: int) -> bool:
    """Чи активний адмін-режим у цього юзера."""
    return user_id in _load()


def activate(user_id: int):
    """Увімкнути адмін-режим."""
    active = _load()
    active.add(user_id)
    _save(active)
    log.info(f"admin activated: {user_id}")


def deactivate(user_id: int):
    """Вимкнути адмін-режим."""
    active = _load()
    active.discard(user_id)
    _save(active)
    log.info(f"admin deactivated: {user_id}")


def reset_all():
    """Скинути всі активні сесії (викликається при старті бота)."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    log.info("all admin sessions reset")
