"""Адмін панель — спрощена версія."""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from core.config import ADMIN_IDS, DATA_DIR
from core.conversation_logger import get_conversation_stats as get_stats
from bot.admin_orders import (
    cmd_orders, handle_orders_callback, handle_order_edit, handle_search_order,
    handle_status_change, handle_set_status, handle_price_change, handle_delete_order,
    handle_delete_confirm
)
from bot.doc_sender import send_doc_in_sections
from telegram import BotCommandScopeChat
from core.admin_state import is_active as admin_is_active, activate as admin_activate, deactivate as admin_deactivate
from core.menu import CLIENT_COMMANDS, ADMIN_COMMANDS

log = logging.getLogger("bot.admin")

TRAINING_FILE = Path(DATA_DIR) / "knowledge" / "training.json"
TRAINING_MEDIA_DIR = Path(DATA_DIR) / "knowledge" / "media"
TRAINING_MEDIA_DIR.mkdir(exist_ok=True, parents=True)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def load_training_data() -> List[Dict]:
    if not TRAINING_FILE.exists():
        return []
    try:
        with open(TRAINING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_training_data(data: List[Dict]) -> bool:
    try:
        TRAINING_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(TRAINING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log.error(f"Помилка збереження: {e}")
        return False


async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /admin — toggle: вхід/вихід з адмін-режиму."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    if not is_admin(user.id):
        # Не адмін — silent ignore (як для клієнта)
        return

    # TOGGLE: якщо вже активний — виходимо
    if admin_is_active(user.id):
        admin_deactivate(user.id)
        try:
            await ctx.bot.set_my_commands(
                CLIENT_COMMANDS, scope=BotCommandScopeChat(chat_id=chat_id)
            )
        except Exception as e:
            log.warning(f"set_my_commands(client) failed: {e}")
        await update.message.reply_text(
            "🔓 Ти вийшов з адмінки.\n/admin — щоб зайти знову."
        )
        return

    # АКТИВАЦІЯ
    admin_activate(user.id)
    try:
        await ctx.bot.set_my_commands(
            ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=chat_id)
        )
    except Exception as e:
        log.warning(f"set_my_commands(admin) failed: {e}")

    data = load_training_data()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Додати знання", callback_data="admin_trainer")],
        [InlineKeyboardButton("📚 База знань", callback_data="admin_knowledge")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 Замовлення", callback_data="admin_orders_menu")],
    ])
    await update.message.reply_text(
        f"🔧 Адмін панель InSilver\n\nЗаписів у базі: {len(data)}\n\n"
        f"_Повторне /admin вийде з адмін-режиму._",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def start_trainer_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Починаємо сесію додавання знань."""
    query = update.callback_query
    await query.answer()
    ctx.user_data["trainer"] = {"title": None, "content": [], "step": "title"}
    await query.edit_message_text(
        "✏️ Режим навчання\n\n"
        "Крок 1: Введіть заголовок/питання (наприклад: \'Яка ціна ланцюжка?\')\n\n"
        "або /cancel щоб скасувати"
    )


async def handle_trainer_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу в режимі тренера або для зміни ціни замовлення."""
    # Якщо адмін вводить нову ціну для замовлення
    awaiting = ctx.user_data.get("awaiting_price")
    if awaiting:
        text = update.message.text.strip().replace(",", ".")
        try:
            new_price = float(text)
        except ValueError:
            await update.message.reply_text("❌ Невірне число. Спробуйте ще: напр. `1500`")
            return
        from bot.admin_orders import load_orders, save_orders
        orders = load_orders()
        order = next((o for o in orders if o.get("id") == awaiting), None)
        if not order:
            await update.message.reply_text(f"❌ Замовлення #{awaiting} не знайдено")
            ctx.user_data.pop("awaiting_price", None)
            return
        # Оновити price_calc.total або просто custom_price
        if isinstance(order.get("price_calc"), dict):
            old = order["price_calc"].get("total", 0)
            order["price_calc"]["total"] = new_price
        else:
            old = order.get("custom_price", 0)
            order["custom_price"] = new_price
        save_orders(orders)
        ctx.user_data.pop("awaiting_price", None)
        await update.message.reply_text(
            f"✅ Ціна #{awaiting}: {old:.0f} → {new_price:.0f} грн"
        )
        return

    trainer = ctx.user_data.get("trainer")
    if not trainer:
        return

    text = update.message.text
    if text == "/cancel":
        ctx.user_data.pop("trainer", None)
        await update.message.reply_text("Скасовано.")
        return

    step = trainer.get("step")

    if step == "title":
        trainer["title"] = text
        trainer["step"] = "content"
        await update.message.reply_text(
            f"Заголовок: {text}\n\n"
            "Крок 2: Введіть відповідь/контент.\n"
            "Можна кілька повідомлень. Коли готово — /done"
        )
    elif step == "content":
        if text == "/done":
            if not trainer["content"]:
                await update.message.reply_text("Немає контенту. Введіть відповідь.")
                return
            trainer["step"] = "confirm"
            full_content = " ".join(trainer["content"])
            title_val = trainer["title"]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Зберегти", callback_data="trainer_save")],
                [InlineKeyboardButton("❌ Скасувати", callback_data="trainer_cancel")],
            ])
            await update.message.reply_text(
                f"Перевірте запис:\n\nПитання: {title_val}\n\nВідповідь: {full_content[:300]}",
                reply_markup=keyboard
            )
        else:
            trainer["content"].append(text)
            await update.message.reply_text(f"Додано. Ще текст або /done для збереження.")


async def finish_trainer_session(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Зберегти запис."""
    query = update.callback_query
    await query.answer()
    trainer = ctx.user_data.get("trainer")
    if not trainer:
        await query.edit_message_text("Помилка: сесія не знайдена.")
        return

    data = load_training_data()
    record = {
        "id": len(data) + 1,
        "title": trainer["title"],
        "content": [{"type": "text", "text": " ".join(trainer["content"])}],
        "created_at": datetime.now().isoformat(),
        "source": "admin_trainer"
    }
    data.append(record)
    if save_training_data(data):
        ctx.user_data.pop("trainer", None)
        await query.edit_message_text(f"✅ Збережено! Всього записів: {len(data)}")
    else:
        await query.edit_message_text("❌ Помилка збереження.")


async def view_knowledge(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати список записів бази знань."""
    query = update.callback_query
    await query.answer()
    data = load_training_data()
    if not data:
        await query.edit_message_text("База знань порожня.")
        return

    page = ctx.user_data.get("kb_page", 0)
    per_page = 8
    start = page * per_page
    chunk = data[start:start + per_page]

    text = f"📚 База знань ({len(data)} записів):\n\n"
    buttons = []
    for record in chunk:
        rid = record.get("id", "?")
        title = record.get("title", "без назви")[:40]
        text += f"#{rid} {title}\n"
        buttons.append([
            InlineKeyboardButton(f"👁 #{rid}", callback_data=f"kb_view_{rid}"),
            InlineKeyboardButton(f"🗑 #{rid}", callback_data=f"kb_del_{rid}"),
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data="kb_prev"))
    if start + per_page < len(data):
        nav.append(InlineKeyboardButton("▶️", callback_data="kb_next"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def delete_knowledge_record(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Видалити запис з бази знань."""
    query = update.callback_query
    data = load_training_data()
    before = len(data)
    data = [r for r in data if r.get("id") != record_id]
    if len(data) < before:
        save_training_data(data)
        await query.answer(f"Запис #{record_id} видалено")
    else:
        await query.answer("Запис не знайдено")
    # Повернутись до списку
    ctx.user_data["kb_page"] = 0
    await view_knowledge(update, ctx)


async def show_conversation_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Статистика розмов."""
    query = update.callback_query
    await query.answer()
    try:
        stats = get_stats()
        today = stats.get("today_messages", 0)
        total = stats.get("total_conversations", 0)
        users = stats.get("unique_users", 0)
        text = f"📊 Статистика\n\nПовідомлень сьогодні: {today}\nВсього розмов: {total}\nУнікальних користувачів: {users}\n" 
    except Exception:
        text = "📊 Статистика недоступна"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]])
    await query.edit_message_text(text, reply_markup=keyboard)


async def view_record(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Показати повний запис бази знань."""
    query = update.callback_query
    await query.answer()
    data = load_training_data()
    record = next((r for r in data if r.get("id") == record_id), None)
    if not record:
        await query.edit_message_text(f"❌ Запис #{record_id} не знайдено")
        return
    title = record.get("title", "без назви")
    content_list = record.get("content", [])
    answer = content_list[0].get("text", "") if content_list and isinstance(content_list, list) else ""
    text = f"📖 Запис #{record_id}\n\n"
    text += f"❓ Питання:\n{title}\n\n"
    text += f"💬 Відповідь:\n{answer}"
    if len(text) > 4000:
        text = text[:3997] + "..."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Редагувати", callback_data=f"kb_edit_{record_id}")],
        [InlineKeyboardButton("🗑 Видалити", callback_data=f"kb_del_{record_id}")],
        [InlineKeyboardButton("🔙 До списку", callback_data="admin_knowledge")],
    ])
    await query.edit_message_text(text, reply_markup=keyboard)


async def start_edit_record(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Видалити старий запис і стартувати trainer mode."""
    query = update.callback_query
    await query.answer()
    data = load_training_data()
    before = len(data)
    data = [r for r in data if r.get("id") != record_id]
    if len(data) < before:
        save_training_data(data)
    ctx.user_data["trainer"] = {"title": None, "content": [], "step": "title"}
    await query.edit_message_text(
        f"✏️ Редагування #{record_id}\n\n"
        "Старий запис видалено. Введіть новий заголовок/питання.\n\n"
        "або /cancel щоб скасувати"
    )


async def handle_trainer_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Адмін у trainer mode скинув фото — поки не підтримується."""
    await update.message.reply_text(
        "📸 Фото у режимі тренера поки не підтримується.\n"
        "Введіть текстом або /cancel щоб вийти."
    )


async def handle_admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Центральний обробник callback для адміна."""
    query = update.callback_query
    user = update.effective_user
    if not is_admin(user.id):
        await query.answer("Немає доступу")
        return

    data = query.data

    if data == "admin_trainer":
        await start_trainer_mode(update, ctx)
    elif data == "admin_knowledge":
        ctx.user_data["kb_page"] = 0
        await view_knowledge(update, ctx)
    elif data == "admin_stats":
        await show_conversation_stats(update, ctx)
    elif data == "admin_orders_menu":
        await query.answer()
        await cmd_orders(update, ctx)
    elif data == "admin_back":
        await query.answer()
        kb_data = load_training_data()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Додати знання", callback_data="admin_trainer")],
            [InlineKeyboardButton("📚 База знань", callback_data="admin_knowledge")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("📋 Замовлення", callback_data="admin_orders_menu")],
        ])
        await query.edit_message_text(
            f"🔧 Адмін панель InSilver\n\nЗаписів у базі: {len(kb_data)}",
            reply_markup=keyboard
        )
    elif data == "trainer_save":
        await finish_trainer_session(update, ctx)
    elif data == "trainer_cancel":
        ctx.user_data.pop("trainer", None)
        await query.edit_message_text("Скасовано.")
    elif data == "kb_prev":
        ctx.user_data["kb_page"] = max(0, ctx.user_data.get("kb_page", 0) - 1)
        await view_knowledge(update, ctx)
    elif data == "kb_next":
        ctx.user_data["kb_page"] = ctx.user_data.get("kb_page", 0) + 1
        await view_knowledge(update, ctx)
    elif data.startswith("kb_view_"):
        rid = int(data.split("_")[-1])
        await view_record(update, ctx, rid)
    elif data.startswith("kb_edit_"):
        rid = int(data.split("_")[-1])
        await start_edit_record(update, ctx, rid)
    elif data.startswith("kb_del_"):
        rid = int(data.split("_")[-1])
        await delete_knowledge_record(update, ctx, rid)
    else:
        # Передаємо в orders handler
        await handle_orders_callback(update, ctx)


async def cmd_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Адмін: /price — показати ціни. /price 150 — змінити дефолтну. /price <плетіння> 160 — для конкретного."""
    if not update.message:
        return  # edited_message або callback — ігноруємо
    user = update.effective_user
    if not user or not is_admin(user.id) or not admin_is_active(user.id):
        return  # silent ignore — як для клієнта
    if not user or not is_admin(user.id):
        return  # тиша для не-адмінів
    
    from core.pricing import load_pricing, save_pricing
    
    args = ctx.args or []
    pricing = load_pricing()
    
    # /price без аргументів → показати всі ціни
    if not args:
        lines = ["💰 *Поточні ціни (грн/г):*\n"]
        lines.append(f"📌 *Дефолт:* {pricing.get('default_price_per_gram', 155)}\n")
        for price_str, weavings in sorted(pricing.get("weaving_prices", {}).items(), key=lambda x: int(x[0])):
            lines.append(f"*{price_str} грн/г:* {', '.join(weavings)}")
        lines.append("\n_Команди:_")
        lines.append("`/price 150` — змінити дефолтну ціну")
        lines.append("`/price Бісмарк 170` — змінити ціну для плетіння")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return
    
    # /price 150 → змінити дефолт
    if len(args) == 1:
        try:
            new_price = float(args[0].replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Невірне число. Приклад: `/price 150`", parse_mode="Markdown")
            return
        old_price = pricing.get("default_price_per_gram", 155)
        pricing["default_price_per_gram"] = new_price
        save_pricing(pricing)
        log.info(f"Admin {user.id} змінив дефолтну ціну: {old_price} → {new_price}")
        await update.message.reply_text(
            f"✅ Дефолтна ціна змінена: *{old_price}* → *{new_price:.0f}* грн/г",
            parse_mode="Markdown"
        )
        return
    
    # /price <плетіння> 160 → змінити ціну для плетіння
    if len(args) >= 2:
        try:
            new_price = float(args[-1].replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Останній аргумент має бути числом. Приклад: `/price Бісмарк 170`", parse_mode="Markdown")
            return
        weaving_name = " ".join(args[:-1]).strip()
        weaving_lower = weaving_name.lower()
        
        # Знайти і видалити з поточної категорії
        weaving_prices = pricing.get("weaving_prices", {})
        found_in = None
        for price_str, weavings in weaving_prices.items():
            for w in weavings:
                if w.lower() == weaving_lower:
                    found_in = (price_str, w)
                    break
            if found_in:
                break
        
        if not found_in:
            available = []
            for weavings in weaving_prices.values():
                available.extend(weavings)
            await update.message.reply_text(
                f"❌ Плетіння *{weaving_name}* не знайдено.\n\n"
                f"Доступні: {', '.join(available)}",
                parse_mode="Markdown"
            )
            return
        
        old_price_str, real_name = found_in
        weaving_prices[old_price_str].remove(real_name)
        if not weaving_prices[old_price_str]:
            del weaving_prices[old_price_str]
        
        # Додати в нову категорію
        new_price_str = str(int(new_price))
        if new_price_str not in weaving_prices:
            weaving_prices[new_price_str] = []
        weaving_prices[new_price_str].append(real_name)
        
        pricing["weaving_prices"] = weaving_prices
        save_pricing(pricing)
        log.info(f"Admin {user.id} змінив ціну {real_name}: {old_price_str} → {new_price_str}")
        await update.message.reply_text(
            f"✅ *{real_name}*: {old_price_str} → *{new_price_str}* грн/г",
            parse_mode="Markdown"
        )
        return


async def cmd_trainer_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Завершення вводу контенту в режимі тренера."""
    user = update.effective_user
    if not user or not is_admin(user.id) or not admin_is_active(user.id):
        return  # silent ignore — як для клієнта
    trainer = ctx.user_data.get("trainer")
    if not trainer:
        return  # не в режимі тренера — ігноруємо
    if trainer.get("step") != "content":
        return
    if not trainer["content"]:
        await update.message.reply_text("Немає контенту. Введіть відповідь.")
        return
    trainer["step"] = "confirm"
    full_content = " ".join(trainer["content"])
    title_val = trainer["title"]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Зберегти", callback_data="trainer_save")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="trainer_cancel")],
    ])
    await update.message.reply_text(
        f"Перевірте запис:\n\nПитання: {title_val}\n\nВідповідь: {full_content[:300]}",
        reply_markup=keyboard
    )


async def cmd_admin_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Команда /admin_help — шле повний ADMIN_GUIDE.md секціями."""
    user = update.effective_user
    if not user or not is_admin(user.id) or not admin_is_active(user.id):
        return  # silent ignore — як для клієнта
    chat_id = update.effective_chat.id
    md_path = Path(__file__).parent.parent / "ADMIN_GUIDE.md"
    if not md_path.exists():
        await ctx.bot.send_message(chat_id, "❌ ADMIN_GUIDE.md не знайдено")
        return
    await ctx.bot.send_message(chat_id, "📖 Надсилаю інструкцію секціями…")
    sent = await send_doc_in_sections(ctx.bot, chat_id, md_path)
    log.info(f"/admin_help → {sent} секцій надіслано user {user.id}")


def create_admin_handlers():
    """Повертає список хендлерів для адміна."""
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("orders", cmd_orders),
        CommandHandler("price", cmd_price),
        CommandHandler("done", cmd_trainer_done),
        CommandHandler("admin_help", cmd_admin_help),
        CallbackQueryHandler(handle_admin_callback, pattern="^(admin_|trainer_|kb_)"),
        CallbackQueryHandler(handle_order_edit, pattern="^order_edit:"),
        CallbackQueryHandler(handle_status_change, pattern="^status:"),
        CallbackQueryHandler(handle_set_status, pattern="^set_status:"),
        CallbackQueryHandler(handle_delete_order, pattern="^delete:"),
        CallbackQueryHandler(handle_delete_confirm, pattern="^delete_confirm:"),
        CallbackQueryHandler(handle_search_order, pattern="^search_order:"),
        CallbackQueryHandler(handle_orders_callback, pattern="^(orders[:_]|orders_full:)"),
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_trainer_input
        ),
    ]
