"""Адмін панель — спрощена версія."""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from core.config import ADMIN_IDS, DATA_DIR
from core.conversation_logger import get_conversation_stats as get_stats
from bot.admin_orders import (
    cmd_orders, handle_orders_callback, handle_order_edit, handle_search_order,
    handle_status_change, handle_set_status, handle_price_change, handle_delete_order,
    handle_no_contact
)

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
    """Команда /admin — головне меню."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Немає доступу.")
        return

    data = load_training_data()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Додати знання", callback_data="admin_trainer")],
        [InlineKeyboardButton("📚 База знань", callback_data="admin_knowledge")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 Замовлення", callback_data="admin_orders_menu")],
    ])
    await update.message.reply_text(
        f"🔧 Адмін панель InSilver\n\nЗаписів у базі: {len(data)}",
        reply_markup=keyboard
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
    """Обробка вводу в режимі тренера."""
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
        buttons.append([InlineKeyboardButton(f"🗑 #{rid}", callback_data=f"kb_del_{rid}")])

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
    elif data.startswith("kb_del_"):
        rid = int(data.split("_")[-1])
        await delete_knowledge_record(update, ctx, rid)
    else:
        # Передаємо в orders handler
        await handle_orders_callback(update, ctx)


def create_admin_handlers():
    """Повертає список хендлерів для адміна."""
    return [
        CallbackQueryHandler(handle_admin_callback, pattern="^(admin_|trainer_|kb_)"),
        CallbackQueryHandler(handle_orders_callback, pattern="^(orders_|order_|set_status_|search_order|edit_order|delete_order|no_contact)"),
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_trainer_input
        ),
    ]
