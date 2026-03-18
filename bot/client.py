"""Обробник повідомлень від клієнтів."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.config import BOT_TOKEN, ADMIN_IDS
from core.ai import ask_ai

log = logging.getLogger("bot.client")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "друже"
    log.info(f"START від {user.id} ({user.first_name})")
    await update.message.reply_text(
        f"Вітаємо, {name} 👋\n\n"
        f"Ви звернулись до майстерні InSilver — виготовляємо срібні прикраси на замовлення.\n\n"
        f"Чим можу допомогти?"
    )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    log.info(f"MSG від {user.id}: {text[:80]}")

    # Показуємо що думаємо
    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    response = await ask_ai(
        user_id=user.id,
        message=text,
        history=ctx.user_data.get("history", [])
    )

    # Зберігаємо історію розмови
    history = ctx.user_data.get("history", [])
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": response})
    # Тримаємо тільки останні 20 повідомлень
    ctx.user_data["history"] = history[-20:]

    await update.message.reply_text(response, parse_mode="Markdown")

def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Handlers зареєстровано")
