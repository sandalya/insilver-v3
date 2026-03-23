#!/usr/bin/env python3
"""Просто розбити записи на окремі (без AI)."""

import json
from datetime import datetime
from pathlib import Path

def split_knowledge():
    """Розбити кожен запис окремо."""
    
    # Завантажуємо стару базу
    old_file = Path("../insilver-v2/knowledge_base.json")
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    print(f"📚 Розбиваю {len(old_data)} записів...")
    
    new_records = []
    
    for i, item in enumerate(old_data, 1):
        trigger = item.get("trigger", "").strip()
        response = item.get("response_text", "").strip()
        old_id = item.get("id", f"unknown_{i}")
        created = item.get("created", "")
        
        # Пропускаємо порожні або дуже короткі
        if not trigger or not response or len(response) < 10:
            print(f"⚠️ Пропускаю ID {old_id}: порожній")
            continue
        
        # Створюємо окремий запис
        new_record = {
            "id": -(i),  # Негативний = неподтверджений
            "title": f"{trigger[:60]}..." if len(trigger) > 60 else trigger,
            "created_by": 189793675,
            "created": datetime.now().isoformat(),
            "content": [
                {
                    "text": response,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "media": [],
            "status": "unconfirmed",
            "migration_source": "insilver-v2",
            "original_id": old_id,
            "original_created": created
        }
        
        # Обробляємо медіа
        if item.get("media"):
            for media_file in item["media"]:
                if isinstance(media_file, str) and media_file:
                    # Старий формат - просто шлях
                    media_type = "photo" if any(ext in media_file for ext in ['.jpg', '.png', '.jpeg']) else "file"
                    new_record["media"].append({
                        "type": media_type,
                        "path": f"../insilver-v2/{media_file}",
                        "caption": "",
                        "filename": Path(media_file).name
                    })
                elif isinstance(media_file, dict) and media_file.get("path"):
                    # Новий формат
                    new_record["media"].append({
                        "type": media_file.get("type", "photo"),
                        "path": f"../insilver-v2/{media_file.get('path')}",
                        "caption": "",
                        "filename": Path(media_file.get("path", "")).name
                    })
        
        new_records.append(new_record)
        print(f"[{len(new_records)}] ✅ {trigger[:50]}...")
    
    # Зберігаємо
    training_file = Path("data/knowledge/training.json")
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(new_records, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 Результат:")
    print(f"✅ Створено {len(new_records)} окремих записів")
    print(f"📂 Файл: {training_file}")
    print(f"⚠️ Статус: неподтверджені")
    
    return len(new_records)

if __name__ == "__main__":
    result = split_knowledge()
    print(f"\n🏁 Готово: {result} записів")