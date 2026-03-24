#!/usr/bin/env python3
"""InSilver Bot v3."""
import logging
import os
import sys
import signal
import traceback
import asyncio
from telegram.ext import Application
from core.lock import acquire_lock, release_lock
from core.config import BOT_TOKEN, LOGS_DIR
from core.health import health_checker
from bot.client import setup_handlers

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("main")

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global uncaught exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    log.critical("💥 Критична помилка:", exc_info=(exc_type, exc_value, exc_traceback))
    release_lock()

def setup_health_monitoring():
    """Setup basic health monitoring."""
    import signal
    
    def save_health_on_signal(signum, frame):
        health_checker.save_status()
        
        # Notify systemd watchdog if available
        try:
            import systemd.daemon
            systemd.daemon.notify("WATCHDOG=1")
        except ImportError:
            pass
    
    # Setup periodic health save on signals
    signal.signal(signal.SIGUSR1, save_health_on_signal)
    
    # Initial health save
    health_checker.save_status()

def main():
    """Main entry point with comprehensive error handling."""
    sys.excepthook = global_exception_handler
    
    try:
        # Validate configuration
        if not BOT_TOKEN:
            log.error("❌ TELEGRAM_TOKEN не встановлений в .env")
            sys.exit(1)
        
        acquire_lock()
        log.info("🚀 InSilver v3 стартує...")

        # Build application with error handling
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Setup handlers
        setup_handlers(app)
        
        # Setup health monitoring
        setup_health_monitoring()
        health_checker.mark_activity()
        
        log.info("✅ Бот запущений. Очікуємо повідомлення...")
        
        # Run with automatic restart on connection issues
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=None,
            close_loop=True
        )
        
    except KeyboardInterrupt:
        log.info("⏹️ Отримано SIGINT, завершуємо...")
    except Exception as e:
        log.critical(f"💥 Критична помилка в main(): {e}")
        log.critical(f"Traceback:\n{traceback.format_exc()}")
        health_checker.increment_errors()
        sys.exit(1)
    finally:
        log.info("🔄 Завершуємо роботу...")
        release_lock()

if __name__ == "__main__":
    main()
