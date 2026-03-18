#!/usr/bin/env python3
"""InSilver Bot v3 — точка входу."""
import asyncio
import logging
import os
from core.lock import acquire_lock
from core.config import LOGS_DIR

# Логування
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("main")

async def main():
    acquire_lock()
    log.info("🚀 InSilver v3 стартує...")
    # TODO: запуск бота
    log.info("✅ Готово")

if __name__ == "__main__":
    asyncio.run(main())
