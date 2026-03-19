"""Обробник замовлень — два режими:
A: кнопка під товаром → коротка форма (ім'я, телефон, місто)
B: /order або кнопка "Оформити" → повна анкета з автозаповненням
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ConversationHandler, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes
)
from core.config import OWNER_CHAT_ID
from core.order_context import extract_order_context
from core.order_config import (
    TYPE_STEP, normalize_type, get_steps_for_type,
    get_keyboard, format_step_message
)

log = logging.getLogger("bot.order")
ORDERS_FILE = Path("data/orders/orders.json")

# ─── Стани ────────────────────────────────────────────────────────────────────
# Режим A
A_NAME, A_PHONE, A_CITY, A_COMMENT = range(4)
# Режим B
B_TYPE, B_STEP, B_TEXT = range(4, 7)


# ─── Збереження ───────────────────────────────────────────────────────────────

def save_order(order: dict):
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    orders = []
    if ORDERS_FILE.exists():
        try:
            orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            orders = []
    orders.append(order)
    ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")


async def notify_owner(ctx, order: dict, user):
    """Відправляє сповіщення Владу з кнопкою написати клієнту."""
    lines = [f"🛒 *Нове замовлення #{order['id']}*\n"]
    lines.append(f"👤 {order.get('name', '—')} | @{user.username or '—'} | `{user.id}`")
    lines.append(f"📞 {order.get('phone', '—')}")
    if order.get('city'):
        lines.append(f"📍 {order['city']}")

    # Деталі виробу якщо є
    detail_keys = {
        'item_title': '🏷 Товар', 'type': 'Тип', 'weaving': 'Плетіння',
        'length': 'Довжина', 'weight': 'Маса', 'plating': 'Покриття',
        'clasp': 'Застібка', 'size': 'Розмір', 'cross_type': 'Тип хреста',
        'collection': 'Колекція', 'motif': 'Мотив', 'style': 'Стиль',
        'set_composition': 'Склад', 'note': 'Додатково',
    }
    for key, label in detail_keys.items():
        if order.get(key):
            lines.append(f"  {label}: {order[key]}")

    if order.get('comment'):
        lines.append(f"💬 {order['comment']}")

    try:
        await ctx.bot.send_message(
            OWNER_CHAT_ID,
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💬 Написати клієнту", url=f"tg://user?id={user.id}")
            ]])
        )
    except Exception as e:
        log.error(f"Не вдалось надіслати сповіщення: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# РЕЖИМ A — коротка форма (кнопка під товаром)
# ════════════════════════════════════════════════════════════════════════════════

async def mode_a_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Вхід через кнопку під товаром."""
    query = update.callback_query
    await query.answer()

    item_idx = int(query.data[len("o:"):])
    ctx.user_data["order"] = {"_mode": "A", "item_idx": item_idx, "item_title": ""}

    try:
        from core.config import SITE_CATALOG
        catalog = json.loads(Path(SITE_CATALOG).read_text(encoding="utf-8"))
        item = catalog.get("items", [])[item_idx]
        ctx.user_data["order"]["item_title"] = item.get("title", "")
    except Exception as e:
        log.warning(f"Не вдалось знайти товар: {e}")

    title = ctx.user_data["order"]["item_title"]
    await query.message.reply_text(
        f"Оформлюємо замовлення:\n*{title}*\n\nЯк вас звати?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel")
        ]])
    )
    return A_NAME


async def a_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["name"] = update.message.text.strip()
    await update.message.reply_text("Ваш номер телефону:")
    return A_PHONE


async def a_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["phone"] = update.message.text.strip()
    await update.message.reply_text("Ваше місто:")
    return A_CITY


async def a_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["city"] = update.message.text.strip()
    await update.message.reply_text(
        "Коментар? (або /skip):",
        reply_markup=ReplyKeyboardRemove()
    )
    return A_COMMENT


async def a_comment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["comment"] = update.message.text.strip()
    return await finish_order(update, ctx)


async def a_skip_comment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["comment"] = ""
    return await finish_order(update, ctx)


# ════════════════════════════════════════════════════════════════════════════════
# РЕЖИМ B — повна анкета (/order або кнопка "Оформити замовлення")
# ════════════════════════════════════════════════════════════════════════════════

async def mode_b_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Вхід через /order або кнопку Оформити."""
    # Підтримуємо і команду і callback
    if update.callback_query:
        await update.callback_query.answer()
        reply = update.callback_query.message.reply_text
    else:
        reply = update.message.reply_text

    # Витягуємо контекст з розмови
    history = ctx.user_data.get("history", [])
    prefilled = extract_order_context(history)

    ctx.user_data["order"] = {
        "_mode": "B",
        "_prefilled": prefilled,
        "_steps": [],       # заповниться після вибору типу
        "_step_idx": 0,
        "_filled": {},
    }

    # Якщо тип вже відомий з розмови — пропускаємо вибір типу
    if prefilled.get("type"):
        return await b_init_steps(update, ctx, prefilled["type"], reply)

    # Інакше питаємо тип
    from telegram import InlineKeyboardMarkup
    buttons = get_keyboard(TYPE_STEP, step_index=0)
    await reply(
        TYPE_STEP["text"],
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )
    return B_TYPE


async def b_init_steps(update, ctx, product_type: str, reply_func=None):
    """Ініціалізує кроки після визначення типу."""
    order = ctx.user_data["order"]
    prefilled = order["_prefilled"]
    order["type"] = product_type

    steps = get_steps_for_type(product_type, prefilled)
    order["_steps"] = steps
    order["_step_idx"] = 0
    order["_filled"] = {k: v for k, v in prefilled.items() if k != "type"}

    if not steps:
        return await finish_order(update, ctx)

    return await b_send_step(update, ctx, reply_func)


async def b_send_step(update, ctx, reply_func=None):
    """Відправляє поточний крок анкети."""
    order = ctx.user_data["order"]
    steps = order["_steps"]
    idx = order["_step_idx"]

    if idx >= len(steps):
        return await finish_order(update, ctx)

    step = steps[idx]
    filled = order.get("_filled", {})
    text = format_step_message(step, idx, len(steps), filled)
    buttons = get_keyboard(step, step_index=idx)

    from telegram import InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None

    if reply_func:
        await reply_func(text, reply_markup=keyboard, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

    # Якщо текстовий ввід — чекаємо на B_TEXT
    return B_TEXT if not buttons else B_STEP


async def b_handle_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання кнопки в анкеті."""
    query = update.callback_query
    await query.answer()
    data = query.data  # f:{key}:{idx} або f:back або f:cancel

    if data == "f:cancel":
        return await cancel_order(update, ctx)

    if data == "f:back":
        order = ctx.user_data["order"]
        if order["_step_idx"] > 0:
            order["_step_idx"] -= 1
            # Видаляємо останнє заповнене
            step_key = order["_steps"][order["_step_idx"]]["key"]
            order["_filled"].pop(step_key, None)
        return await b_send_step(update, ctx)

    # f:{key}:{idx}
    parts = data.split(":")
    if len(parts) == 3 and parts[0] == "f":
        step_key = parts[1]
        opt_idx = int(parts[2])

        order = ctx.user_data["order"]
        steps = order["_steps"]
        current_step = steps[order["_step_idx"]]

        # Якщо це крок вибору типу
        if step_key == "type":
            options = TYPE_STEP["options"]
            raw = options[opt_idx]
            product_type = normalize_type(raw)
            return await b_init_steps(update, ctx, product_type)

        # Звичайний крок
        options = current_step.get("options", [])
        if opt_idx < len(options):
            order["_filled"][step_key] = options[opt_idx]
            order[step_key] = options[opt_idx]

        order["_step_idx"] += 1
        return await b_send_step(update, ctx)

    return B_STEP


async def b_handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробляє текстовий ввід в анкеті."""
    order = ctx.user_data["order"]
    steps = order["_steps"]
    idx = order["_step_idx"]

    if idx >= len(steps):
        return await finish_order(update, ctx)

    step = steps[idx]
    step_key = step["key"]
    value = update.message.text.strip()

    order["_filled"][step_key] = value
    order[step_key] = value
    order["_step_idx"] += 1

    return await b_send_step(update, ctx)


# ════════════════════════════════════════════════════════════════════════════════
# ФІНАЛ — спільний для обох режимів
# ════════════════════════════════════════════════════════════════════════════════

async def finish_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order = ctx.user_data.get("order", {})
    user = update.effective_user

    order["id"] = str(uuid.uuid4())[:8].upper()
    order["tg_id"] = user.id
    order["tg_username"] = user.username or ""
    order["tg_name"] = user.first_name or ""
    order["delivery"] = "Нова Пошта"
    order["created_at"] = datetime.now().isoformat()

    # Очищаємо службові ключі
    for k in ["_mode", "_prefilled", "_steps", "_step_idx", "_filled"]:
        order.pop(k, None)

    save_order(order)
    log.info(f"Замовлення #{order['id']} від {user.id}")

    # Витягуємо контакт з поля contact якщо є (режим B)
    if order.get("contact") and not order.get("name"):
        order["name"] = order["contact"]

    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        f"✅ Замовлення *#{order['id']}* прийнято!\n\n"
        f"Влад зв'яжеться з вами найближчим часом 🥈",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    await notify_owner(ctx, order, user)
    ctx.user_data.pop("order", None)
    return ConversationHandler.END


async def cancel_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("order", None)
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "Замовлення скасовано. Якщо передумаєте — просто напишіть! 😊",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════════
# ЗБІРКА
# ════════════════════════════════════════════════════════════════════════════════

def build_order_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(mode_a_start, pattern=r"^o:\d+$"),
            CallbackQueryHandler(mode_b_start, pattern=r"^order_full$"),
            CommandHandler("order", mode_b_start),
        ],
        states={
            # Режим A
            A_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, a_name)],
            A_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, a_phone)],
            A_CITY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, a_city)],
            A_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, a_comment),
                CommandHandler("skip", a_skip_comment),
            ],
            # Режим B
            B_TYPE: [CallbackQueryHandler(b_handle_button, pattern=r"^f:")],
            B_STEP: [
                CallbackQueryHandler(b_handle_button, pattern=r"^f:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, b_handle_text),
            ],
            B_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, b_handle_text),
                CallbackQueryHandler(b_handle_button, pattern=r"^f:"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_order, pattern=r"^f:cancel$"),
            CommandHandler("cancel", cancel_order),
        ],
        per_user=True,
        per_chat=True,
    )
