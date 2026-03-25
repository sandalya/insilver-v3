"""Обробник повідомлень від клієнтів."""
import logging
import time
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from core.config import BOT_TOKEN, ADMIN_IDS
from core.ai import ask_ai
from core.order_context import has_order_intent
from core.catalog import search_catalog, format_item_text
from core.health import health_checker
from core.conversation_logger import log_user_message, log_bot_response, log_order_action, log_error_interaction
from bot.order import build_order_handler

log = logging.getLogger("bot.client")

LOGO_SIZE = 61514


def order_keyboard(item: dict, idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Замовити цей виріб", callback_data=f"o:{idx}")],
        [InlineKeyboardButton("📝 Індивідуальне замовлення", callback_data="order_full")],
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
    username = user.username or user.first_name or "anonymous"
    
    log.info(f"START від {user.id} ({username})")
    health_checker.increment_messages()
    
    response = f"Вітаємо, {name}! 👋\n\nВи звернулись до майстерні InSilver — виготовляємо срібні прикраси на замовлення.\n\n💎 У нас є ланцюжки, браслети, печатки, хрести та інші вироби зі срібла 925°.\n\n🛠️ Працюємо як з готовими виробами, так і під індивідуальне замовлення.\n\nЧим можу допомогти?"
    
    # Створюємо клавіатуру з кнопками
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Наш сайт", url="https://insilver.com.ua")],
        [InlineKeyboardButton("📱 Зв'язок з майстром", callback_data="contact_master")],
        [InlineKeyboardButton("📋 Показати каталог", callback_data="show_catalog")],
    ])
    
    # Логування
    log_user_message(user.id, username, "/start")
    log_bot_response(user.id, username, response)
    
    await update.message.reply_text(response, reply_markup=keyboard)


async def handle_callback_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "contact_master":
        response = "📱 **Контакти майстра Влада:**\n\n" + \
                  "🟢 Telegram: @vlad_insilver\n" + \
                  "📞 Телефон: +380XX XXX XXXX\n" + \
                  "⏰ Робочі години: Пн-Пт 9:00-18:00\n\n" + \
                  "Майстер консультує з технічних питань і особливостей виготовлення."
        await query.edit_message_text(response, parse_mode="Markdown")
    
    elif query.data == "show_catalog":
        response = "📋 **Основні категорії нашого каталогу:**\n\n" + \
                  "🔗 **Ланцюжки:** Рамзес, Тризуб, Якірний, Водоспад\n" + \
                  "📿 **Браслети:** Бісмарк, Рамзес, Фараон, Імператор\n" + \
                  "💍 **Печатки та персні** різних розмірів\n" + \
                  "✝️ **Хрести та ладанки** з гравіюванням\n" + \
                  "🎨 **Ексклюзивні вироби** під замовлення\n\n" + \
                  "Напишіть назву виробу або плетіння, і я покажу варіанти з фото і цінами!"
        await query.edit_message_text(response, parse_mode="Markdown")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages with comprehensive error handling."""
    try:
        user = update.effective_user
        text = update.message.text
        username = user.username or user.first_name or "anonymous"
        
        log.info(f"MSG від {user.id}: {text[:80]}")
        health_checker.increment_messages()

        # Якщо клієнт в процесі замовлення — не втручаємось
        if ctx.user_data.get("order"):
            return

        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

        # Search catalog with error handling
        try:
            items, found = search_catalog(text)
        except Exception as e:
            log.error(f"Помилка пошуку в каталозі: {e}")
            log_error_interaction(user.id, username, f"Catalog search error: {e}", text[:50])
            items, found = [], False

        # Логування повідомлення користувача
        log_user_message(user.id, username, text, len(items) if found else 0)

        response = ""
        ai_time = 0
        has_photos = False

        if found:
            log.info(f"Каталог: знайдено {len(items)} товарів для '{text[:40]}'")
            try:
                items_desc = "\n\n".join(format_item_text(i) for i in items)
                augmented = (
                    f"Клієнт питає: {text}\n\n"
                    f"Знайдено в каталозі {len(items)} варіанти:\n{items_desc}\n\n"
                    f"Коротко представ ці товари (1-2 речення), скажи що зараз покажеш фото. "
                    f"Не вигадуй деталей яких немає."
                )
                
                start_time = time.time()
                response = await ask_ai(user.id, augmented, ctx.user_data.get("history", []))
                ai_time = time.time() - start_time
                has_photos = True
                
                await update.message.reply_text(response, parse_mode="Markdown")
                
                # Send photos with error recovery
                photos_sent = 0
                for item in items:
                    try:
                        await ctx.bot.send_chat_action(update.effective_chat.id, "upload_photo")
                        await send_item_with_photo(update, item)
                        photos_sent += 1
                    except Exception as e:
                        log.error(f"Помилка відправки фото для товару {item.get('title', 'N/A')}: {e}")
                        log_error_interaction(user.id, username, f"Photo send error: {e}", item.get('title', 'N/A'))
                        # Continue with other items
                        
                log.info(f"Надіслано фото: {photos_sent}/{len(items)}")
                
            except Exception as e:
                log.error(f"Помилка обробки знайденних товарів: {e}")
                log_error_interaction(user.id, username, f"Items processing error: {e}", text[:50])
                response = "Вибачте, виникла проблема з обробкою результатів пошуку. Спробуйте ще раз."
                ai_time = 0
                await update.message.reply_text(response)
        else:
            log.info(f"Каталог: нічого не знайдено для '{text[:40]}'")
            try:
                start_time = time.time()
                response = await ask_ai(user.id, text, ctx.user_data.get("history", []))
                ai_time = time.time() - start_time
                await update.message.reply_text(response, parse_mode="Markdown")
            except Exception as e:
                log.error(f"Помилка AI відповіді: {e}")
                log_error_interaction(user.id, username, f"AI response error: {e}", text[:50])
                response = "Вибачте, зараз не можу обробити ваш запит. Спробуйте ще раз пізніше."
                ai_time = 0
                await update.message.reply_text(response)

        # Логування відповіді бота
        if response:
            log_bot_response(user.id, username, response, ai_time, has_photos)

        # Update history safely
        try:
            history = ctx.user_data.get("history", [])
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": response})
            ctx.user_data["history"] = history[-20:]
        except Exception as e:
            log.warning(f"Помилка збереження історії: {e}")

        # Show order button if needed
        try:
            if has_order_intent(text):
                log_order_action(user.id, username, "order_button_shown", {"trigger": text[:50]})
                await update.message.reply_text(
                    "Готові оформити замовлення? 👇",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📋 Оформити замовлення", callback_data="order_full")
                    ]])
                )
        except Exception as e:
            log.warning(f"Помилка показу кнопки замовлення: {e}")
            
    except Exception as e:
        log.error(f"💥 Критична помилка в handle_message: {e}")
        log_error_interaction(user.id, user.username or "unknown", f"Critical error: {e}", text[:50] if 'text' in locals() else "unknown")
        try:
            await update.message.reply_text(
                "Вибачте, сталася технічна помилка. Спробуйте ще раз або зверніться до @Vlad_InSilver"
            )
        except:
            pass  # If we can't even send error message, just log


async def error_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Global error handler for the bot."""
    log.error(f"💥 Bot error: {ctx.error}")
    health_checker.increment_errors()
    
    # Notify user if possible
    if update and update.effective_chat:
        try:
            await ctx.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Вибачте, сталася технічна помилка. Спробуйте ще раз."
            )
        except:
            pass  # Can't send message

async def debug_all_updates(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Debug handler - спрацює на БУДЬ-ЩО (Claude.AI рекомендація)"""
    log.info(f"🔍 [DEBUG] RAW UPDATE: {type(update)} - {update}")
    if update.message:
        log.info(f"🔍 [DEBUG] MESSAGE TEXT: {update.message.text}")
    elif update.edited_message:
        log.info(f"🔍 [DEBUG] EDITED MESSAGE: {update.edited_message.text}")
    else:
        log.info(f"🔍 [DEBUG] OTHER UPDATE TYPE")

def setup_handlers(app: Application):
    # Import admin handlers
    from bot.admin import create_admin_handlers
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # ✅ CLAUDE.AI: Debug handler ПЕРШИМ (group=-1)
    app.add_handler(MessageHandler(filters.ALL, debug_all_updates), group=-1)
    
    # ✅ Regular handlers BEFORE admin (нижчий пріоритет групи)
    app.add_handler(CommandHandler("start", cmd_start), group=1)
    app.add_handler(CallbackQueryHandler(handle_callback_query), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message), group=1)
    app.add_handler(build_order_handler(), group=1)  
    
    # ✅ Admin handlers в окремій групі з вищим номером (lower priority)
    for handler in create_admin_handlers():
        app.add_handler(handler, group=2)
    
    log.info("Handlers: regular (group=1) + admin (group=2) + debug (group=-1)")
