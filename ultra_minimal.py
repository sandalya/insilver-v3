#!/usr/bin/env python3
"""
СУПЕР-МІНІМАЛЬНИЙ тест без жодних додаткових імпортів
"""
import asyncio
from telegram.ext import Application, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

TOKEN = "8627781342:AAGRpzlKRGmABft7QkTIyzZjWHk4SFqw4wI"

async def ultra_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Абсолютно простий handler"""
    print(f"🎉 ULTRA HANDLER ПРАЦЮЄ! Text: {update.message.text}")
    await update.message.reply_text("🎉 Ultra minimal працює!")

async def main():
    print("🚀 Ultra minimal starting...")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, ultra_handler))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=False)
    
    print("✅ Ultra minimal ready!")
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())