#!/usr/bin/env python3
"""
Абсолютно мінімальний Telegram бот для тестування
"""
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

TOKEN = "8627781342:AAGRpzlKRGmABft7QkTIyzZjWHk4SFqw4wI"
log = logging.getLogger("test_minimal")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    user = update.effective_user
    log.info(f"🎯 START від {user.id} ({user.username or user.first_name})")
    
    await update.message.reply_text(
        f"✅ Мінімальний бот працює!\\n"
        f"Привіт, {user.first_name}!\\n"
        f"Час: {update.message.date}\\n"
        f"ID: {user.id}"
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages"""
    user = update.effective_user
    text = update.message.text
    
    log.info(f"🎯 MSG від {user.id}: '{text}'")
    
    await update.message.reply_text(
        f"🔥 Отримав: '{text}'\\n"
        f"От: {user.first_name}\\n"
        f"Мінімальний бот ПРАЦЮЄ!"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    log.error(f"💥 Error: {context.error}")

async def main():
    log.info("🚀 MINIMAL BOT STARTING...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    log.info("🎯 Handlers added")
    
    # Start polling
    await app.initialize()
    await app.start()
    
    log.info("🎯 Starting polling...")
    await app.updater.start_polling(
        drop_pending_updates=False,
        poll_interval=1.0,
        timeout=10,
        read_timeout=10,
        write_timeout=10,
        connect_timeout=10,
    )
    
    log.info("✅ MINIMAL BOT READY!")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        log.info("⏹️ Stopping...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())