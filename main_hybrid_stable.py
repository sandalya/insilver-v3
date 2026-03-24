#!/usr/bin/env python3
"""InSilver Bot v3 - Гібрідна стабільна версія."""
import logging
import os
import sys
import signal
import traceback
import asyncio
import time
from telegram.ext import Application
from telegram.error import Conflict, TimedOut, NetworkError
from core.lock import acquire_lock, release_lock
from core.config import BOT_TOKEN, LOGS_DIR
from core.health import health_checker
from bot.client import setup_handlers

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Enhanced logging setup with DEBUG for troubleshooting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot.log"),
        logging.StreamHandler()
    ]
)

# Enable debug for telegram library
logging.getLogger("telegram.ext.Updater").setLevel(logging.DEBUG)

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

async def stable_error_handler(update: object, context):
    """Enhanced error handler for stability"""
    error = context.error
    
    log.error(f"💥 Telegram error: {error}")
    
    if isinstance(error, Conflict):
        log.critical("🚨 КОНФЛІКТ ТОКЕНІВ! Зупиняємо бот...")
        # Stop application to avoid further conflicts
        if hasattr(context, 'application') and context.application:
            await context.application.stop()
            return
    
    elif isinstance(error, (TimedOut, NetworkError)):
        log.warning(f"⚠️ Мережева помилка: {error}")
        # Continue operation for network issues
        
    else:
        log.error(f"❓ Невідома помилка: {error}")
        health_checker.increment_errors()

async def check_token_conflicts(app: Application):
    """Check for token conflicts before starting"""
    log.info("🔍 Перевірка конфліктів токенів...")
    
    try:
        # Initialize if needed
        if not app.bot._initialized:
            await app.bot.initialize()
        
        # Try to get bot info
        bot_info = await app.bot.get_me()
        log.info(f"✅ Токен валідний: @{bot_info.username}")
        
        # Try a simple getUpdates call to check for conflicts
        updates = await app.bot.get_updates(limit=1, timeout=5)
        log.info(f"✅ getUpdates тест пройшов: {len(updates)} updates")
        
        return True
        
    except Conflict as e:
        log.error(f"🚨 КОНФЛІКТ ТОКЕНІВ: {e}")
        return False
    except Exception as e:
        log.error(f"❌ Помилка перевірки токена: {e}")
        return False

def main():
    """Main entry point with comprehensive error handling."""
    sys.excepthook = global_exception_handler
    
    async def async_main():
        try:
            # Validate configuration
            if not BOT_TOKEN:
                log.error("❌ TELEGRAM_TOKEN не встановлений в .env")
                sys.exit(1)
            
            acquire_lock()
            log.info("🚀 InSilver v3 HYBRID стартує...")

            # Build application with error handling
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Add enhanced error handler first
            app.add_error_handler(stable_error_handler)
            
            # Setup existing handlers (from bot.client)
            setup_handlers(app)
            
            # Check for token conflicts
            await app.initialize()
            
            if not await check_token_conflicts(app):
                log.error("❌ Не вдалося пройти перевірку конфліктів")
                return
            
            # Setup health monitoring
            setup_health_monitoring()
            health_checker.mark_activity()
            
            log.info("✅ Бот запущений. Очікуємо повідомлення...")
            
            # Start with stable polling settings
            await app.start()
            
            # Start polling with STABLE settings
            await app.updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                bootstrap_retries=-1,  # Infinite retries
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30,
                drop_pending_updates=False,  # ⭐ CRITICAL: Don't drop messages!
            )
            
            log.info("🎯 Polling запущено стабільно")
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
                health_checker.mark_activity()
        
        except KeyboardInterrupt:
            log.info("⏹️ Отримано SIGINT, завершуємо...")
        except Exception as e:
            log.critical(f"💥 Критична помилка в main(): {e}")
            log.critical(f"Traceback:\\n{traceback.format_exc()}")
            health_checker.increment_errors()
            raise
        finally:
            log.info("🔄 Завершуємо роботу...")
            if 'app' in locals():
                await app.stop()
                await app.shutdown()
            release_lock()
    
    # Run async main
    try:
        asyncio.run(async_main())
    except Exception as e:
        log.critical(f"💥 Критична помилка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()