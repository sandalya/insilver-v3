#!/usr/bin/env python3
"""Переробка: 1 запис = 1 знання (не групи)."""

import json
import asyncio
from datetime import datetime
from pathlib import Path

async def simple_ai_improve(question, answer):
    """Просто покращити текст через AI без складного розширення."""
    try:
        from core.ai import ask_ai
        
        prompt = f"""Перефразуй цю відповідь для бота ювелірної майстерні InSilver. Зроби текст зрозумілішим і природнішим.

Питання клієнта: {question}

Поточна відповідь: {answer}

Завдання:
- Зроби відповідь більш людською і ввічливою
- Виправ граматичні помилки якщо є
- Зберегти всю важливу інформацію
- Додай 1-2 корисні деталі якщо доречно
- Відповідь має бути готова для надсилання клієнту

Відповідай тільки покращеним текстом, без коментарів."""

        improved = await ask_ai(189793675, prompt, [])
        return improved.strip()
        
    except Exception as e:
        print(f"⚠️ AI помилка: {e}")
        return answer  # Повертаємо оригінал якщо AI не працює

async def remake_knowledge():
    """Переробити групи на окремі записи."""
    
    # Очищуємо поточні записи
    training_file = Path("data/knowledge/training.json")
    
    # Завантажуємо стару базу знову
    old_file = Path("../insilver-v2/knowledge_base.json")
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    print(f"📚 Обробляю {len(old_data)} записів з v2...")
    
    new_records = []
    processed_count = 0
    
    for i, item in enumerate(old_data, 1):
        trigger = item.get("trigger", "").strip()
        response = item.get("response_text", "").strip()
        old_id = item.get("id", f"unknown_{i}")
        
        # Пропускаємо порожні або дуже короткі
        if not trigger or not response or len(response) < 10:
            print(f"⚠️ Пропускаю ID {old_id}: порожній або занадто короткий")
            continue
        
        print(f"[{processed_count + 1}] 🔄 {trigger[:50]}...")
        
        # Просте AI покращення
        improved_response = await simple_ai_improve(trigger, response)
        
        # Створюємо окремий запис
        new_record = {
            "id": -(processed_count + 1),  # Негативний = неподтверджений
            "title": f"FAQ: {trigger[:60]}..." if len(trigger) > 60 else f"FAQ: {trigger}",
            "created_by": 189793675,
            "created": datetime.now().isoformat(),
            "content": [
                {
                    "text": improved_response,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "media": [],
            "status": "unconfirmed",
            "migration_source": "insilver-v2",
            "original_id": old_id,
            "original_trigger": trigger,
            "ai_improved": True
        }
        
        # Обробляємо медіа якщо є
        if item.get("media"):
            for media_file in item["media"]:
                if isinstance(media_file, str):
                    # Старий формат
                    media_type = "photo" if any(ext in media_file for ext in ['.jpg', '.png']) else "file"
                    new_record["media"].append({
                        "type": media_type,
                        "path": f"../insilver-v2/{media_file}",
                        "caption": "",
                        "filename": Path(media_file).name
                    })
                elif isinstance(media_file, dict):
                    # Новий формат
                    new_record["media"].append({
                        "type": media_file.get("type", "photo"),
                        "path": f"../insilver-v2/{media_file.get('path', '')}",
                        "caption": "",
                        "filename": Path(media_file.get("path", "")).name
                    })
        
        new_records.append(new_record)
        processed_count += 1
        
        print(f"✅ Покращено: {len(improved_response)} символів")
    
    # Зберігаємо всі записи
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(new_records, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 Результат:")
    print(f"✅ Створено {len(new_records)} окремих записів")
    print(f"📂 Збережено: {training_file}")
    print(f"⚠️ Статус: неподтверджені - потрібне схвалення в /admin")
    
    return len(new_records)

if __name__ == "__main__":
    result = asyncio.run(remake_knowledge())
    print(f"\n🏁 Готово: {result} записів")