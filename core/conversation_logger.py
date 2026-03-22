"""Логування розмов консультанта для аналізу."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from core.config import LOGS_DIR

# Окремий логер для розмов
conversation_log = logging.getLogger("conversations")
conversation_log.setLevel(logging.INFO)

# Створити папку якщо не існує
logs_path = Path(LOGS_DIR)
logs_path.mkdir(exist_ok=True)

# Файл для розмов
conversation_file = logs_path / "conversations.log"
conv_handler = logging.FileHandler(conversation_file, encoding='utf-8')
conv_handler.setLevel(logging.INFO)

# Формат: простий для читання людьми
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
conv_handler.setFormatter(formatter)
conversation_log.addHandler(conv_handler)
conversation_log.propagate = False  # Не дублювати в основні логи

# JSON файл для структурованого аналізу
json_file = logs_path / "conversations.jsonl"

def log_user_message(user_id: int, username: str, message: str, found_items: int = 0):
    """Логувати повідомлення від користувача."""
    try:
        # Читабельний лог
        conversation_log.info(f"USER {user_id} ({username}): {message}")
        
        # JSON лог для аналізу
        json_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user_message",
            "user_id": user_id,
            "username": username,
            "message": message,
            "catalog_matches": found_items
        }
        
        with open(json_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        logging.getLogger("conversation_logger").error(f"Помилка логування user message: {e}")

def log_bot_response(user_id: int, username: str, response: str, ai_time: float = 0, with_photos: bool = False):
    """Логувати відповідь бота."""
    try:
        # Читабельний лог
        response_preview = response[:200] + "..." if len(response) > 200 else response
        extras = []
        if ai_time > 0:
            extras.append(f"AI: {ai_time:.2f}s")
        if with_photos:
            extras.append("з фото")
        
        extra_info = f" [{', '.join(extras)}]" if extras else ""
        conversation_log.info(f"BOT -> {user_id} ({username}): {response_preview}{extra_info}")
        
        # JSON лог для аналізу
        json_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "bot_response", 
            "user_id": user_id,
            "username": username,
            "response": response,
            "ai_processing_time": ai_time,
            "with_photos": with_photos,
            "response_length": len(response)
        }
        
        with open(json_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        logging.getLogger("conversation_logger").error(f"Помилка логування bot response: {e}")

def log_order_action(user_id: int, username: str, action: str, details: Optional[dict] = None):
    """Логувати дії пов'язані з замовленням."""
    try:
        conversation_log.info(f"ORDER {user_id} ({username}): {action}")
        
        json_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "order_action",
            "user_id": user_id,
            "username": username,
            "action": action,
            "details": details or {}
        }
        
        with open(json_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        logging.getLogger("conversation_logger").error(f"Помилка логування order action: {e}")

def log_error_interaction(user_id: int, username: str, error: str, context: str = ""):
    """Логувати помилки в розмові."""
    try:
        conversation_log.error(f"ERROR {user_id} ({username}): {error} | Context: {context}")
        
        json_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "user_id": user_id,
            "username": username,
            "error": error,
            "context": context
        }
        
        with open(json_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        logging.getLogger("conversation_logger").error(f"Помилка логування error: {e}")

# Допоміжні функції для аналізу
def get_conversation_stats(hours: int = 24) -> dict:
    """Базова статистика розмов за останні N годин."""
    try:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        
        stats = {
            "total_messages": 0,
            "unique_users": set(),
            "bot_responses": 0,
            "orders": 0,
            "errors": 0,
            "avg_response_time": 0,
            "response_times": []
        }
        
        if not json_file.exists():
            return {k: list(v) if isinstance(v, set) else v for k, v in stats.items()}
        
        with open(json_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    if entry_time < cutoff:
                        continue
                        
                    if entry["type"] == "user_message":
                        stats["total_messages"] += 1
                        stats["unique_users"].add(entry["user_id"])
                    elif entry["type"] == "bot_response":
                        stats["bot_responses"] += 1
                        if entry.get("ai_processing_time", 0) > 0:
                            stats["response_times"].append(entry["ai_processing_time"])
                    elif entry["type"] == "order_action":
                        stats["orders"] += 1
                    elif entry["type"] == "error":
                        stats["errors"] += 1
                        
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        # Підрахувати середній час відповіді
        if stats["response_times"]:
            stats["avg_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
        
        # Конвертувати set в list для JSON
        stats["unique_users"] = len(stats["unique_users"])  # Тільки кількість
        del stats["response_times"]  # Видалити робочий список
        
        return stats
        
    except Exception as e:
        logging.getLogger("conversation_logger").error(f"Помилка отримання статистики: {e}")
        return {"error": str(e)}