"""Аналіз логів для пошуку втрачених навчальних записів."""
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from core.config import LOGS_DIR
from core.conversation_logger import log_user_message

log = logging.getLogger("log_analyzer")

def find_lost_trainer_data() -> List[Dict]:
    """Знайти втрачені навчальні записи в логах."""
    lost_records = []
    
    try:
        # Аналізуємо основний лог
        bot_log = Path(LOGS_DIR) / "bot.log"
        if not bot_log.exists():
            return lost_records
        
        # Шукаємо записи тренер режиму
        trainer_patterns = [
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[INFO\] bot\.admin: Тренер: записано повідомлення від (\d+): (.+)",
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[INFO\] bot\.admin: AI аналіз збірки для (\d+)",
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[INFO\] bot\.admin: Збережено збірку як запис (\d+) адміном (\d+)"
        ]
        
        # Читаємо останні 1000 рядків
        with open(bot_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-1000:]
        
        # Аналізуємо кожен рядок
        trainer_messages = []
        collection_analyses = []
        saved_records = []
        
        for line in lines:
            # Пошук повідомлень тренера
            match = re.search(trainer_patterns[0], line)
            if match:
                timestamp_str, user_id, message = match.groups()
                trainer_messages.append({
                    "timestamp": timestamp_str,
                    "user_id": int(user_id),
                    "message": message,
                    "type": "trainer_message"
                })
            
            # Пошук AI аналізів
            match = re.search(trainer_patterns[1], line)
            if match:
                timestamp_str, user_id = match.groups()
                collection_analyses.append({
                    "timestamp": timestamp_str,
                    "user_id": int(user_id),
                    "type": "ai_analysis"
                })
            
            # Пошук збережених записів
            match = re.search(trainer_patterns[2], line)
            if match:
                timestamp_str, record_id, user_id = match.groups()
                saved_records.append({
                    "timestamp": timestamp_str,
                    "record_id": int(record_id),
                    "user_id": int(user_id),
                    "type": "saved_record"
                })
        
        # Знаходимо аналізи без збережених записів
        for analysis in collection_analyses:
            analysis_time = datetime.strptime(analysis["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
            user_id = analysis["user_id"]
            
            # Шукаємо збереження протягом 5 хвилин після аналізу
            found_save = False
            for save in saved_records:
                save_time = datetime.strptime(save["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
                if (save["user_id"] == user_id and 
                    save_time > analysis_time and 
                    save_time <= analysis_time + timedelta(minutes=5)):
                    found_save = True
                    break
            
            if not found_save:
                # Знаходимо повідомлення тренера перед цим аналізом
                related_messages = []
                for msg in trainer_messages:
                    msg_time = datetime.strptime(msg["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
                    if (msg["user_id"] == user_id and 
                        msg_time <= analysis_time and 
                        msg_time >= analysis_time - timedelta(hours=1)):
                        related_messages.append(msg)
                
                if related_messages:
                    lost_records.append({
                        "analysis_timestamp": analysis["timestamp"],
                        "user_id": user_id,
                        "messages": related_messages,
                        "type": "lost_collection"
                    })
        
        log.info(f"Знайдено {len(lost_records)} втрачених записів у логах")
        return lost_records
        
    except Exception as e:
        log.error(f"Помилка аналізу логів: {e}")
        return []

def analyze_conversation_logs(user_id: int, hours: int = 2) -> List[Dict]:
    """Аналізувати логи розмов для пошуку тренер даних."""
    try:
        conversations_log = Path(LOGS_DIR) / "conversations.log"
        if not conversations_log.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        trainer_entries = []
        
        with open(conversations_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    # Шукаємо записи пов'язані з тренер режимом
                    if "тренер" in line.lower() or "збірка" in line.lower():
                        # Парсимо timestamp
                        timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            entry_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            
                            if entry_time >= cutoff_time:
                                trainer_entries.append({
                                    "timestamp": timestamp_str,
                                    "content": line.strip(),
                                    "type": "conversation_log"
                                })
                except Exception:
                    continue
        
        return trainer_entries
        
    except Exception as e:
        log.error(f"Помилка аналізу логів розмов: {e}")
        return []

async def ai_expand_lost_record(lost_record: Dict, ai_function) -> Optional[Dict]:
    """Використати AI для розширення втраченого запису."""
    try:
        messages = lost_record.get("messages", [])
        if not messages:
            return None
        
        # Формуємо контент для AI
        messages_text = "\n".join([f"- {msg['message']}" for msg in messages])
        analysis_time = lost_record.get("analysis_timestamp", "")
        
        ai_prompt = (
            f"Відновлення втраченого навчального запису для бота-консультанта ювелірної майстерні.\n\n"
            f"Знайдені фрагменти з логів (час аналізу: {analysis_time}):\n"
            f"{messages_text}\n\n"
            f"Завдання:\n"
            f"1. Проаналізуй ці фрагменти\n"
            f"2. Створи структурований навчальний запис\n"
            f"3. Розшири їх у корисні інструкції для бота\n"
            f"4. Додай можливі питання клієнтів до цієї теми\n\n"
            f"Формат відповіді:\n"
            f"**Тема:** [назва теми]\n"
            f"**Зміст:** [детальний опис]\n"
            f"**Інструкції:** [як боту відповідати]\n"
            f"**Питання клієнтів:** [можливі варіанти]\n\n"
            f"Відповідай українською мовою."
        )
        
        # Викликаємо AI (передаємо функцію як параметр)
        ai_response = await ai_function(lost_record["user_id"], ai_prompt, [])
        
        return {
            "ai_expanded_content": ai_response,
            "original_messages": messages,
            "analysis_timestamp": analysis_time,
            "user_id": lost_record["user_id"]
        }
        
    except Exception as e:
        log.error(f"Помилка AI розширення запису: {e}")
        return None

def create_unconfirmed_record(expanded_data: Dict) -> Dict:
    """Створити неподтверджений запис з розширених даних."""
    try:
        # Завантажуємо існуючі дані
        training_data = load_training_data()
        
        # Генеруємо ID для неподтвердженого запису (негативний щоб не конфліктувати)
        unconfirmed_ids = [r.get("id", 0) for r in training_data if r.get("id", 0) < 0]
        new_id = min(unconfirmed_ids, default=0) - 1
        
        # Створюємо запис
        record = {
            "id": new_id,
            "title": f"Втрачений запис (відновлено {datetime.now().strftime('%d.%m.%Y %H:%M')})",
            "created": datetime.now().isoformat(),
            "created_by": expanded_data["user_id"],
            "status": "unconfirmed",  # Особливий статус
            "recovery_source": "log_analysis",
            "original_analysis_time": expanded_data.get("analysis_timestamp", ""),
            "content": [{
                "text": expanded_data["ai_expanded_content"],
                "timestamp": datetime.now().isoformat(),
                "recovery_method": "ai_expansion"
            }],
            "original_fragments": expanded_data.get("original_messages", []),
            "media": []
        }
        
        log.info(f"Створено неподтверджений запис ID {new_id}")
        return record
        
    except Exception as e:
        log.error(f"Помилка створення неподтвердженого запису: {e}")
        return {}

async def auto_recover_lost_data(user_id: int, ai_function) -> List[Dict]:
    """Автоматично відновити втрачені дані."""
    recovered_records = []
    
    try:
        # Знаходимо втрачені записи
        lost_records = find_lost_trainer_data()
        user_lost_records = [r for r in lost_records if r.get("user_id") == user_id]
        
        log.info(f"Знайдено {len(user_lost_records)} втрачених записів для користувача {user_id}")
        
        # Обробляємо кожен втрачений запис
        for lost_record in user_lost_records:
            try:
                # AI розширення
                expanded = await ai_expand_lost_record(lost_record, ai_function)
                if expanded:
                    # Створюємо неподтверджений запис
                    unconfirmed_record = create_unconfirmed_record(expanded)
                    if unconfirmed_record:
                        recovered_records.append(unconfirmed_record)
                        
            except Exception as e:
                log.error(f"Помилка обробки втраченого запису: {e}")
                continue
        
        return recovered_records
        
    except Exception as e:
        log.error(f"Помилка автовідновлення: {e}")
        return []

def load_training_data() -> List[Dict]:
    """Завантажити навчальні дані."""
    training_file = Path(LOGS_DIR).parent / "data" / "knowledge" / "training.json"
    if not training_file.exists():
        return []
    try:
        with open(training_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Помилка завантаження training.json: {e}")
        return []

def save_training_data(data: List[Dict]) -> bool:
    """Зберегти навчальні дані."""
    training_file = Path(LOGS_DIR).parent / "data" / "knowledge" / "training.json"
    try:
        with open(training_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log.error(f"Помилка збереження training.json: {e}")
        return False

def get_unconfirmed_records() -> List[Dict]:
    """Отримати всі непідтверджені записи."""
    try:
        training_data = load_training_data()
        unconfirmed = [r for r in training_data if r.get("status") == "unconfirmed"]
        return unconfirmed
    except Exception as e:
        log.error(f"Помилка отримання неподтверджених записів: {e}")
        return []

def confirm_record(record_id: int, user_id: int) -> bool:
    """Підтвердити відновлений запис."""
    try:
        training_data = load_training_data()
        
        for record in training_data:
            if record.get("id") == record_id and record.get("status") == "unconfirmed":
                # Переназначаємо позитивний ID
                max_confirmed_id = max([r.get("id", 0) for r in training_data if r.get("id", 0) > 0], default=0)
                record["id"] = max_confirmed_id + 1
                record["status"] = "confirmed"
                record["confirmed_by"] = user_id
                record["confirmed_at"] = datetime.now().isoformat()
                
                # Оновлюємо назву
                if "втрачений запис" in record.get("title", "").lower():
                    record["title"] = f"Відновлений запис {record['id']}"
                
                log.info(f"Підтверджено запис {record['id']} адміном {user_id}")
                return save_training_data(training_data)
        
        return False
        
    except Exception as e:
        log.error(f"Помилка підтвердження запису: {e}")
        return False

def reject_record(record_id: int, user_id: int) -> bool:
    """Відхилити відновлений запис."""
    try:
        training_data = load_training_data()
        training_data = [r for r in training_data if r.get("id") != record_id]
        
        log.info(f"Відхилено запис {record_id} адміном {user_id}")
        return save_training_data(training_data)
        
    except Exception as e:
        log.error(f"Помилка відхилення запису: {e}")
        return False