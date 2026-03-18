"""Обробник повідомлень від клієнтів."""
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.config import BOT_TOKEN, ADMIN_IDS
from core.ai import ask_ai
from core.catalog import search_catalog, format_item_text
log = logging.getLogger("bot.client")

LOGO_SIZE = 61514  # розмір логотипу InSilver — фільтруємо

async def send_item_with_photo(update: Update, item: dict):
    """Відправляє товар з фото."""
    from pathlib import Path
    caption = format_item_text(item)
    all_photos = item.get("local_photos") or []
    # Фільтруємо логотип по розміру
    local_photos = [p for p in all_photos if Path(p).exists() and Path(p).stat().st_size != LOGO_SIZE]
    local_photo = local_photos[0] if local_photos else None

    if len(local_photos) > 1:
        media = []
        for i, path in enumerate(local_photos[:4]):
            try:
                cap = caption if i == 0 else None
                media.append(InputMediaPhoto(
                    media=open(path, "rb"),
                    caption=cap,
                    parse_mode="Markdown"
                ))
            except Exception as e:
                log.warning(f"Не вдалось відкрити фото {path}: {e}")
        if len(media) > 1:
            try:
                await update.message.reply_media_group(media=media)
                return
            except Exception as e:
                log.warning(f"Медіагрупа не вдалась: {e}")

    if local_photo:
        try:
            await update.message.reply_photo(
                photo=open(local_photo, "rb"),
                caption=caption,
                parse_mode="Markdown"
            )
            return
        except Exception as e:
            log.warning(f"Фото не вдалось: {e}")

    await update.message.reply_text(caption, parse_mode="Markdown")

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
    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    items, found = search_catalog(text)

    if found:
        log.info(f"Каталог: знайдено {len(items)} товарів для '{text[:40]}'")
        items_desc = "\n\n".join(format_item_text(i) for i in items)
        augmented = (
            f"Клієнт питає: {text}\n\n"
            f"Знайдено в каталозі {len(items)} варіанти:\n{items_desc}\n\n"
            f"Коротко представ ці товари (1-2 речення), скажи що зараз покажеш фото. "
            f"Не вигадуй деталей яких немає."
        )
        response = await ask_ai(user.id, augmented, ctx.user_data.get("history", []))
        await update.message.reply_text(response, parse_mode="Markdown")
        for item in items:
            await ctx.bot.send_chat_action(update.effective_chat.id, "upload_photo")
            await send_item_with_photo(update, item)
    else:
        log.info(f"Каталог: нічого не знайдено для '{text[:40]}'")
        response = await ask_ai(user.id, text, ctx.user_data.get("history", []))
        await update.message.reply_text(response, parse_mode="Markdown")

    history = ctx.user_data.get("history", [])
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": response})
    ctx.user_data["history"] = history[-20:]

def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Handlers зареєстровано")
