"""Admin функціонал управління замовленнями"""
import json
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.config import ORDERS_FILE

log = logging.getLogger("admin_orders")

def load_orders():
    """Завантажити всі замовлення"""
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_orders(orders):
    """Зберегти замовлення"""
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

async def cmd_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати всі замовлення. Підтримує виклик з /orders і з callback."""
    if update.callback_query:
        send = update.callback_query.message.reply_text
    elif update.message:
        send = update.message.reply_text
    else:
        return
    orders = load_orders()
    if not orders:
        await send("📭 Немає замовлень")
        return
    
    # Групуємо по статусам
    stats = {}
    for order in orders:
        status = order.get('status', 'unknown')
        if status not in stats:
            stats[status] = 0
        stats[status] += 1
    
    # Показуємо статистику
    text = "📊 ЗАМОВЛЕННЯ\n\n"
    for status, count in stats.items():
        emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(status, "❓")
        text += f"{emoji} {status}: {count}\n"
    
    text += f"\n📈 Всього: {len(orders)}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Нові", callback_data="orders:new")],
        [InlineKeyboardButton("⚙️ В роботі", callback_data="orders:processing")],
        [InlineKeyboardButton("✅ Готові", callback_data="orders:ready")],
        [InlineKeyboardButton("📋 Всі", callback_data="orders:all")],
    ])
    
    await send(text, reply_markup=keyboard)

async def handle_orders_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробка callback для замовлень"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    if len(data) != 2:
        return
        
    action = data[1]
    
    # Обробка "Показати всі"  
    if query.data.startswith("orders_full:"):
        return await handle_orders_full(update, ctx)
    
    # Обробка "Пошук по ID"
    if query.data.startswith("search_order:"):
        return await handle_search_order(update, ctx)
        
    # Обробка "Назад до головної"
    if action == "back":
        return await cmd_orders(update, ctx)
    orders = load_orders()
    
    if action == "all":
        filtered_orders = orders
        title = "📋 Всі замовлення"
    else:
        filtered_orders = [o for o in orders if o.get('status') == action]
        emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(action, "❓")
        title = f"{emoji} Замовлення: {action}"
    
    if not filtered_orders:
        await query.edit_message_text(f"{title}\n\n📭 Немає замовлень")
        return
    
    # Показуємо перші 10 замовлень
    text = f"{title}\n\n"
    for i, order in enumerate(filtered_orders[:10]):
        client_name = order.get('name', order.get('contact', 'Аноним'))
        
        # Обробляємо різні варіанти назв полів продукту
        product_type = (order.get('product_type') or 
                       order.get('item_type') or 
                       order.get('type', '?'))
        
        product_style = (order.get('style') or 
                        order.get('plating') or 
                        order.get('weaving') or '')
        
        weight = order.get('weight', '')
        if weight:
            product = f"{product_type} {product_style} ({weight})"
        else:
            product = f"{product_type} {product_style}"
        
        created = order.get('created', '?')
        status = order.get('status', 'new')
        status_emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(status, "❓")
        
        text += f"**#{order.get('id', '?')}** {client_name}\n"
        text += f"🎨 {product.strip()}\n"
        text += f"{status_emoji} {status} | 📅 {created}\n\n"
    
    if len(filtered_orders) > 10:
        text += f"... і ще {len(filtered_orders) - 10} замовлень\n"
        text += f"**Всього:** {len(filtered_orders)}"
    
    # Кнопки для дій - ВСІХ видимих замовлень (до 8 кнопок макс)
    keyboard = []
    
    # Додаємо кнопки для редагування всіх видимих замовлень (але не більше 8)
    visible_orders = filtered_orders[:8]  # Telegram ліміт ~8 кнопок
    
    # Групуємо по 2 кнопки в рядок для економії місця
    for i in range(0, len(visible_orders), 2):
        row = []
        for j in range(2):
            if i + j < len(visible_orders):
                order = visible_orders[i + j]
                row.append(InlineKeyboardButton(
                    f"✏️ #{order.get('id', '?')}", 
                    callback_data=f"order_edit:{order.get('id', '')}"
                ))
        keyboard.append(row)
    
    # Якщо є ще замовлення які не поміщаються в кнопки
    if len(filtered_orders) > 8:
        keyboard.append([InlineKeyboardButton(
            f"🔍 Пошук по ID (ще {len(filtered_orders) - 8})", 
            callback_data=f"search_order:{action}"
        )])
    
    # Навігаційні кнопки
    nav_row = []
    if len(filtered_orders) > 10:
        nav_row.append(InlineKeyboardButton("📋 Показати всі", callback_data=f"orders_full:{action}"))
    
    nav_row.extend([
        InlineKeyboardButton("🔄 Оновити", callback_data=f"orders:{action}"),
        InlineKeyboardButton("🔙 Назад", callback_data="orders:back")
    ])
    keyboard.append(nav_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_order_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Редагування конкретного замовлення"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split(":", 1)[1]
    orders = load_orders()
    
    order = next((o for o in orders if o.get('id') == order_id), None)
    if not order:
        await query.edit_message_text(f"❌ Замовлення #{order_id} не знайдено")
        return
    
    # Показуємо деталі замовлення
    text = f"📋 **ЗАМОВЛЕННЯ #{order_id}**\n\n"
    
    client_name = order.get('name', order.get('contact', 'Аноним'))
    text += f"👤 **Клієнт:** {client_name}\n"
    
    if order.get('phone'):
        text += f"📞 **Телефон:** {order['phone']}\n"
    
    if order.get('city'):
        text += f"🏙️ **Місто:** {order['city']}\n"
        
    product = f"{order.get('product_type', '?')} {order.get('style', '')}"
    text += f"🎨 **Виріб:** {product}\n"
    
    if order.get('size'):
        text += f"📏 **Розмір:** {order['size']}\n"
    
    if order.get('weight'):
        text += f"⚖️ **Вага:** {order['weight']}\n"
        
    if order.get('price'):
        text += f"💰 **Ціна:** {order['price']}\n"
    
    status = order.get('status', 'unknown')
    emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(status, "❓")
    text += f"📊 **Статус:** {emoji} {status}\n"
    
    text += f"📅 **Створено:** {order.get('created', '?')}\n"
    
    if order.get('comment'):
        text += f"💬 **Коментар:** {order['comment']}\n"
    
    # Кнопки дій
    keyboard = [
        [InlineKeyboardButton("📊 Змінити статус", callback_data=f"status:{order_id}")],
    ]
    
    # Кнопка "Написати клієнту" тільки якщо є tg_id; інакше нічого не показуємо
    client_id = order.get('tg_id') or order.get('client_chat_id')
    if client_id and str(client_id).strip():
        keyboard.append([InlineKeyboardButton("💬 Написати клієнту", url=f"tg://user?id={client_id}")])
    
    keyboard.extend([
        [InlineKeyboardButton("🗑️ Видалити", callback_data=f"delete:{order_id}")],
        [InlineKeyboardButton("🔙 До списку", callback_data="orders:all")],
    ])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_search_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Пошук замовлення по ID"""
    query = update.callback_query
    
    # Показуємо список всіх ID для вибору
    orders = load_orders()
    
    if not orders:
        await query.edit_message_text("📭 Немає замовлень")
        return
    
    # Групуємо замовлення по статусам для зручності
    by_status = {}
    for order in orders:
        status = order.get('status', 'new')
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(order)
    
    text = "🔍 **ПОШУК ЗАМОВЛЕННЯ**\n\nВиберіть замовлення для редагування:\n\n"
    
    # Показуємо по статусам
    for status, orders_list in by_status.items():
        emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(status, "❓")
        text += f"**{emoji} {status.upper()}:**\n"
        for order in orders_list[:10]:  # Обмежуємо кількість для читабельності
            client = order.get('name', order.get('contact', 'Аноним'))[:15]
            text += f"• #{order.get('id', '?')} - {client}\n"
        if len(orders_list) > 10:
            text += f"  ... і ще {len(orders_list) - 10}\n"
        text += "\n"
    
    # Кнопки для швидкого доступу (останні 20 замовлень)
    keyboard = []
    recent_orders = orders[-20:]  # Останні 20 замовлень
    
    # По 4 кнопки в рядок
    for i in range(0, len(recent_orders), 4):
        row = []
        for j in range(4):
            if i + j < len(recent_orders):
                order = recent_orders[i + j]
                row.append(InlineKeyboardButton(
                    f"#{order.get('id', '?')}", 
                    callback_data=f"order_edit:{order.get('id', '')}"
                ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="orders:all")])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_orders_full(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати ВСІ замовлення без ліміту"""
    query = update.callback_query
    data_parts = query.data.split(":")
    status_filter = data_parts[1] if len(data_parts) > 1 else "all"
    
    orders = load_orders()
    
    if status_filter == "all":
        filtered_orders = orders
        title = "📋 ВСІ замовлення"
    else:
        filtered_orders = [o for o in orders if o.get('status') == status_filter]
        emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(status_filter, "❓")
        title = f"{emoji} ВСІ замовлення: {status_filter}"
    
    if not filtered_orders:
        await query.edit_message_text(f"{title}\n\n📭 Немає замовлень")
        return
    
    # Формуємо повний список (до 25 замовлень)
    text = f"{title}\n\n"
    for order in filtered_orders[:25]:
        client_name = order.get('name', order.get('contact', 'Аноним'))
        
        product_type = (order.get('product_type') or 
                       order.get('item_type') or 
                       order.get('type', '?'))
        
        product_style = (order.get('style') or 
                        order.get('plating') or 
                        order.get('weaving') or '')
        
        weight = order.get('weight', '')
        price = order.get('price', '')
        
        product = f"{product_type} {product_style}"
        if weight:
            product += f" ({weight})"
        if price:
            product += f" - {price}"
            
        status = order.get('status', 'new')
        status_emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(status, "❓")
        
        created = order.get('created', '?')
        
        text += f"#{order.get('id', '?')} | {client_name}\n"
        text += f"  {product.strip()}\n"
        text += f"  {status_emoji} {status} | {created}\n\n"
    
    if len(filtered_orders) > 25:
        text += f"... і ще {len(filtered_orders) - 25} замовлень\n"
    
    text += f"📊 **Всього:** {len(filtered_orders)}"
    
    # Додаємо кнопки для редагування (до 15 кнопок по 3 в рядок)
    keyboard = []
    visible_orders = filtered_orders[:15]  # Для повного списку показуємо більше кнопок
    
    # Групуємо по 3 кнопки в рядок
    for i in range(0, len(visible_orders), 3):
        row = []
        for j in range(3):
            if i + j < len(visible_orders):
                order = visible_orders[i + j]
                row.append(InlineKeyboardButton(
                    f"#{order.get('id', '?')}", 
                    callback_data=f"order_edit:{order.get('id', '')}"
                ))
        keyboard.append(row)
    
    # Якщо замовлень більше 15
    if len(filtered_orders) > 15:
        keyboard.append([InlineKeyboardButton(
            f"🔍 Пошук по ID (ще {len(filtered_orders) - 15})", 
            callback_data=f"search_order:{status_filter}"
        )])
    
    # Навігація
    keyboard.append([InlineKeyboardButton("🔙 Назад до статистики", callback_data="orders:back")])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_status_change(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Зміна статусу замовлення"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split(":", 1)[1]
    orders = load_orders()
    
    order = next((o for o in orders if o.get('id') == order_id), None)
    if not order:
        await query.edit_message_text(f"❌ Замовлення #{order_id} не знайдено")
        return
    
    current_status = order.get('status', 'new')
    
    text = f"📊 **СТАТУС ЗАМОВЛЕННЯ #{order_id}**\n\n"
    text += f"Поточний статус: **{current_status}**\n\n"
    text += "Виберіть новий статус:"
    
    keyboard = [
        [InlineKeyboardButton("🆕 Нове", callback_data=f"set_status:{order_id}:new")],
        [InlineKeyboardButton("⚙️ В роботі", callback_data=f"set_status:{order_id}:processing")],
        [InlineKeyboardButton("✅ Готове", callback_data=f"set_status:{order_id}:ready")],
        [InlineKeyboardButton("🏁 Завершено", callback_data=f"set_status:{order_id}:completed")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"order_edit:{order_id}")],
    ]
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_set_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Встановити новий статус"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split(":")
    order_id = parts[1]
    new_status = parts[2]
    
    orders = load_orders()
    order = next((o for o in orders if o.get('id') == order_id), None)
    
    if not order:
        await query.edit_message_text(f"❌ Замовлення #{order_id} не знайдено")
        return
    
    old_status = order.get('status', 'new')
    order['status'] = new_status
    order['status_updated'] = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    save_orders(orders)
    
    status_emoji = {"new": "🆕", "processing": "⚙️", "ready": "✅", "completed": "🏁"}.get(new_status, "❓")
    
    await query.edit_message_text(
        f"✅ **СТАТУС ОНОВЛЕНО**\n\n"
        f"Замовлення #{order_id}\n"
        f"Статус: {old_status} → **{status_emoji} {new_status}**\n\n"
        f"Оновлено: {order['status_updated']}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Переглянути замовлення", callback_data=f"order_edit:{order_id}")],
            [InlineKeyboardButton("🔙 До списку", callback_data="orders:all")],
        ])
    )

async def handle_price_change(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Зміна ціни замовлення — питає нову ціну текстом."""
    query = update.callback_query
    await query.answer()
    order_id = query.data.split(":", 1)[1]
    orders = load_orders()
    order = next((o for o in orders if o.get("id") == order_id), None)
    if not order:
        await query.edit_message_text(f"❌ Замовлення #{order_id} не знайдено")
        return
    ctx.user_data["awaiting_price"] = order_id
    current = ""
    pc = order.get("price_calc")
    if isinstance(pc, dict) and pc.get("total"):
        current = f"\nПоточна: {pc['total']:.0f} грн"
    await query.edit_message_text(
        f"💰 Введіть нову ціну для #{order_id} (грн):{current}\n\nабо /cancel",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=f"order_edit:{order_id}")
        ]])
    )


async def handle_delete_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Видалення замовлення — спочатку підтвердження."""
    query = update.callback_query
    await query.answer()
    order_id = query.data.split(":", 1)[1]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Так, видалити", callback_data=f"delete_confirm:{order_id}")],
        [InlineKeyboardButton("🔙 Скасувати", callback_data=f"order_edit:{order_id}")],
    ])
    await query.edit_message_text(
        f"🗑 Точно видалити замовлення #{order_id}?\n\nЦю дію не можна скасувати.",
        reply_markup=keyboard
    )


async def handle_delete_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Підтверджене видалення замовлення."""
    query = update.callback_query
    await query.answer()
    order_id = query.data.split(":", 1)[1]
    orders = load_orders()
    before = len(orders)
    orders = [o for o in orders if o.get("id") != order_id]
    if len(orders) < before:
        save_orders(orders)
        await query.edit_message_text(f"✅ Замовлення #{order_id} видалено")
    else:
        await query.edit_message_text(f"❌ Замовлення #{order_id} не знайдено")