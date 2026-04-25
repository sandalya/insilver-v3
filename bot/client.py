"""Обробник повідомлень від клієнтів."""
import logging
import time
from pathlib import Path
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram import BotCommand
from core.config import BOT_TOKEN, ADMIN_IDS, MASTER_TELEGRAM, WEBSITE_URL
from core.ai import ask_ai
from core.order_context import has_order_intent
from core.catalog import search_catalog, format_item_text
from core.health import health_checker
from core.conversation_logger import log_user_message, log_bot_response, log_order_action, log_error_interaction
from bot.order import build_order_handler, build_new_order_handler
from core.router import classify_intent
from datetime import datetime

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


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Скасування поточної дії — для Ed QA та клієнтів."""
    ctx.user_data.clear()
    await update.message.reply_text("Скасовано. Чим можу допомогти? 😊")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "друже"
    username = user.username or user.first_name or "anonymous"
    
    log.info(f"START від {user.id} ({username})")
    health_checker.increment_messages()
    
    response = f"Вітаємо, {name}! 👋\n\nВи звернулись до майстерні InSilver — виготовляємо срібні прикраси на замовлення.\n\n💎 У нас є ланцюжки, браслети, печатки, хрести та інші вироби зі срібла 925°.\n\n🛠️ Працюємо як з готовими виробами, так і під індивідуальне замовлення.\n\nЧим можу допомогти?"
    
    # Створюємо клавіатуру з кнопками
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Наш сайт", url=WEBSITE_URL)],
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
        response = "📱 **Контакти майстерні InSilver:**\n\n" + \
                  f"🟢 **Telegram майстра:** {MASTER_TELEGRAM}\n" + \
                  f"🌐 **Сайт:** {WEBSITE_URL}\n" + \
                  "⏰ **Робочі години:** Пн-Пт 9:00-18:00\n\n" + \
                  "💬 **Для консультацій** з технічних питань, особливостей виготовлення або індивідуальних замовлень пишіть напряму майстру.\n\n" + \
                  "🛠️ **Складні питання** краще обговорювати особисто."
        await query.edit_message_text(response, parse_mode="Markdown")
    
    elif query.data == "show_catalog":
        response = "📋 **Основні категорії нашого каталогу:**\n\n" + \
                  "🔗 **Ланцюжки:** Рамзес, Тризуб, Якірний, Водоспад\n" + \
                  "📿 **Браслети:** Бісмарк, Рамзес, Фараон, Імператор\n" + \
                  "💍 **Перстні та печатки** різних розмірів\n" + \
                  "✝️ **Хрести та ладанки** з гравіюванням\n" + \
                  "🎨 **Ексклюзивні вироби** під замовлення\n\n" + \
                  "Напишіть назву виробу або плетіння, і я покажу варіанти з фото і цінами!"
        await query.edit_message_text(response, parse_mode="Markdown")


async def cmd_catalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /catalog command."""
    response = "📋 **Основні категорії нашого каталогу:**\n\n" + \
              "🔗 **Ланцюжки:** Рамзес, Тризуб, Якірний, Водоспад\n" + \
              "📿 **Браслети:** Бісмарк, Рамзес, Фараон, Імператор\n" + \
              "💍 **Перстні та печатки** різних розмірів\n" + \
              "✝️ **Хрести та ладанки** з гравіюванням\n" + \
              "🎨 **Ексклюзивні вироби** під замовлення\n\n" + \
              "Напишіть назву виробу або плетіння, і я покажу варіанти з фото і цінами!"
    await update.message.reply_text(response, parse_mode="Markdown")


async def cmd_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /contact command."""
    response = "📱 **Контакти InSilver:**\n\n" + \
              f"🌐 **Сайт:** {WEBSITE_URL}\n" + \
              f"🟢 **Telegram майстра:** {MASTER_TELEGRAM}\n" + \
              "⏰ **Робочі години:** Пн-Пт 9:00-18:00\n\n" + \
              "📞 **Для термінових питань** пишіть в особисті повідомлення майстру.\n" + \
              "🛠️ **Технічні консультації** та особливості виготовлення."
    await update.message.reply_text(response, parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    response = "❓ **Як користуватися ботом:**\n\n" + \
              "🔍 **Пошук:** Напишіть назву виробу (наприклад: \"ланцюжки\", \"браслет бісмарк\")\n" + \
              "📋 **Каталог:** Переглянути всі категорії виробів\n" + \
              "🛒 **Замовлення:** Два варіанти:\n" + \
              "   • Швидке замовлення конкретного виробу\n" + \
              "   • Індивідуальне замовлення під ваші параметри\n\n" + \
              "💬 **Питання:** Просто напишіть що вас цікавить, і я допоможу!\n\n" + \
              "📱 **Контакти:** /contact для зв'язку з майстром"
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages with comprehensive error handling."""
    try:
        from core.handoff import is_paused, safe_admin_send
        if is_paused(update.effective_chat.id):
            return
        user = update.effective_user
        text = update.message.text
        if not text or not text.strip():
            await update.message.reply_text("Напишіть ваше питання або побажання щодо виробу 🙂")
            return
        username = user.username or user.first_name or "anonymous"
        
        log.info(f"MSG від {user.id}: {text[:80]}")
        health_checker.increment_messages()

        # Якщо клієнт в процесі замовлення — не втручаємось
        if ctx.user_data.get("order"):
            return



        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

        # Логування повідомлення користувача
        log_user_message(user.id, username, text)

        # Keyword detection — handoff
        text_lower = text.lower()
        found_human = [t for t in HUMAN_TRIGGERS if t in text_lower]
        if found_human:
            await update.message.reply_text(
                "Передаю діалог майстру, він скоро підключиться! 🙏"
            )
            username_str = f"@{user.username}" if user.username else user.first_name
            for admin_id in ADMIN_IDS:
                await safe_admin_send(ctx, admin_id, lambda aid=admin_id: ctx.bot.send_message(aid,
                        f"🔔 КЛІЄНТ ПРОСИТЬ ЛЮДИНУ\n\n"
                        f"👤 {user.first_name} ({username_str})\n"
                        f"💬 «{text}»",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🤖 Повернути бота", callback_data=f"resume_{update.effective_chat.id}")
                        ]])
                ))
            from core.handoff import pause_bot
            pause_bot(update.effective_chat.id, reason=f"human: {', '.join(found_human)}")
            return

        found_complex = [kw for kw in COMPLEX_KEYWORDS if kw in text_lower]
        if found_complex:
            await update.message.reply_text(
                "Для таких виробів потрібна точна консультація майстра. "
                "Передаю йому ваш запит — він скоро зв'яжеться з вами! 🙏"
            )
            username_str = f"@{user.username}" if user.username else user.first_name
            for admin_id in ADMIN_IDS:
                await safe_admin_send(ctx, admin_id, lambda aid=admin_id: ctx.bot.send_message(aid,
                        f"🔔 СКЛАДНИЙ ВИРІБ\n\n"
                        f"👤 {user.first_name} ({username_str})\n"
                        f"💬 «{text}»\n"
                        f"🏷️ Ключові слова: {', '.join(found_complex)}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🤖 Повернути бота", callback_data=f"resume_{update.effective_chat.id}")
                        ]])
                ))
            from core.handoff import pause_bot
            pause_bot(update.effective_chat.id, reason=f"complex: {', '.join(found_complex)}")
            return

        # Smart Router — класифікуємо намір
        intent = classify_intent(text)

        response = ""
        ai_time = 0
        has_photos = False

        if intent == "SEARCH":
            try:
                items, found = search_catalog(text)
            except Exception as e:
                log.error(f"Помилка пошуку в каталозі: {e}")
                log_error_interaction(user.id, username, f"Catalog search error: {e}", text[:50])
                items, found = [], False

            if found:
                log.info(f"SEARCH: знайдено {len(items)} для '{text[:40]}'")
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
                    photos_sent = 0
                    for item in items:
                        try:
                            await ctx.bot.send_chat_action(update.effective_chat.id, "upload_photo")
                            await send_item_with_photo(update, item)
                            photos_sent += 1
                        except Exception as e:
                            log.error(f"Помилка відправки фото {item.get('title', 'N/A')}: {e}")
                    log.info(f"Надіслано фото: {photos_sent}/{len(items)}")
                except Exception as e:
                    log.error(f"Помилка обробки товарів: {e}")
                    log_error_interaction(user.id, username, f"Items processing error: {e}", text[:50])
                    response = "Вибачте, виникла проблема з обробкою результатів пошуку. Спробуйте ще раз."
                    await update.message.reply_text(response)
            else:
                log.info(f"SEARCH але каталог порожній для '{text[:40]}' — fallback до AI")
                try:
                    start_time = time.time()
                    response = await ask_ai(user.id, text, ctx.user_data.get("history", []))
                    ai_time = time.time() - start_time
                    await update.message.reply_text(response, parse_mode="Markdown")
                except Exception as e:
                    log.error(f"Помилка AI: {e}")
                    response = "Вибачте, зараз не можу обробити запит. Спробуйте ще раз."
                    await update.message.reply_text(response)

        elif intent == "SOCIAL":
            log.info(f"SOCIAL: '{text[:40]}'")
            try:
                start_time = time.time()
                response = await ask_ai(user.id, text, ctx.user_data.get("history", []))
                ai_time = time.time() - start_time
                await update.message.reply_text(response, parse_mode="Markdown")
            except Exception as e:
                log.error(f"Помилка AI (SOCIAL): {e}")
                response = "Дякую! Звертайтесь 😊"
                await update.message.reply_text(response)

        else:
            log.info(f"{intent}: '{text[:40]}'")
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

async def setup_bot_commands(app: Application):
    """Встановити команди меню для бота."""
    commands = [
        BotCommand("start", "🏠 Головна сторінка"),
        BotCommand("catalog", "📋 Показати каталог виробів"),
        BotCommand("order", "📝 Індивідуальне замовлення"),
        BotCommand("contact", "📱 Контакти майстерні"),
        BotCommand("help", "❓ Допомога")
    ]
    
    try:
        await app.bot.set_my_commands(commands)
        log.info(f"✅ Встановлено {len(commands)} команд меню")
    except Exception as e:
        log.error(f"❌ Помилка встановлення команд меню: {e}")


COMPLEX_KEYWORDS = [
    "індивідуальний дизайн", "унікальний дизайн", "своє ескіз", "свій ескіз",
    "гравіювання", "гравіровка", "гравірування",
    "весільн", "корпоративн", "оптом", "партія",
    "комплект", "каблучк", "перстен", "вушк"
]

HUMAN_TRIGGERS = [
    "людина", "людину", "менеджер", "менеджера", "майстер", "майстра",
    "позвати когось", "живий оператор", "оператор", "человек", "мастер"
]


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Якщо адмін у режимі тренера — фото не для handoff, а для trainer
    if ctx.user_data.get("trainer"):
        from bot.admin import handle_trainer_photo
        return await handle_trainer_photo(update, ctx)
    from core.handoff import pause_bot
    user = update.effective_user
    chat_id = update.effective_chat.id

    photo = update.message.photo[-1] if update.message.photo else None
    doc = update.message.document if not photo else None
    file_obj = photo or doc
    if not file_obj:
        return

    tg_file = await file_obj.get_file()
    save_dir = Path("data/photos/incoming")
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = save_dir / filename
    await tg_file.download_to_drive(str(filepath))

    await update.message.reply_text(
        "Дякую за фото! 📸 Передав його майстру для точної оцінки. "
        "Хвилинку, він скоро відповість."
    )

    username = f"@{user.username}" if user.username else user.first_name
    caption = (
        f"📸 ФОТО ВІД КЛІЄНТА\n\n"
        f"👤 {user.first_name} ({username})\n"
        f"💬 {update.message.caption or 'без підпису'}"
    )
    for admin_id in ADMIN_IDS:
        async def _notify(aid):
            await ctx.bot.send_photo(aid, file_obj.file_id, caption=caption)
            await ctx.bot.send_message(aid,
                f"Бот поставлено на паузу для цього клієнта.\n"
                f"Зв\'яжіться з клієнтом напряму, потім поверніть бота:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🤖 Повернути бота", callback_data=f"resume_{chat_id}")
                ]])
            )
        try:
            await _notify(admin_id)
        except Exception as e:
            msg = str(e)
            if "Chat not found" in msg or "chat not found" in msg.lower():
                log.warning(f"Admin {admin_id} peer not in cache, warming up...")
                try:
                    await ctx.bot.send_chat_action(admin_id, "typing")
                    await _notify(admin_id)
                    log.info(f"Admin {admin_id} notified after warmup")
                except Exception as e2:
                    log.error(f"Admin {admin_id} unreachable after warmup: {e2}")
            else:
                log.error(f"Не вдалось сповістити адміна {admin_id}: {e}")

    pause_bot(chat_id, reason="photo")
    log.info(f"HANDOFF (photo): user {user.id}, chat paused")


async def handle_resume(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from core.handoff import resume_bot
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Тільки для адміна")
        return
    chat_id = int(query.data.split("_", 1)[1])
    resume_bot(chat_id)
    await query.answer("Бот повернено!")
    await query.message.edit_text(
        query.message.text + "\n\n✅ Бот повернено в роботу"
    )
    log.info(f"RESUME: chat {chat_id} by admin {query.from_user.id}")


def setup_handlers(app: Application):
    # Import admin handlers
    from bot.admin import create_admin_handlers
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # ✅ CLAUDE.AI: Debug handler ПЕРШИМ (group=-1)
    import os
    if os.getenv("DEBUG") == "1":
        app.add_handler(MessageHandler(filters.ALL, debug_all_updates), group=-1)
    
    # ✅ Regular handlers BEFORE admin (нижчий пріоритет групи)
    app.add_handler(CommandHandler("cancel", cmd_cancel), group=1)
    app.add_handler(CommandHandler("start", cmd_start), group=1)
    app.add_handler(CommandHandler("catalog", cmd_catalog), group=1)
    app.add_handler(CommandHandler("contact", cmd_contact), group=1)  
    app.add_handler(CommandHandler("help", cmd_help), group=1)
    # ✅ ORDER HANDLER FIRST - має перехоплювати conversations перед загальним handler
    app.add_handler(build_order_handler(), group=1)
    
    # Callback handlers з specific patterns (НЕ include order_full - воно в conversation handler)  
    app.add_handler(CallbackQueryHandler(handle_resume, pattern=r"^resume_"), group=1)
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo), group=1)
    app.add_handler(CallbackQueryHandler(handle_callback_query, pattern="^(contact_master|show_catalog)$"), group=1)
    
    # General message handler LAST - щоб не перехоплював conversation messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message), group=1)  
    
    # ✅ Admin handlers в окремій групі з вищим номером (lower priority)
    for handler in create_admin_handlers():
        app.add_handler(handler, group=2)
    
    log.info("Handlers: regular (group=1) + admin (group=2) + debug (group=-1)")
    
    # Встановлюємо команди меню після створення app  
    app.post_init = setup_bot_commands
