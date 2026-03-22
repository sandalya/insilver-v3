"""Адмін панель для навчання бота."""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from core.config import ADMIN_IDS, DATA_DIR
from core.backup_system import (
    backup_trainer_collection, backup_training_record, list_backup_files, 
    restore_from_backup, convert_backup_to_training_record, emergency_log_trainer_data
)
from core.log_analyzer import (
    find_lost_trainer_data, auto_recover_lost_data, get_unconfirmed_records,
    confirm_record, reject_record
)

log = logging.getLogger("bot.admin")

# Файл з навчальними записами
TRAINING_FILE = Path(DATA_DIR) / "knowledge" / "training.json"
TRAINING_MEDIA_DIR = Path(DATA_DIR) / "knowledge" / "media"

# Створити директорії якщо не існують
TRAINING_MEDIA_DIR.mkdir(exist_ok=True, parents=True)

def is_admin(user_id: int) -> bool:
    """Перевірка чи користувач адмін."""
    return user_id in ADMIN_IDS

def load_training_data() -> List[Dict]:
    """Завантажити навчальні дані."""
    if not TRAINING_FILE.exists():
        return []
    try:
        with open(TRAINING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Помилка завантаження training.json: {e}")
        return []

def save_training_data(data: List[Dict]) -> bool:
    """Зберегти навчальні дані."""
    try:
        with open(TRAINING_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log.error(f"Помилка збереження training.json: {e}")
        return False

async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати головну адмін панель."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ заборонено")
        return
    
    training_data = load_training_data()
    confirmed_count = len([r for r in training_data if r.get("status", "confirmed") != "unconfirmed"])
    unconfirmed_data = get_unconfirmed_records()
    unconfirmed_count = len(unconfirmed_data)
    
    keyboard_buttons = []
    
    # Основні кнопки
    keyboard_buttons.extend([
        [InlineKeyboardButton("🎓 Тренер мод", callback_data="admin_trainer")],
        [InlineKeyboardButton("📋 Переглянути знання", callback_data="admin_view")],
    ])
    
    # Кнопка неподтверджених записів (якщо є)
    if unconfirmed_count > 0:
        keyboard_buttons.append([
            InlineKeyboardButton(f"⚠️ Непідтверджені ({unconfirmed_count})", callback_data="admin_unconfirmed")
        ])
    
    keyboard_buttons.extend([
        [InlineKeyboardButton("💾 Відновити дані", callback_data="admin_recover")],
        [InlineKeyboardButton("🔍 Сканувати втрачені", callback_data="admin_scan_lost")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("❌ Закрити", callback_data="admin_close")]
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    status_text = f"Підтверджених: {confirmed_count}"
    if unconfirmed_count > 0:
        status_text += f"\n⚠️ Неподтверджених: {unconfirmed_count}"
    
    text = f"🔧 *Адмін панель InSilver v3*\n\n{status_text}\n\nОберіть дію:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def start_trainer_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Активувати тренер режим."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    # Встановити тренер режим
    ctx.user_data["trainer_mode"] = True
    ctx.user_data["trainer_session"] = {
        "started": datetime.now().isoformat(),
        "records": []
    }
    
    # Перевіряємо чи є активна збірка
    collection = ctx.user_data.get("trainer_collection", [])
    keyboard_buttons = []
    
    if collection:
        keyboard_buttons.append([
            InlineKeyboardButton(f"💾 Завершити збірку ({len(collection)})", callback_data="trainer_finish_collection")
        ])
    
    keyboard_buttons.extend([
        [InlineKeyboardButton("✅ Завершити тренування", callback_data="trainer_finish")],
        [InlineKeyboardButton("📊 Статус", callback_data="trainer_status")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    # Перевіряємо чи є активна збірка
    collection = ctx.user_data.get("trainer_collection", [])
    collection_info = f"\n\n📦 *Активна збірка: {len(collection)} записів*" if collection else ""
    
    text = (
        "🎓 *Тренер режим активовано*\n\n"
        "Я буду пропонувати записати кожне ваше повідомлення.\n\n"
        "Розкажіть що треба знати боту:\n"
        "• Відповіді на питання клієнтів\n"
        "• Інструкції з вимірювань\n"
        "• Правила роботи\n\n"
        "Можете додавати фото та відео.\n\n"
        "_Для кожного повідомлення: 📥Додати до збірки або ❌Пропустити_"
        f"{collection_info}"
    )
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    log.info(f"Тренер режим активовано для {user_id}")

async def show_trainer_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати статус тренер сесії."""
    query = update.callback_query
    await query.answer()
    
    session = ctx.user_data.get("trainer_session", {})
    all_records = session.get("records", [])
    confirmed = len([r for r in all_records if r.get("confirmed", False)])
    total = len(all_records)
    started = session.get("started", "")[:16]  # YYYY-MM-DD HH:MM
    
    # Інформація про збірку
    collection = ctx.user_data.get("trainer_collection", [])
    collection_info = f"📦 В збірці: {len(collection)} записів\n" if collection else ""
    
    text = (
        f"📊 *Статус тренування*\n\n"
        f"Почато: {started}\n"
        f"Всього повідомлень: {total}\n"
        f"Підтверджено: {confirmed}\n"
        f"В очікуванні: {total - confirmed}\n"
        f"{collection_info}\n"
        f"_Продовжуйте надсилати повідомлення_"
    )
    
    # Кнопки залежно від стану збірки
    keyboard_buttons = []
    if collection:
        keyboard_buttons.append([
            InlineKeyboardButton(f"💾 Завершити збірку ({len(collection)})", callback_data="trainer_finish_collection")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton("🔙 Назад до тренера", callback_data="admin_trainer")
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_trainer_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробка повідомлень в тренер режимі."""
    if not ctx.user_data.get("trainer_mode"):
        return False  # Не в тренер режимі
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return False
    
    message = update.message
    text = message.text or message.caption or ""
    
    # Ігноруємо команди
    if text.startswith('/'):
        log.info(f"Тренер: ігноруємо команду {text}")
        return True  # Не відповідаємо, але блокуємо обробку
    
    # Ігноруємо порожні повідомлення без медіа
    if not text and not message.photo and not message.video and not message.document:
        return True
    
    media_files = []
    
    # Обробляємо медіа
    if message.photo:
        media_files.append({
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "caption": text
        })
        text = text or "Фото без підпису"
    
    if message.video:
        media_files.append({
            "type": "video", 
            "file_id": message.video.file_id,
            "caption": text
        })
        text = text or "Відео без підпису"
    
    if message.document:
        media_files.append({
            "type": "document",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name,
            "caption": text
        })
        text = text or f"Документ: {message.document.file_name}"
    
    # Зберігаємо в сесію з можливістю підтвердження
    session = ctx.user_data.get("trainer_session", {})
    session["records"] = session.get("records", [])
    
    record_id = len(session["records"])
    session["records"].append({
        "id": record_id,
        "text": text,
        "media": media_files,
        "timestamp": datetime.now().isoformat(),
        "confirmed": False  # Чекає підтвердження
    })
    
    ctx.user_data["trainer_session"] = session
    
    # Кнопки для збирання
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Додати до збірки", callback_data=f"trainer_collect_{record_id}")],
        [InlineKeyboardButton("❌ Пропустити", callback_data=f"trainer_skip_{record_id}")],
        [InlineKeyboardButton("💾 Завершити збірку", callback_data="trainer_finish_collection")]
    ])
    
    # Показуємо поточну збірку
    collection = ctx.user_data.get("trainer_collection", [])
    collection_text = ""
    if collection:
        collection_text = f"\n\n📦 *В збірці ({len(collection)} записів):*\n"
        for i, item in enumerate(collection[-3:], 1):  # Останні 3
            collection_text += f"{i}. {item['text'][:50]}...\n"
    
    preview = f"📝 *Нове повідомлення:*\n{text[:200]}"
    if len(text) > 200:
        preview += "..."
    if media_files:
        preview += f"\n📎 Медіа: {len(media_files)}"
    
    preview += collection_text
    
    await message.reply_text(
        preview, 
        parse_mode="Markdown",
        reply_markup=keyboard,
        reply_to_message_id=message.message_id
    )
    
    log.info(f"Тренер: запропоновано запис від {user_id}: {text[:50]}")
    return True

async def finish_trainer_session(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Завершити тренер сесію і зберегти дані."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = ctx.user_data.get("trainer_session", {})
    all_records = session.get("records", [])
    
    # Тільки підтверджені записи
    confirmed_records = [r for r in all_records if r.get("confirmed", False)]
    
    # Перевіряємо чи є незавершена збірка
    collection = ctx.user_data.get("trainer_collection", [])
    if collection:
        text = (
            f"⚠️ *У вас є незавершена збірка ({len(collection)} записів)*\n\n"
            f"Що робити з нею?"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💾 Завершити збірку", callback_data="trainer_finish_collection")],
            [InlineKeyboardButton("❌ Скасувати збірку", callback_data="trainer_cancel_collection")],
            [InlineKeyboardButton("🔙 Продовжити тренування", callback_data="admin_trainer")]
        ])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return
    
    if not confirmed_records:
        await query.edit_message_text(
            "🤷‍♂️ Нічого не підтверджено для запису.\n\nТренер режим завершено.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
            ]])
        )
        ctx.user_data.pop("trainer_mode", None)
        ctx.user_data.pop("trainer_session", None)
        return
    
    records = confirmed_records
    
    # Зберігаємо записи
    try:
        # Завантажуємо існуючі дані
        training_data = load_training_data()
        
        # Створюємо новий запис
        new_record = {
            "id": len(training_data) + 1,
            "title": f"Тренування {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "created_by": user_id,
            "created": datetime.now().isoformat(),
            "content": [],
            "media": []
        }
        
        # Обробляємо всі записи сесії
        for record in records:
            content_item = {
                "text": record["text"],
                "timestamp": record["timestamp"]
            }
            
            # Зберігаємо медіа файли
            for media in record.get("media", []):
                try:
                    # Завантажуємо файл
                    file = await ctx.bot.get_file(media["file_id"])
                    
                    # Генеруємо унікальне ім'я
                    ext = "jpg" if media["type"] == "photo" else "mp4" if media["type"] == "video" else "bin"
                    filename = f"{new_record['id']}_{len(new_record['media'])}_{int(datetime.now().timestamp())}.{ext}"
                    local_path = TRAINING_MEDIA_DIR / filename
                    
                    # Завантажуємо файл
                    await file.download_to_drive(local_path)
                    
                    # Додаємо до медіа
                    new_record["media"].append({
                        "type": media["type"],
                        "path": str(local_path.relative_to(Path(DATA_DIR))),
                        "caption": media.get("caption", ""),
                        "filename": media.get("file_name", filename)
                    })
                    
                except Exception as e:
                    log.error(f"Помилка збереження медіа {media['file_id']}: {e}")
                    continue
            
            new_record["content"].append(content_item)
        
        # Додаємо до загального списку
        training_data.append(new_record)
        
        # Зберігаємо
        if save_training_data(training_data):
            text = (
                f"✅ *Тренування завершено*\n\n"
                f"Записано: {len(records)} повідомлень\n"
                f"Медіа: {len(new_record['media'])} файлів\n\n"
                f"ID запису: {new_record['id']}"
            )
        else:
            text = "❌ Помилка збереження даних"
            
    except Exception as e:
        log.error(f"Помилка завершення тренер сесії: {e}")
        text = "❌ Помилка збереження даних"
    
    # Очищаємо сесію
    ctx.user_data.pop("trainer_mode", None)
    ctx.user_data.pop("trainer_session", None)
    ctx.user_data.pop("trainer_collection", None)
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
    ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    log.info(f"Тренер сесія завершена для {user_id}")

async def view_knowledge(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Переглянути існуючі знання."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    training_data = load_training_data()
    
    if not training_data:
        text = "📋 База знань порожня.\n\nПочніть з тренер режиму."
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
        ]])
    else:
        text = f"📋 *База знань ({len(training_data)} записів)*\n\n"
        keyboard_buttons = []
        
        for record in training_data[-10:]:  # Останні 10
            title = record.get("title", f"Запис {record.get('id', '?')}")
            created = record.get("created", "")[:10]  # YYYY-MM-DD
            button_text = f"{title[:25]}... ({created})"
            
            keyboard_buttons.append([
                InlineKeyboardButton(button_text, callback_data=f"knowledge_view_{record['id']}")
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
        ])
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        if len(training_data) > 10:
            text += "_Показані останні 10 записів_\n\n"
        
        text += "Оберіть запис для перегляду:"
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_knowledge_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Показати детальний перегляд навчального запису."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    training_data = load_training_data()
    record = next((r for r in training_data if r.get("id") == record_id), None)
    
    if not record:
        await query.edit_message_text("❌ Запис не знайдено")
        return
    
    title = record.get("title", f"Запис {record_id}")
    created = record.get("created", "")[:16]  # YYYY-MM-DD HH:MM
    created_by = record.get("created_by", "невідомо")
    
    # Інформація про редагування
    edited = record.get("edited")
    edit_info = ""
    if edited:
        edited_date = edited[:16] if edited else ""
        edited_by = record.get("edited_by", "невідомо")
        edit_info = f"✏️ Редаговано: {edited_date} (by {edited_by})\n"
    
    # Контент
    content = record.get("content", [])
    if isinstance(content, list):
        content_text = "\n\n".join([item.get("text", "") for item in content])
    else:
        content_text = str(content)
    
    # Обрізати якщо дуже довгий
    if len(content_text) > 800:
        content_text = content_text[:800] + "..."
    
    # Медіа
    media = record.get("media", [])
    media_info = f"\n📎 Медіа: {len(media)} файлів" if media else ""
    
    text = (
        f"📋 *{title}*\n\n"
        f"📅 Створено: {created}\n"
        f"👤 Автор: {created_by}\n"
        f"{edit_info}"
        f"{media_info}\n\n"
        f"📝 *Контент:*\n{content_text}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Редагувати", callback_data=f"knowledge_edit_{record_id}")],
        [InlineKeyboardButton("🗑️ Видалити", callback_data=f"knowledge_delete_{record_id}")],
        [InlineKeyboardButton("📋 До списку", callback_data="admin_view")]
    ])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def delete_knowledge_record(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Видалити навчальний запис."""
    query = update.callback_query
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.answer("❌ Доступ заборонено")
        return
    
    training_data = load_training_data()
    record = next((r for r in training_data if r.get("id") == record_id), None)
    
    if not record:
        await query.answer("❌ Запис не знайдено")
        return
    
    title = record.get("title", f"Запис {record_id}")
    
    # Підтвердження видалення
    text = (
        f"🗑️ *Видалити запис?*\n\n"
        f"**{title}**\n\n"
        f"⚠️ Ця дія незворотна!\n"
        f"Також видаляться всі медіа файли."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Так, видалити", callback_data=f"knowledge_confirm_delete_{record_id}")],
        [InlineKeyboardButton("❌ Скасувати", callback_data=f"knowledge_view_{record_id}")]
    ])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def confirm_delete_knowledge(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Підтвердити видалення навчального запису."""
    query = update.callback_query
    await query.answer("🗑️ Видаляю...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        training_data = load_training_data()
        record = next((r for r in training_data if r.get("id") == record_id), None)
        
        if not record:
            await query.edit_message_text("❌ Запис не знайдено")
            return
        
        title = record.get("title", f"Запис {record_id}")
        
        # Видаляємо медіа файли
        media_deleted = 0
        for media_item in record.get("media", []):
            try:
                media_path = Path(DATA_DIR) / media_item.get("path", "")
                if media_path.exists():
                    media_path.unlink()
                    media_deleted += 1
            except Exception as e:
                log.warning(f"Не вдалось видалити медіа {media_item.get('path', '')}: {e}")
        
        # Видаляємо запис зі списку
        training_data = [r for r in training_data if r.get("id") != record_id]
        
        # Зберігаємо оновлений список
        if save_training_data(training_data):
            text = (
                f"✅ *Запис видалено*\n\n"
                f"**{title}**\n\n"
                f"Медіа файлів видалено: {media_deleted}\n"
                f"Записів залишилось: {len(training_data)}"
            )
        else:
            text = "❌ Помилка збереження після видалення"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 До списку знань", callback_data="admin_view")]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        log.info(f"Видалено навчальний запис {record_id} адміном {user_id}")
        
    except Exception as e:
        log.error(f"Помилка видалення запису {record_id}: {e}")
        await query.edit_message_text("❌ Помилка видалення запису")

async def start_knowledge_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Почати редагування навчального запису."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    training_data = load_training_data()
    record = next((r for r in training_data if r.get("id") == record_id), None)
    
    if not record:
        await query.edit_message_text("❌ Запис не знайдено")
        return
    
    title = record.get("title", f"Запис {record_id}")
    
    # Поточний контент для редагування
    content = record.get("content", [])
    if isinstance(content, list):
        current_text = "\n\n".join([item.get("text", "") for item in content])
    else:
        current_text = str(content)
    
    # Встановити режим редагування
    ctx.user_data["edit_mode"] = {
        "record_id": record_id,
        "original_text": current_text,
        "title": title
    }
    
    preview = current_text[:500] + "..." if len(current_text) > 500 else current_text
    
    text = (
        f"✏️ *Редагування: {title}*\n\n"
        f"**Поточний текст:**\n{preview}\n\n"
        f"📝 Надішліть новий текст або натисніть скасувати:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Скасувати", callback_data=f"knowledge_view_{record_id}")]
    ])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_edit_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробити новий текст для редагування."""
    edit_mode = ctx.user_data.get("edit_mode")
    if not edit_mode:
        return False  # Не в режимі редагування
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return False
    
    new_text = update.message.text
    if not new_text:
        return True  # Блокуємо, але не обробляємо порожній текст
    
    record_id = edit_mode["record_id"]
    title = edit_mode["title"]
    
    # Показати попередження перед збереженням
    preview = new_text[:300] + "..." if len(new_text) > 300 else new_text
    
    text = (
        f"✏️ *Підтвердити зміни: {title}*\n\n"
        f"**Новий текст:**\n{preview}\n\n"
        f"💾 Зберегти зміни?"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Зберегти", callback_data=f"knowledge_save_edit_{record_id}")],
        [InlineKeyboardButton("❌ Скасувати", callback_data=f"knowledge_view_{record_id}")]
    ])
    
    # Зберегти новий текст в сесію
    ctx.user_data["edit_mode"]["new_text"] = new_text
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    return True

async def save_knowledge_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Зберегти зміни в навчальному записі."""
    query = update.callback_query
    await query.answer("💾 Зберігаю...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    edit_mode = ctx.user_data.get("edit_mode")
    if not edit_mode or edit_mode.get("record_id") != record_id:
        await query.edit_message_text("❌ Помилка: дані редагування не знайдено")
        return
    
    new_text = edit_mode.get("new_text")
    if not new_text:
        await query.edit_message_text("❌ Помилка: новий текст не знайдено")
        return
    
    try:
        training_data = load_training_data()
        record = next((r for r in training_data if r.get("id") == record_id), None)
        
        if not record:
            await query.edit_message_text("❌ Запис не знайдено")
            return
        
        title = record.get("title", f"Запис {record_id}")
        
        # Оновити контент
        record["content"] = [{
            "text": new_text,
            "timestamp": datetime.now().isoformat()
        }]
        
        # Додати інформацію про редагування
        record["edited"] = datetime.now().isoformat()
        record["edited_by"] = user_id
        
        # Зберегти оновлений список
        if save_training_data(training_data):
            text = (
                f"✅ *Запис оновлено*\n\n"
                f"**{title}**\n\n"
                f"📅 Редаговано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                f"👤 Редактор: {user_id}"
            )
        else:
            text = "❌ Помилка збереження змін"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Переглянути", callback_data=f"knowledge_view_{record_id}")],
            [InlineKeyboardButton("📋 До списку", callback_data="admin_view")]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        log.info(f"Відредаговано навчальний запис {record_id} адміном {user_id}")
        
        # Очистити режим редагування
        ctx.user_data.pop("edit_mode", None)
        
    except Exception as e:
        log.error(f"Помилка редагування запису {record_id}: {e}")
        await query.edit_message_text("❌ Помилка збереження змін")

async def show_conversation_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати статистику розмов."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        from core.conversation_logger import get_conversation_stats
        
        # Статистика за останні 24 години
        stats_24h = get_conversation_stats(24)
        stats_7d = get_conversation_stats(24 * 7)
        
        if "error" in stats_24h:
            text = f"❌ Помилка отримання статистики:\n{stats_24h['error']}"
        else:
            text = (
                f"📊 *Статистика розмов*\n\n"
                f"**За 24 години:**\n"
                f"• Повідомлень від клієнтів: {stats_24h['total_messages']}\n"
                f"• Унікальних користувачів: {stats_24h['unique_users']}\n"
                f"• Відповідей бота: {stats_24h['bot_responses']}\n"
                f"• Дії з замовленнями: {stats_24h['orders']}\n"
                f"• Помилки: {stats_24h['errors']}\n"
                f"• Сер. час AI відповіді: {stats_24h['avg_response_time']:.2f}с\n\n"
                f"**За 7 днів:**\n"
                f"• Повідомлень: {stats_7d['total_messages']}\n"
                f"• Унікальних користувачів: {stats_7d['unique_users']}\n"
                f"• Відповідей: {stats_7d['bot_responses']}\n"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ])
        
    except Exception as e:
        text = f"❌ Помилка отримання статистики: {e}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_recovery_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати меню відновлення даних."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        backups = list_backup_files()
        user_backups = [b for b in backups if b.get("user_id") == user_id]
        
        text = (
            f"💾 *Відновлення даних*\n\n"
            f"Знайдено бекапів: {len(backups)}\n"
            f"Ваших бекапів: {len(user_backups)}\n\n"
            f"Оберіть дію:"
        )
        
        keyboard_buttons = []
        if user_backups:
            keyboard_buttons.append([
                InlineKeyboardButton("📋 Мої бекапи", callback_data="recovery_my_backups")
            ])
        
        keyboard_buttons.extend([
            [InlineKeyboardButton("🔍 Всі бекапи", callback_data="recovery_all_backups")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
        ])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
    except Exception as e:
        text = f"❌ Помилка завантаження бекапів: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_backup_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE, show_all: bool = False):
    """Показати список бекапів."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        backups = list_backup_files()
        if not show_all:
            backups = [b for b in backups if b.get("user_id") == user_id]
        
        if not backups:
            text = "📋 Бекапів не знайдено."
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_recover")
            ]])
        else:
            text = f"📋 *Бекапи ({'всі' if show_all else 'ваші'}):*\n\n"
            keyboard_buttons = []
            
            for backup in backups[:10]:  # Показуємо останні 10
                timestamp = backup["timestamp"][:16] if backup["timestamp"] else "?"
                backup_type = "📦 збірка" if backup["type"] == "trainer_collection" else "📝 запис"
                size_info = f"({backup['size']})" if backup["size"] > 1 else ""
                
                button_text = f"{backup_type} {timestamp} {size_info}"
                if len(button_text) > 30:
                    button_text = button_text[:27] + "..."
                
                keyboard_buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"recovery_show_{backup['filename']}")
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton("🔙 Назад", callback_data="admin_recover")
            ])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
    except Exception as e:
        text = f"❌ Помилка: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_recover")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_backup_details(update: Update, ctx: ContextTypes.DEFAULT_TYPE, filename: str):
    """Показати детальну інформацію про бекап."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        from core.backup_system import BACKUP_DIR
        backup_path = BACKUP_DIR / filename
        backup_data = restore_from_backup(str(backup_path))
        
        if not backup_data:
            await query.edit_message_text("❌ Не вдалось завантажити бекап")
            return
        
        backup_type = backup_data.get("type", "unknown")
        timestamp = backup_data.get("timestamp", "")[:16]
        
        if backup_type == "trainer_collection":
            collection = backup_data.get("collection", [])
            preview = "\n".join([f"• {item['text'][:50]}..." for item in collection[:3]])
            if len(collection) > 3:
                preview += f"\n... і ще {len(collection) - 3}"
            
            text = (
                f"📦 *Бекап збірки*\n\n"
                f"📅 Час: {timestamp}\n"
                f"📝 Записів: {len(collection)}\n\n"
                f"**Зміст:**\n{preview}"
            )
        else:
            record = backup_data.get("record", {})
            content = record.get("content", [])
            preview = content[0].get("text", "")[:100] + "..." if content else "Порожньо"
            
            text = (
                f"📝 *Бекап запису*\n\n"
                f"📅 Час: {timestamp}\n"
                f"🆔 ID: {record.get('id', '?')}\n"
                f"📋 Назва: {record.get('title', 'Без назви')}\n\n"
                f"**Зміст:**\n{preview}"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Відновити", callback_data=f"recovery_restore_{filename}")],
            [InlineKeyboardButton("📋 До списку", callback_data="recovery_my_backups")]
        ])
        
    except Exception as e:
        text = f"❌ Помилка завантаження бекапу: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 До списку", callback_data="recovery_my_backups")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def restore_backup(update: Update, ctx: ContextTypes.DEFAULT_TYPE, filename: str):
    """Відновити дані з бекапу."""
    query = update.callback_query
    await query.answer("🔄 Відновлюю...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        from core.backup_system import BACKUP_DIR
        backup_path = BACKUP_DIR / filename
        backup_data = restore_from_backup(str(backup_path))
        
        if not backup_data:
            await query.edit_message_text("❌ Не вдалось завантажити бекап")
            return
        
        if backup_data.get("type") == "trainer_collection":
            # Конвертуємо збірку в навчальний запис
            record = convert_backup_to_training_record(backup_data, user_id)
            if not record:
                await query.edit_message_text("❌ Не вдалось конвертувати бекап")
                return
            
            # Зберігаємо відновлений запис
            training_data = load_training_data()
            training_data.append(record)
            
            if save_training_data(training_data):
                text = (
                    f"✅ *Бекап відновлено*\n\n"
                    f"📝 Створено запис ID: {record['id']}\n"
                    f"📋 Назва: {record['title']}\n"
                    f"📅 Відновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                log.info(f"Відновлено бекап {filename} як запис {record['id']} адміном {user_id}")
            else:
                text = "❌ Помилка збереження відновленого запису"
        
        elif backup_data.get("type") == "training_record":
            # Відновлюємо готовий запис
            record = backup_data.get("record", {})
            training_data = load_training_data()
            
            # Перевіряємо чи не дублюється ID
            existing_ids = [r.get("id") for r in training_data]
            if record.get("id") in existing_ids:
                max_id = max(existing_ids, default=0)
                record["id"] = max_id + 1
                record["title"] += f" (відновлено як ID {record['id']})"
            
            training_data.append(record)
            
            if save_training_data(training_data):
                text = (
                    f"✅ *Запис відновлено*\n\n"
                    f"📝 ID: {record['id']}\n"
                    f"📋 Назва: {record.get('title', 'Без назви')}\n"
                    f"📅 Відновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                log.info(f"Відновлено запис {record['id']} з бекапу {filename} адміном {user_id}")
            else:
                text = "❌ Помилка збереження відновленого запису"
        else:
            text = "❌ Невідомий тип бекапу"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Переглянути знання", callback_data="admin_view")],
            [InlineKeyboardButton("💾 До відновлення", callback_data="admin_recover")]
        ])
        
    except Exception as e:
        log.error(f"Помилка відновлення бекапу {filename}: {e}")
        text = f"❌ Помилка відновлення: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 До списку", callback_data="recovery_my_backups")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def scan_for_lost_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Сканувати логи для пошуку втрачених записів."""
    query = update.callback_query
    await query.answer("🔍 Сканую логи...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        from core.ai import ask_ai
        
        # Автоматичне відновлення
        recovered_records = await auto_recover_lost_data(user_id, ask_ai)
        
        if not recovered_records:
            text = "🔍 *Сканування завершено*\n\nВтрачених записів не знайдено."
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
            ]])
        else:
            # Додаємо відновлені записи до бази
            training_data = load_training_data()
            training_data.extend(recovered_records)
            
            if save_training_data(training_data):
                text = (
                    f"✅ *Сканування завершено*\n\n"
                    f"Знайдено і відновлено: {len(recovered_records)} записів\n"
                    f"Статус: непідтверджені\n\n"
                    f"Перегляньте і підтвердіть їх у розділі 'Непідтверджені'"
                )
                log.info(f"Автоматично відновлено {len(recovered_records)} записів для {user_id}")
            else:
                text = "❌ Помилка збереження відновлених записів"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚠️ Переглянути непідтверджені", callback_data="admin_unconfirmed")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
            ])
        
    except Exception as e:
        log.error(f"Помилка сканування втрачених даних: {e}")
        text = f"❌ Помилка сканування: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_unconfirmed_records(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показати непідтверджені записи."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        unconfirmed_records = get_unconfirmed_records()
        
        if not unconfirmed_records:
            text = "⚠️ *Непідтверджені записи*\n\nНемає записів для перевірки."
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
            ]])
        else:
            text = f"⚠️ *Непідтверджені записи ({len(unconfirmed_records)})*\n\n"
            keyboard_buttons = []
            
            for record in unconfirmed_records[:10]:  # Показуємо перші 10
                record_id = abs(record.get("id", 0))
                title = record.get("title", f"Запис {record_id}")
                created = record.get("created", "")[:16] if record.get("created") else ""
                
                button_text = f"{title[:20]}... ({created})"
                keyboard_buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"unconfirmed_view_{record_id}")
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
            ])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            if len(unconfirmed_records) > 10:
                text += "_Показані перші 10 записів_\n\n"
            
            text += "Оберіть запис для перегляду:"
        
    except Exception as e:
        text = f"❌ Помилка: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_main")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_unconfirmed_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Показати детальний перегляд неподтвердженого запису."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    try:
        unconfirmed_records = get_unconfirmed_records()
        record = next((r for r in unconfirmed_records if abs(r.get("id", 0)) == record_id), None)
        
        if not record:
            await query.edit_message_text("❌ Запис не знайдено")
            return
        
        title = record.get("title", f"Запис {record.get('id', '?')}")
        created = record.get("created", "")[:16]
        recovery_time = record.get("original_analysis_time", "")[:16] if record.get("original_analysis_time") else ""
        
        # AI розширений контент
        content = record.get("content", [])
        if content:
            ai_content = content[0].get("text", "")
            if len(ai_content) > 600:
                ai_content = ai_content[:600] + "..."
        else:
            ai_content = "Порожньо"
        
        # Оригінальні фрагменти
        original_fragments = record.get("original_fragments", [])
        fragments_preview = ""
        if original_fragments:
            fragments_preview = "\n\n**Оригінальні фрагменти з логів:**\n"
            for i, fragment in enumerate(original_fragments[:3], 1):
                fragments_preview += f"{i}. {fragment.get('message', '')[:80]}...\n"
        
        text = (
            f"⚠️ *{title}*\n\n"
            f"📅 Відновлено: {created}\n"
            f"🕐 Втрачено: {recovery_time}\n"
            f"🤖 Джерело: автоматичний аналіз логів\n\n"
            f"**AI розширений зміст:**\n{ai_content}"
            f"{fragments_preview}\n\n"
            f"**Підтвердити цей запис?**"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Підтвердити", callback_data=f"unconfirmed_confirm_{record_id}")],
            [InlineKeyboardButton("❌ Відхилити", callback_data=f"unconfirmed_reject_{record_id}")],
            [InlineKeyboardButton("📋 До списку", callback_data="admin_unconfirmed")]
        ])
        
    except Exception as e:
        text = f"❌ Помилка завантаження запису: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 До списку", callback_data="admin_unconfirmed")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_unconfirmed_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE, action: str, record_id: int):
    """Обробити дію з неподтвердженим записом."""
    query = update.callback_query
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.answer("❌ Доступ заборонено")
        return
    
    try:
        if action == "confirm":
            await query.answer("✅ Підтверджую...")
            success = confirm_record(-record_id, user_id)  # Негативний ID для пошуку
            
            if success:
                text = "✅ *Запис підтверджено*\n\nЗапис переміщено до основної бази знань з новим ID."
                log.info(f"Підтверджено неподтверджений запис {record_id} адміном {user_id}")
            else:
                text = "❌ Помилка підтвердження запису"
                
        elif action == "reject":
            await query.answer("❌ Відхиляю...")
            success = reject_record(-record_id, user_id)  # Негативний ID для пошуку
            
            if success:
                text = "❌ *Запис відхилено*\n\nЗапис видалено з бази даних."
                log.info(f"Відхилено неподтверджений запис {record_id} адміном {user_id}")
            else:
                text = "❌ Помилка відхилення запису"
        else:
            text = "❌ Невідома дія"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚠️ До неподтверджених", callback_data="admin_unconfirmed")],
            [InlineKeyboardButton("🔧 Головна", callback_data="admin_main")]
        ])
        
    except Exception as e:
        log.error(f"Помилка обробки дії {action} для запису {record_id}: {e}")
        text = f"❌ Помилка: {e}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 До списку", callback_data="admin_unconfirmed")
        ]])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_trainer_collect(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Додати запис до збірки."""
    query = update.callback_query
    await query.answer("📥 Додано до збірки")
    
    session = ctx.user_data.get("trainer_session", {})
    records = session.get("records", [])
    
    # Знаходимо запис
    target_record = None
    for record in records:
        if record.get("id") == record_id:
            target_record = record
            break
    
    if target_record:
        # Додаємо до збірки
        collection = ctx.user_data.get("trainer_collection", [])
        collection.append(target_record)
        ctx.user_data["trainer_collection"] = collection
        
        # Видаляємо зі звичайних записів
        session["records"] = [r for r in records if r.get("id") != record_id]
        ctx.user_data["trainer_session"] = session
    
    # Оновити повідомлення з кнопкою завершення
    collection_size = len(ctx.user_data.get("trainer_collection", []))
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💾 Завершити збірку ({collection_size})", callback_data="trainer_finish_collection")]
    ])
    
    await query.edit_message_text(
        f"📥 *Додано до збірки*\n\n📦 В збірці: {collection_size} записів", 
        parse_mode="Markdown", 
        reply_markup=keyboard
    )

async def handle_trainer_finish_collection(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Завершити збірку і показати AI резюме."""
    query = update.callback_query
    await query.answer("🤖 Аналізую збірку...")
    
    collection = ctx.user_data.get("trainer_collection", [])
    if not collection:
        await query.edit_message_text("🤷‍♂️ Збірка порожня")
        return
    
    try:
        # Формуємо текст для AI
        combined_text = ""
        total_media = 0
        for item in collection:
            combined_text += f"{item['text']}\n\n"
            total_media += len(item.get('media', []))
        
        # AI резюме
        from core.ai import ask_ai
        ai_prompt = (
            f"Проаналізуй цю навчальну інформацію для бота-консультанта ювелірної майстерні:\n\n"
            f"{combined_text}\n\n"
            f"Створи структуроване резюме:\n"
            f"1. Основна тема (1 речення)\n"
            f"2. Ключові моменти (3-5 пунктів)\n"
            f"3. Можливі питання клієнтів (2-3 варіанти)\n\n"
            f"Відповідай українською, коротко та зрозуміло."
        )
        
        ai_summary = await ask_ai(189793675, ai_prompt, [])
        
        # Показуємо резюме з можливістю підтвердити
        text = (
            f"🤖 *AI Аналіз збірки ({len(collection)} записів):*\n\n"
            f"{ai_summary}\n\n"
            f"📎 Медіа: {total_media} файлів\n\n"
            f"*Зберегти цю збірку як навчальний запис?*"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Зберегти", callback_data="trainer_save_collection")],
            [InlineKeyboardButton("✏️ Доповнити", callback_data="trainer_edit_collection")],
            [InlineKeyboardButton("❌ Скасувати", callback_data="trainer_cancel_collection")]
        ])
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        log.error(f"Помилка AI аналізу збірки: {e}")
        await query.edit_message_text("❌ Помилка аналізу збірки")

async def handle_trainer_save_collection(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Зберегти збірку напряму в training.json."""
    query = update.callback_query
    await query.answer("💾 Зберігаю...")
    
    collection = ctx.user_data.get("trainer_collection", [])
    if not collection:
        await query.edit_message_text("❌ Збірка порожня")
        return
    
    try:
        # БЕКАП ЗБІРКИ ПЕРЕД ЗБЕРЕЖЕННЯМ
        backup_path = backup_trainer_collection(update.effective_user.id, collection)
        emergency_log_trainer_data(update.effective_user.id, "pre_save_collection", collection)
        
        # Завантажуємо існуючі навчальні дані
        training_data = load_training_data()
        
        # Генеруємо унікальний ID
        max_id = max([r.get("id", 0) for r in training_data], default=0)
        new_id = max_id + 1
        
        # Створюємо новий запис
        new_record = {
            "id": new_id,
            "title": f"Збірка {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "created_by": update.effective_user.id,
            "created": datetime.now().isoformat(),
            "content": [],
            "media": []
        }
        
        # Обробляємо всі записи збірки
        for item in collection:
            content_item = {
                "text": item["text"],
                "timestamp": item["timestamp"]
            }
            new_record["content"].append(content_item)
            
            # Зберігаємо медіа файли
            for media in item.get("media", []):
                try:
                    # Завантажуємо файл
                    file = await ctx.bot.get_file(media["file_id"])
                    
                    # Генеруємо унікальне ім'я
                    ext = "jpg" if media["type"] == "photo" else "mp4" if media["type"] == "video" else "bin"
                    filename = f"{new_id}_{len(new_record['media'])}_{int(datetime.now().timestamp())}.{ext}"
                    local_path = TRAINING_MEDIA_DIR / filename
                    
                    # Завантажуємо файл
                    await file.download_to_drive(local_path)
                    
                    # Додаємо до медіа
                    new_record["media"].append({
                        "type": media["type"],
                        "path": str(local_path.relative_to(Path(DATA_DIR))),
                        "caption": media.get("caption", ""),
                        "filename": media.get("file_name", filename)
                    })
                    
                except Exception as e:
                    log.error(f"Помилка збереження медіа {media['file_id']}: {e}")
                    continue
        
        # Додаємо до загального списку
        training_data.append(new_record)
        
        # Зберігаємо в файл
        if save_training_data(training_data):
            # Бекап готового запису
            backup_training_record(new_record)
            emergency_log_trainer_data(update.effective_user.id, "saved_record", new_record)
            
            text = (
                f"✅ *Збірку збережено*\n\n"
                f"ID: {new_id}\n"
                f"Записів об'єднано: {len(collection)}\n"
                f"Медіа файлів: {len(new_record['media'])}\n"
                f"Всього записів у базі: {len(training_data)}\n\n"
                f"💾 Бекап: {Path(backup_path).name if backup_path else 'помилка'}"
            )
            log.info(f"Збережено збірку як запис {new_id} адміном {update.effective_user.id}")
        else:
            text = "❌ Помилка збереження у файл"
    
    except Exception as e:
        log.error(f"Помилка збереження збірки: {e}")
        text = "❌ Помилка збереження збірки"
    
    # Очищуємо збірку
    ctx.user_data.pop("trainer_collection", None)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Переглянути знання", callback_data="admin_view")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_main")]
    ])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_trainer_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE, record_id: int):
    """Пропустити запис."""
    query = update.callback_query
    await query.answer("❌ Пропущено")
    
    session = ctx.user_data.get("trainer_session", {})
    records = session.get("records", [])
    
    # Видаляємо запис
    session["records"] = [r for r in records if r.get("id") != record_id]
    ctx.user_data["trainer_session"] = session
    
    # Оновити повідомлення
    await query.edit_message_text("❌ *Пропущено*", parse_mode="Markdown")

async def handle_admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обробка callback від адмін панелі."""
    query = update.callback_query
    data = query.data
    
    if data == "admin_main":
        await admin_panel(update, ctx)
    elif data == "admin_trainer":
        await start_trainer_mode(update, ctx)
    elif data == "trainer_finish":
        await finish_trainer_session(update, ctx)
    elif data == "trainer_status":
        await show_trainer_status(update, ctx)
    elif data == "admin_view":
        await view_knowledge(update, ctx)
    elif data == "admin_stats":
        await show_conversation_stats(update, ctx)
    elif data == "admin_recover":
        await show_recovery_menu(update, ctx)
    elif data == "recovery_my_backups":
        await show_backup_list(update, ctx, show_all=False)
    elif data == "recovery_all_backups":
        await show_backup_list(update, ctx, show_all=True)
    elif data.startswith("recovery_show_"):
        filename = data.replace("recovery_show_", "")
        await show_backup_details(update, ctx, filename)
    elif data.startswith("recovery_restore_"):
        filename = data.replace("recovery_restore_", "")
        await restore_backup(update, ctx, filename)
    elif data == "admin_scan_lost":
        await scan_for_lost_data(update, ctx)
    elif data == "admin_unconfirmed":
        await show_unconfirmed_records(update, ctx)
    elif data.startswith("unconfirmed_view_"):
        record_id = int(data.split("_")[2])
        await show_unconfirmed_detail(update, ctx, record_id)
    elif data.startswith("unconfirmed_confirm_"):
        record_id = int(data.split("_")[2])
        await handle_unconfirmed_action(update, ctx, "confirm", record_id)
    elif data.startswith("unconfirmed_reject_"):
        record_id = int(data.split("_")[2])
        await handle_unconfirmed_action(update, ctx, "reject", record_id)
    elif data == "admin_close":
        await query.delete_message()
    elif data.startswith("trainer_collect_"):
        record_id = int(data.split("_")[2])
        await handle_trainer_collect(update, ctx, record_id)
    elif data.startswith("trainer_skip_"):
        record_id = int(data.split("_")[2])
        await handle_trainer_skip(update, ctx, record_id)
    elif data == "trainer_finish_collection":
        await handle_trainer_finish_collection(update, ctx)
    elif data == "trainer_save_collection":
        await handle_trainer_save_collection(update, ctx)
    elif data == "trainer_edit_collection":
        await query.answer("✏️ Напишіть доповнення і натисніть 'Додати до збірки'")
    elif data == "trainer_cancel_collection":
        ctx.user_data.pop("trainer_collection", None)
        await query.edit_message_text("❌ *Збірку скасовано*", parse_mode="Markdown")
    elif data.startswith("knowledge_view_"):
        record_id = int(data.split("_")[2])
        await show_knowledge_detail(update, ctx, record_id)
    elif data.startswith("knowledge_delete_"):
        record_id = int(data.split("_")[2])
        await delete_knowledge_record(update, ctx, record_id)
    elif data.startswith("knowledge_confirm_delete_"):
        record_id = int(data.split("_")[3])
        await confirm_delete_knowledge(update, ctx, record_id)
    elif data.startswith("knowledge_edit_"):
        record_id = int(data.split("_")[2])
        await start_knowledge_edit(update, ctx, record_id)
    elif data.startswith("knowledge_save_edit_"):
        record_id = int(data.split("_")[3])
        await save_knowledge_edit(update, ctx, record_id)
    else:
        await query.answer("❓ Невідома команда")

# Експортні хендлери для main
def create_admin_handlers():
    """Створити хендлери для адмін панелі."""
    from telegram.ext import CommandHandler
    
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(handle_admin_callback, pattern="^(admin_|trainer_|knowledge_|recovery_|unconfirmed_)"),
        MessageHandler(
            filters.TEXT,
            handle_edit_input
        ),
        MessageHandler(
            filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL,
            handle_trainer_input
        )
    ]