"""Система бекапів і відновлення для тренер режиму."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from core.config import LOGS_DIR, DATA_DIR

log = logging.getLogger("backup_system")

# Папка для бекапів
BACKUP_DIR = Path(LOGS_DIR) / "training_backups"
BACKUP_DIR.mkdir(exist_ok=True)

def backup_trainer_collection(user_id: int, collection: List[Dict]) -> Optional[str]:
    """Зберегти збірку тренера як бекап."""
    if not collection:
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"trainer_collection_{user_id}_{timestamp}.json"
        backup_path = BACKUP_DIR / backup_filename
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "collection_size": len(collection),
            "collection": collection,
            "type": "trainer_collection"
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        log.info(f"Збережено бекап збірки: {backup_filename}")
        return str(backup_path)
        
    except Exception as e:
        log.error(f"Помилка створення бекапу збірки: {e}")
        return None

def backup_training_record(record: Dict) -> Optional[str]:
    """Зберегти готовий навчальний запис як бекап."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"training_record_{record.get('id', 'unknown')}_{timestamp}.json"
        backup_path = BACKUP_DIR / backup_filename
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "record": record,
            "type": "training_record"
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        log.info(f"Збережено бекап запису: {backup_filename}")
        return str(backup_path)
        
    except Exception as e:
        log.error(f"Помилка створення бекапу запису: {e}")
        return None

def list_backup_files() -> List[Dict]:
    """Список всіх бекапних файлів."""
    backups = []
    
    try:
        for backup_file in sorted(BACKUP_DIR.glob("*.json"), reverse=True):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "timestamp": data.get("timestamp", ""),
                    "type": data.get("type", "unknown"),
                    "size": len(data.get("collection", [])) if data.get("type") == "trainer_collection" else 1,
                    "user_id": data.get("user_id"),
                    "record_id": data.get("record", {}).get("id") if data.get("type") == "training_record" else None
                })
                
            except (json.JSONDecodeError, KeyError) as e:
                log.warning(f"Пошкоджений бекап файл {backup_file.name}: {e}")
                continue
                
    except Exception as e:
        log.error(f"Помилка читання бекапів: {e}")
    
    return backups

def restore_from_backup(backup_path: str) -> Optional[Dict]:
    """Відновити дані з бекапу."""
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        log.info(f"Відновлено дані з бекапу: {Path(backup_path).name}")
        return backup_data
        
    except Exception as e:
        log.error(f"Помилка відновлення з бекапу {backup_path}: {e}")
        return None

def convert_backup_to_training_record(backup_data: Dict, user_id: int) -> Optional[Dict]:
    """Конвертувати бекап збірки в готовий навчальний запис."""
    if backup_data.get("type") != "trainer_collection":
        return None
    
    try:
        collection = backup_data.get("collection", [])
        if not collection:
            return None
        
        # Генеруємо запис як у handle_trainer_save_collection
        from bot.admin import load_training_data
        training_data = load_training_data()
        max_id = max([r.get("id", 0) for r in training_data], default=0)
        new_id = max_id + 1
        
        record = {
            "id": new_id,
            "title": f"Відновлено з бекапу {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "created_by": user_id,
            "created": datetime.now().isoformat(),
            "content": [],
            "media": [],
            "restored_from_backup": backup_data.get("timestamp", "")
        }
        
        # Додаємо контент
        for item in collection:
            content_item = {
                "text": item["text"],
                "timestamp": item["timestamp"]
            }
            record["content"].append(content_item)
        
        log.info(f"Конвертовано бекап в навчальний запис ID {new_id}")
        return record
        
    except Exception as e:
        log.error(f"Помилка конвертації бекапу: {e}")
        return None

def emergency_log_trainer_data(user_id: int, data_type: str, data: any):
    """Екстрене логування даних тренера (для діагностики втрат)."""
    try:
        timestamp = datetime.now().isoformat()
        log_file = BACKUP_DIR / "emergency_log.jsonl"
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "data_type": data_type,
            "data": data
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        log.error(f"Помилка екстреного логування: {e}")

def search_emergency_logs(user_id: int, minutes: int = 60) -> List[Dict]:
    """Пошук екстрених логів для користувача за останні N хвилин."""
    try:
        log_file = BACKUP_DIR / "emergency_log.jsonl"
        if not log_file.exists():
            return []
        
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        results = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    if (entry_time >= cutoff_time and 
                        entry.get("user_id") == user_id):
                        results.append(entry)
                        
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)
        
    except Exception as e:
        log.error(f"Помилка пошуку екстрених логів: {e}")
        return []