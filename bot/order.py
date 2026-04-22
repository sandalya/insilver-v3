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
from core.pricing import get_locks, calculate_price, format_price, get_price_per_gram
from core.order_config import (
    TYPE_STEP, normalize_type, get_steps_for_type,
    get_keyboard, format_step_message
)

log = logging.getLogger("bot.order")
ORDERS_FILE = Path("data/orders/orders.json")

# ─── Стани ────────────────────────────────────────────────────────────────────
# Режим A
A_NAME, A_PHONE, A_CITY, A_COMMENT = range(4)
# Режим B — нові кроки воронки
B_TYPE, B_STEP, B_CONFIRM = range(4, 7)
# Нова лінійна воронка
B_PRODUCT_TYPE, B_WEAVING, B_LENGTH, B_WEIGHT, B_COATING, B_LOCK, B_NAME, B_PHONE, B_CITY, B_SUMMARY = range(6, 16)


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
# РЕЖИМ B — повна анкета
# Ключова зміна: використовуємо ОДИН стан B_STEP який приймає і кнопки і текст.
# b_send_step завжди повертає B_STEP — ніякого B_TEXT більше нема.
# ════════════════════════════════════════════════════════════════════════════════

async def mode_b_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        reply = update.callback_query.message.reply_text
    else:
        reply = update.message.reply_text

    history = ctx.user_data.get("history", [])
    prefilled = extract_order_context(history)

    ctx.user_data["order"] = {
        "_mode": "B",
        "_prefilled": prefilled,
        "_steps": [],
        "_step_idx": 0,
        "_filled": {},
    }

    if prefilled.get("type"):
        return await b_init_steps(update, ctx, prefilled["type"], reply)

    buttons = get_keyboard(TYPE_STEP, step_index=0)
    await reply(
        TYPE_STEP["text"],
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )
    return B_TYPE


async def b_init_steps(update, ctx, product_type: str, reply_func=None):
    order = ctx.user_data["order"]
    prefilled = order["_prefilled"]
    order["type"] = product_type

    steps = get_steps_for_type(product_type, prefilled)
    order["_steps"] = steps
    order["_step_idx"] = 0
    order["_filled"] = {k: v for k, v in prefilled.items() if k != "type"}

    if not steps:
        return await finish_order(update, ctx)

    result = await b_send_step(update, ctx, reply_func)
    if result == -1:
        return result
    return B_STEP


async def b_send_step(update, ctx, reply_func=None):
    """Відправляє поточний крок. Завжди повертає B_STEP."""
    order = ctx.user_data["order"]
    steps = order["_steps"]
    idx = order["_step_idx"]

    if idx >= len(steps):
        result = await finish_order(update, ctx)
        return result

    step = steps[idx]
    filled = order.get("_filled", {})
    text = format_step_message(step, idx, len(steps), filled)
    buttons = get_keyboard(step, step_index=idx)
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None

    # Якщо крок текстовий — додаємо кнопки навігації окремо
    if not buttons:
        nav_row = []
        if idx > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data="f:back"))
        nav_row.append(InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel"))
        keyboard = InlineKeyboardMarkup([nav_row])

    if reply_func:
        await reply_func(text, reply_markup=keyboard, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

    return B_STEP


async def b_handle_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data not in ("f:cancel", "f:back") and "order" not in ctx.user_data:
        return ConversationHandler.END

    if data == "f:cancel":
        return await cancel_order(update, ctx)

    if data == "f:back":
        order = ctx.user_data["order"]
        if order["_step_idx"] > 0:
            order["_step_idx"] -= 1
            step_key = order["_steps"][order["_step_idx"]]["key"]
            order["_filled"].pop(step_key, None)
            order.pop(step_key, None)
        else:
            # На першому кроці "Назад" = скасування
            return await cancel_order(update, ctx)
        await b_send_step(update, ctx)
        return B_STEP

    parts = data.split(":")
    if len(parts) == 3 and parts[0] == "f":
        step_key = parts[1]
        opt_idx = int(parts[2])

        order = ctx.user_data["order"]
        steps = order["_steps"]

        if step_key == "type":
            options = TYPE_STEP["options"]
            raw = options[opt_idx]
            product_type = normalize_type(raw)
            return await b_init_steps(update, ctx, product_type)

        current_step = steps[order["_step_idx"]]
        options = current_step.get("options", [])
        if opt_idx < len(options):
            chosen = options[opt_idx]

            # "Інше" — просимо текстовий ввід
            if chosen in ("✏️ Інше", "Інше"):
                order["_waiting_custom"] = step_key
                await update.callback_query.message.reply_text(
                    "Введіть свій варіант:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel")
                    ]])
                )
                return B_STEP

            # "Є коментар" — просимо текст коментаря
            if step_key == "comment" and chosen == "✍️ Є коментар":
                order["_waiting_custom"] = "comment"
                await update.callback_query.message.reply_text(
                    "Напишіть ваш коментар:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel")
                    ]])
                )
                return B_STEP

            order["_filled"][step_key] = chosen
            order[step_key] = chosen

        order["_step_idx"] += 1
        result = await b_send_step(update, ctx)
        if result == -1:
            return result
        return B_STEP

    return B_STEP


async def b_handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "order" not in ctx.user_data:
        return ConversationHandler.END
    order = ctx.user_data["order"]
    value = update.message.text.strip()

    # Чекаємо кастомний ввід після "Інше" або "Є коментар"
    if order.get("_waiting_custom"):
        step_key = order.pop("_waiting_custom")
        order["_filled"][step_key] = value
        order[step_key] = value
        order["_step_idx"] += 1
        result = await b_send_step(update, ctx)
        if result == -1:
            return result
        return B_STEP

    steps = order["_steps"]
    idx = order["_step_idx"]

    if idx >= len(steps):
        result = await finish_order(update, ctx)
        return result

    step = steps[idx]
    step_key = step["key"]

    order["_filled"][step_key] = value
    order[step_key] = value
    order["_step_idx"] += 1

    result = await b_send_step(update, ctx)
    if result == -1:
        return result
    return B_STEP


# ════════════════════════════════════════════════════════════════════════════════
# ФІНАЛ
# ════════════════════════════════════════════════════════════════════════════════

async def finish_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показує summary замовлення з ціною і кнопками Підтвердити/Скасувати.
    Повертає B_CONFIRM щоб далі обробити вибір в b_handle_confirm."""
    from core.pricing import calculate_price, format_price
    order = ctx.user_data.get("order", {})
    product_type = (order.get("type") or "").lower()
    lines = ["📋 *Перевірте замовлення:*\n"]
    field_labels = {
        "weaving": "Плетіння", "length": "Довжина", "weight": "Маса",
        "coating": "Покриття", "lock": "Застібка", "extra": "Додатково",
        "cross_type": "Тип хреста", "collection": "Колекція", "motif": "Мотив",
        "size": "Розмір", "style": "Стиль", "composition": "Склад",
        "contact": "Контакт", "comment": "Коментар",
    }
    lines.append(f"  • Тип: {product_type}")
    for key, label in field_labels.items():
        val = order.get(key)
        if val:
            lines.append(f"  • {label}: {val}")
    price_types = {"ланцюжок", "браслет", "хрестик", "кулон", "печатка"}
    weight_raw = order.get("weight", "")
    try:
        weight = float(str(weight_raw).replace(",", ".").replace("г", "").strip())
    except (ValueError, AttributeError):
        weight = 0.0
    if product_type in price_types and weight > 0:
        weaving = order.get("weaving", "")
        if product_type in {"хрестик", "кулон", "печатка"}:
            weaving = product_type.capitalize()
        lock_name = order.get("lock", "") or ""
        lock_clean = "".join(c for c in lock_name if c.isalpha() or c.isspace()).strip()
        calc = calculate_price(weight, lock_clean, weaving)
        lines.append("")
        lines.append(format_price(calc))
        lines.append("\n_Ціна орієнтовна, остаточну уточнить майстер._")
    else:
        lines.append("")
        lines.append("💰 Орієнтовну вартість уточнить майстер.")
    text = "\n".join(lines)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Підтвердити", callback_data="f:confirm"),
        InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel"),
    ]])
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    return B_CONFIRM


async def _save_and_notify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order = ctx.user_data.get("order", {})
    user = update.effective_user
    order["id"] = str(uuid.uuid4())[:8].upper()
    order["tg_id"] = user.id
    order["tg_username"] = user.username or ""
    order["tg_name"] = user.first_name or ""
    order["delivery"] = "Нова Пошта"
    order["created_at"] = datetime.now().isoformat()
    for k in ["_mode", "_prefilled", "_steps", "_step_idx", "_filled", "_waiting_custom"]:
        order.pop(k, None)
    if order.get("contact") and not order.get("name"):
        order["name"] = order["contact"]
    save_order(order)
    log.info(f"Замовлення #{order['id']} від {user.id}")
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


async def b_handle_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "f:confirm":
        return await _save_and_notify(update, ctx)
    if data == "f:cancel":
        return await cancel_order(update, ctx)
    return B_CONFIRM


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


HOW_TO_MEASURE = """📏 Як виміряти:

Для браслета:
1. Візьміть м'яку мірну стрічку або нитку
2. Обмотайте зап'ястя в найширшому місці
3. Заміряйте і додайте 1-2 см для комфорту

Для ланцюжка: виміряйте шию і додайте бажану довжину звисання.

Стандартні розміри:
- Браслет: 18-22 см
- Ланцюг жіночий: 45-50 см
- Ланцюг чоловічий: 50-60 см"""


def generate_order_id() -> str:
    from datetime import datetime
    return f"#{datetime.now().strftime('%Y%m%d-%H%M')}"


async def new_b_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        send = update.callback_query.message.reply_text
    else:
        send = update.message.reply_text
    ctx.user_data["order"] = {"_mode": "B_NEW"}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⛓ Ланцюжок", callback_data="nb:type:ланцюжок"),
         InlineKeyboardButton("📿 Браслет", callback_data="nb:type:браслет")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")]
    ])
    await send("Що виготовляємо? 😊", reply_markup=keyboard)
    return B_PRODUCT_TYPE


async def nb_product_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "nb:cancel":
        return await nb_cancel(update, ctx)
    product_type = data.split(":", 2)[2]
    ctx.user_data["order"]["product_type"] = product_type
    await query.message.reply_text(
        f"Чудово! Яке плетіння?\n\n"
        f"Наприклад: Бісмарк, Рамзес, Тризуб, Пітон, Фараон...\n"
        f"Напишіть назву плетіння:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")
        ]])
    )
    return B_WEAVING


async def nb_weaving(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    weaving = update.message.text.strip()
    ctx.user_data["order"]["weaving"] = weaving
    ppg = get_price_per_gram(weaving)
    await update.message.reply_text(
        f"Плетіння: *{weaving}* ({ppg:.0f} грн/г)\n\n"
        f"Яка довжина в сантиметрах?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📏 Як виміряти?", callback_data="nb:measure")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")]
        ])
    )
    return B_LENGTH


async def nb_length_measure(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "nb:cancel":
        return await nb_cancel(update, ctx)
    await query.message.reply_text(HOW_TO_MEASURE)
    await query.message.reply_text(
        "Введіть довжину в сантиметрах:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")
        ]])
    )
    return B_LENGTH


async def nb_length(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".")
    try:
        length = float(text)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть число. Наприклад: 21")
        return B_LENGTH
    ctx.user_data["order"]["length"] = length
    await update.message.reply_text(
        f"Довжина: *{length:.0f} см*\n\nЯка очікувана маса в грамах?\n"
        f"(Якщо не знаєте — майстер уточнить після уточнення всіх деталей)",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")
        ]])
    )
    return B_WEIGHT


async def nb_weight(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".")
    try:
        weight = float(text)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть число. Наприклад: 20")
        return B_WEIGHT
    ctx.user_data["order"]["weight"] = weight
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬜ Біле срібло", callback_data="nb:coating:біле срібло"),
         InlineKeyboardButton("⬛ Чорніння", callback_data="nb:coating:чорніння")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")]
    ])
    await update.message.reply_text("Яке покриття?", reply_markup=keyboard)
    return B_COATING


async def nb_coating(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "nb:cancel":
        return await nb_cancel(update, ctx)
    coating = query.data.split(":", 2)[2]
    ctx.user_data["order"]["coating"] = coating
    locks = get_locks()
    buttons = []
    row = []
    for lock in locks:
        price_text = f" (+{lock['price']} грн)" if lock.get("price", 0) > 0 else " (включено)"
        row.append(InlineKeyboardButton(
            f"{lock['name']}{price_text}",
            callback_data=f"nb:lock:{lock['name']}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")])
    await query.message.reply_text("Який замок?", reply_markup=InlineKeyboardMarkup(buttons))
    return B_LOCK


async def nb_lock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "nb:cancel":
        return await nb_cancel(update, ctx)
    lock_name = query.data.split(":", 2)[2]
    order = ctx.user_data["order"]
    order["lock"] = lock_name
    calc = calculate_price(
        weight=order.get("weight", 0),
        lock_name=lock_name,
        weaving=order.get("weaving", "")
    )
    order["price_calc"] = calc
    price_text = format_price(calc)
    await query.message.reply_text(
        f"Замок: *{lock_name}*\n\n{price_text}\n\nЯк вас звати?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")
        ]])
    )
    return B_NAME


async def nb_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Ваш номер телефону:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")
        ]])
    )
    return B_PHONE


async def nb_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["phone"] = update.message.text.strip()
    await update.message.reply_text(
        "Ваше місто (для відправки Новою Поштою):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")
        ]])
    )
    return B_CITY


async def nb_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["city"] = update.message.text.strip()
    return await nb_show_summary(update, ctx)


async def nb_show_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order = ctx.user_data["order"]
    calc = order.get("price_calc", {})
    price_text = format_price(calc) if calc else "⚠️ Ціну уточнить майстер"
    product = order.get("product_type", "").capitalize()
    weaving = order.get("weaving", "")
    length = order.get("length", "")
    weight = order.get("weight", "")
    coating = order.get("coating", "")
    lock = order.get("lock", "")
    name = order.get("name", "")
    phone = order.get("phone", "")
    city = order.get("city", "")
    coating_icon = "⬛" if "чорн" in coating.lower() else "⬜"
    summary = (
        f"📋 *Ваше замовлення:*\n\n"
        f"📿 {product}, плетіння {weaving}\n"
        f"📏 {length:.0f} см, {weight:.0f} г\n"
        f"{coating_icon} {coating.capitalize()}\n"
        f"🔒 {lock}\n\n"
        f"{price_text}\n\n"
        f"👤 {name}\n"
        f"📱 {phone}\n"
        f"📦 {city}\n\n"
        f"Все вірно?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="nb:confirm"),
         InlineKeyboardButton("❌ Скасувати", callback_data="nb:cancel")]
    ])
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(summary, parse_mode="Markdown", reply_markup=keyboard)
    return B_SUMMARY


async def nb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "nb:cancel":
        return await nb_cancel(update, ctx)
    order = ctx.user_data["order"]
    user = update.effective_user
    order_id = generate_order_id()
    order["id"] = order_id
    order["tg_id"] = user.id
    order["tg_username"] = user.username or ""
    order["tg_name"] = user.first_name or ""
    order["delivery"] = "Нова Пошта"
    from datetime import datetime
    order["created_at"] = datetime.now().isoformat()
    for k in ["_mode", "price_calc"]:
        order.pop(k, None)
    save_order(order)
    log.info(f"Замовлення {order_id} від {user.id}")
    await query.message.reply_text(
        f"✅ Замовлення *{order_id}* прийнято!\n\n"
        f"Влад зв'яжеться з вами найближчим часом 🥈",
        parse_mode="Markdown"
    )
    calc = order.get("price_calc") or {}
    product = order.get("product_type", "").capitalize()
    weaving = order.get("weaving", "")
    length = order.get("length", "")
    weight = order.get("weight", "")
    coating = order.get("coating", "")
    lock = order.get("lock", "")
    price_line = f"💰 {calc.get('total', 0):.0f} грн (срібло {calc.get('silver_cost', 0):.0f} + замок {calc.get('lock_cost', 0):.0f})" if calc else "💰 ціну уточнить майстер"
    admin_text = (
        f"📦 *НОВЕ ЗАМОВЛЕННЯ {order_id}*\n\n"
        f"👤 {order.get('name', '—')} (@{user.username or '—'})\n"
        f"📱 {order.get('phone', '—')}\n"
        f"📦 {order.get('city', '—')}\n\n"
        f"📿 {product} — {weaving}\n"
        f"📏 {length} см, {weight} г\n"
        f"{'⬛' if 'чорн' in str(coating).lower() else '⬜'} {coating}\n"
        f"🔒 {lock}\n\n"
        f"{price_line}"
    )
    try:
        await ctx.bot.send_message(
            OWNER_CHAT_ID,
            admin_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💬 Написати клієнту", url=f"tg://user?id={user.id}")
            ]])
        )
    except Exception as e:
        log.error(f"Не вдалось надіслати адміну: {e}")
    ctx.user_data.pop("order", None)
    return ConversationHandler.END


async def nb_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("order", None)
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text("Замовлення скасовано. Якщо передумаєте — просто напишіть! 😊")
    return ConversationHandler.END


def build_new_order_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(new_b_start, pattern=r"^order_full$"),
            CommandHandler("order", new_b_start),
        ],
        states={
            B_PRODUCT_TYPE: [CallbackQueryHandler(nb_product_type, pattern=r"^nb:")],
            B_WEAVING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nb_weaving),
                CallbackQueryHandler(nb_cancel, pattern=r"^nb:cancel$"),
            ],
            B_LENGTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nb_length),
                CallbackQueryHandler(nb_length_measure, pattern=r"^nb:(measure|cancel)$"),
            ],
            B_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nb_weight),
                CallbackQueryHandler(nb_cancel, pattern=r"^nb:cancel$"),
            ],
            B_COATING: [CallbackQueryHandler(nb_coating, pattern=r"^nb:(coating:|cancel)")],
            B_LOCK: [CallbackQueryHandler(nb_lock, pattern=r"^nb:(lock:|cancel)")],
            B_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nb_name),
                CallbackQueryHandler(nb_cancel, pattern=r"^nb:cancel$"),
            ],
            B_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nb_phone),
                CallbackQueryHandler(nb_cancel, pattern=r"^nb:cancel$"),
            ],
            B_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nb_city),
                CallbackQueryHandler(nb_cancel, pattern=r"^nb:cancel$"),
            ],
            B_SUMMARY: [CallbackQueryHandler(nb_confirm, pattern=r"^nb:(confirm|cancel)$")],
        },
        fallbacks=[
            CallbackQueryHandler(nb_cancel, pattern=r"^nb:cancel$"),
            CommandHandler("cancel", nb_cancel),
        ],
        per_user=True,
        per_chat=True,
    )


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
            # Режим B — один стан для всього
            B_TYPE: [CallbackQueryHandler(b_handle_button, pattern=r"^f:")],
            B_STEP: [
                CallbackQueryHandler(b_handle_button, pattern=r"^f:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, b_handle_text),
            ],
            B_CONFIRM: [
                CallbackQueryHandler(b_handle_confirm, pattern=r"^f:(confirm|cancel)$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_order, pattern=r"^f:cancel$"),
            CommandHandler("cancel", cancel_order),
        ],
        per_user=True,
        per_chat=True,
    )
