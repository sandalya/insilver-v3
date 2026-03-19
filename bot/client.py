"""Обробник повідомлень від клієнтів."""
import logging
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.config import BOT_TOKEN, ADMIN_IDS
from core.ai import ask_ai
from core.order_context import has_order_intent
from core.catalog import search_catalog, format_item_text
from bot.order import build_order_handler

log = logging.getLogger("bot.client")

LOGO_SIZE = 61514


def order_keyboard(item: dict, idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Замовити", callback_data=f"o:{idx}")],
        [InlineKeyboardButton("📋 Оформити замовлення", callback_data="order_full")],
    ])


async def send_item_with_photo(update: Update, item: dict):
    from pathlib import Path
    caption = format_item_text(item)
    # Знаходимо індекс товару в каталозі
    try:
        import json as _json
        from core.config import SITE_CATALOG
        _catalog = _json.loads(Path(SITE_CATALOG).read_text(encoding="utf-8"))
        _items = _catalog.get("items", [])
        _url = item.get("url", "")
        _idx = next((i for i, x in enumerate(_items) if x.get("url") == _url), 0)
    except Exception:
        _idx = 0
    keyboard = order_keyboard(item, _idx)
    all_photos = item.get("local_photos") or []
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
                await update.message.reply_text(
                    f"👆 *{item.get('title', '')}*",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                return
            except Exception as e:
                log.warning(f"Медіагрупа не вдалась: {e}")

    if local_photo:
        try:
            await update.message.reply_photo(
                photo=open(local_photo, "rb"),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            return
        except Exception as e:
            log.warning(f"Фото не вдалось: {e}")

    await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=keyboard)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "друже"
    log.info(f"START від {user.id} ({user.first_name})")
    await update.message.reply_text(
        f"Вітаємо, {name}\n\nВи звернулись до майстерні InSilver — виготовляємо срібні прикраси на замовлення.\n\nЧим можу допомогти?"
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    log.info(f"MSG від {user.id}: {text[:80]}")

    # Якщо клієнт в процесі замовлення — не втручаємось
    if ctx.user_data.get("order"):
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    items, found = search_catalog(text)
    response = ""

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

    # Якщо клієнт явно хоче замовити — показуємо кнопку
    if has_order_intent(text):
        await update.message.reply_text(
            "Готові оформити замовлення? 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Оформити замовлення", callback_data="order_full")
            ]])
        )


def setup_handlers(app: Application):
    app.add_handler(build_order_handler())
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Handlers зареєстровано")
