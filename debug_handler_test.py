#!/usr/bin/env python3
"""
Радикальний тест - кастомний handler що логує ВСЕ
"""
import logging
import asyncio
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/home/sashok/.openclaw/workspace/insilver-v3/logs/debug_handler.log"),
        logging.StreamHandler()
    ]
)

TOKEN = "8627781342:AAGRpzlKRGmABft7QkTIyzZjWHk4SFqw4wI"
log = logging.getLogger("debug_handler")

async def debug_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логувати абсолютно ВСЕ що прилітає"""
    try:
        log.info("🎯 RECEIVED UPDATE!")
        log.info(f"Update ID: {update.update_id}")
        
        if update.message:
            user = update.message.from_user
            text = update.message.text
            log.info(f"📨 MESSAGE: '{text}' від {user.id} ({user.username})")
            
            # Відповідь
            await update.message.reply_text(f"✅ DEBUG отримав: '{text}'")
        else:
            log.info(f"📨 NON-MESSAGE UPDATE: {update}")
            
    except Exception as e:
        log.error(f"💥 Debug handler error: {e}")
        import traceback
        log.error(traceback.format_exc())

async def main():
    log.info("🚀 DEBUG HANDLER TEST STARTING...")
    
    # Create app
    app = Application.builder().token(TOKEN).build()
    
    # Add ONE simple handler that catches EVERYTHING
    app.add_handler(MessageHandler(filters.ALL, debug_all_updates))
    log.info("✅ Debug handler додано")
    
    # Start
    await app.initialize()
    await app.start()
    log.info("✅ App started")
    
    # Start polling
    await app.updater.start_polling(
        drop_pending_updates=False,
        poll_interval=1.0,
        timeout=5,
    )
    log.info("🎯 DEBUG POLLING STARTED!")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())