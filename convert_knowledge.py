#!/usr/bin/env python3
"""Швидка конвертація знань з v2 до v3 формату."""

import json
from datetime import datetime
from pathlib import Path

def convert_knowledge():
    """Конвертувати стару базу в новий формат."""
    
    # Завантажуємо стару базу
    old_file = Path("../insilver-v2/knowledge_base.json")
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    # Групуємо по темах
    groups = {}
    
    for item in old_data:
        # Визначаємо групу по ключових словах в trigger
        trigger = item.get("trigger", "").lower()
        response = item.get("response_text", "")
        
        if any(word in trigger for word in ["замовлення", "оформ", "потрібно", "вказати"]):
            group = "ordering"
        elif any(word in trigger for word in ["бісмарк", "165", "грн/г"]):
            group = "bismarak_pricing" 
        elif any(word in trigger for word in ["карабін", "коробочка", "застібка", "замок"]):
            group = "clasps"
        elif any(word in trigger for word in ["покриття", "чорніння", "родіювання", "біле срібло"]):
            group = "coatings"
        elif any(word in trigger for word in ["час", "термін", "тижні", "виготовлення"]):
            group = "timing"
        elif any(word in trigger for word in ["замір", "виміряти", "руку", "кулон"]):
            group = "measurements"
        else:
            group = "general"
        
        if group not in groups:
            groups[group] = {
                "items": [],
                "media_files": []
            }
        
        groups[group]["items"].append({
            "trigger": item.get("trigger", ""),
            "response": response,
            "media": item.get("media", []),
            "created": item.get("created", "")
        })
        
        # Збираємо медіа файли
        if item.get("media"):
            groups[group]["media_files"].extend(item["media"])

    # Назви груп
    group_titles = {
        "ordering": "Оформлення замовлення та параметри",
        "bismarak_pricing": "Плетіння Бісмарк - ціни та розрахунки", 
        "clasps": "Застібки - карабін та коробочка",
        "coatings": "Покриття та обробка виробів",
        "timing": "Терміни виготовлення",
        "measurements": "Заміри для браслетів та кулонів",
        "general": "Загальна інформація"
    }
    
    # Створюємо нові записи
    new_records = []
    record_id = 1
    
    for group_key, group_data in groups.items():
        if not group_data["items"]:
            continue
            
        # Об'єднуємо всі відповіді в одну
        combined_content = []
        for item in group_data["items"]:
            if item["trigger"] and item["response"]:
                combined_content.append(f"Q: {item['trigger']}\nA: {item['response']}")
        
        content_text = "\n\n".join(combined_content)
        
        # Конвертуємо медіа
        converted_media = []
        seen_paths = set()
        for media_file in group_data["media_files"]:
            # Отримуємо шлях для перевірки дублікатів
            if isinstance(media_file, str):
                file_path = media_file
            elif isinstance(media_file, dict):
                file_path = media_file.get("path", "")
            else:
                continue
            
            # Перевіряємо чи не дублікат
            if file_path in seen_paths:
                continue
            seen_paths.add(file_path)
            
            if isinstance(media_file, str):
                # Старий формат - просто шлях
                media_type = "photo" if any(ext in media_file for ext in ['.jpg', '.png']) else "file"
                converted_media.append({
                    "type": media_type,
                    "path": f"../insilver-v2/{media_file}",
                    "caption": "",
                    "filename": Path(media_file).name
                })
            elif isinstance(media_file, dict):
                # Новий формат
                converted_media.append({
                    "type": media_file.get("type", "photo"),
                    "path": f"../insilver-v2/{media_file.get('path', '')}",
                    "caption": "",
                    "filename": Path(media_file.get("path", "")).name
                })
        
        # Створюємо запис
        new_record = {
            "id": -record_id,  # Негативний ID = неподтверджений
            "title": group_titles.get(group_key, f"Група {group_key}"),
            "created_by": 189793675,
            "created": datetime.now().isoformat(),
            "content": [
                {
                    "text": content_text,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "media": converted_media,
            "status": "unconfirmed",
            "migration_source": "insilver-v2",
            "original_count": len(group_data["items"])
        }
        
        new_records.append(new_record)
        record_id += 1
    
    # Зберігаємо
    training_file = Path("data/knowledge/training.json")
    existing_data = []
    if training_file.exists():
        with open(training_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    existing_data.extend(new_records)
    
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Конвертовано {len(new_records)} записів")
    print("📋 Групи:")
    for record in new_records:
        print(f"  - {record['title']} (ID: {record['id']}, оригіналів: {record['original_count']})")
    
    print(f"\n💾 Збережено в: {training_file}")
    print("⚠️  Статус: 'unconfirmed' - потрібне підтвердження в /admin")
    
    return len(new_records)

if __name__ == "__main__":
    result = convert_knowledge()
    print(f"\n🎯 Результат: {result} записів створено")