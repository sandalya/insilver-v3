#!/usr/bin/env python3
"""InSilver Bot v3."""
import logging
import os
from telegram.ext import Application
from core.lock import acquire_lock
from core.config import BOT_TOKEN, LOGS_DIR
from bot.client import setup_handlers

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

def main():
    acquire_lock()
    log.info("🚀 InSilver v3 стартує...")

    app = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(app)

    log.info("✅ Бот запущений. Очікуємо повідомлення...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
