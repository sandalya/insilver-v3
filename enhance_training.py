#!/usr/bin/env python3
"""
🧠 Enhanced AI Training - додавання реальних клієнтських сценаріїв в training.json
На основі 7 партій скрінів та real_client_cases.py
"""

import json
import sys
from datetime import datetime
import os

# Додаємо tests в path
sys.path.append('tests')
from real_client_cases import REAL_CLIENT_CASES

def load_current_training():
    """Завантажити поточний training.json"""
    with open('data/knowledge/training.json', encoding='utf-8') as f:
        return json.load(f)

def get_next_id(training_data):
    """Отримати наступний ID"""
    return max([record['id'] for record in training_data], default=0) + 1

def create_training_record(record_id, title, answer, created_by=189793675):
    """Створити запис training.json"""
    now = datetime.now().isoformat()
    return {
        "id": record_id,
        "title": title,
        "created_by": created_by,
        "created": now,
        "content": [
            {
                "text": answer,
                "timestamp": now
            }
        ]
    }

def enhance_training():
    """Головна функція покращення training.json"""
    print("🧠 Enhanced AI Training - розширення knowledge base")
    print("=" * 60)
    
    # Завантажити поточні дані
    current_training = load_current_training()
    print(f"📋 Поточні записи: {len(current_training)}")
    
    # Отримати high-priority кейси
    high_priority_cases = [case for case in REAL_CLIENT_CASES if case.get('priority') == 'high']
    print(f"🎯 High-priority cases: {len(high_priority_cases)}")
    
    next_id = get_next_id(current_training)
    new_records = []
    
    # Додати high-priority кейси з real_client_cases.py
    for case in high_priority_cases:
        question = case['client_question']
        category = case['category']
        
        # Створити відповідь на основі expected_elements та контексту
        expected_elements = case.get('expected_elements', [])
        should_mention = case.get('should_mention', [])
        context = case.get('context', '')
        
        # Генерувати відповідь в залежності від категорії
        answer = generate_answer_for_case(case)
        
        record = create_training_record(
            record_id=next_id,
            title=question,
            answer=answer
        )
        
        new_records.append(record)
        next_id += 1
        print(f"✅ Додано: {question[:50]}... ({category})")
    
    # Додати нові сценарії з партій 5-7 скрінів
    additional_scenarios = get_additional_scenarios()
    for scenario in additional_scenarios:
        record = create_training_record(
            record_id=next_id,
            title=scenario['question'],
            answer=scenario['answer']
        )
        new_records.append(record)
        next_id += 1
        print(f"✅ Додано: {scenario['question'][:50]}...")
    
    # Об'єднати дані
    enhanced_training = current_training + new_records
    
    # Зберегти розширений training.json
    with open('data/knowledge/training.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_training, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"🎉 ГОТОВО! Розширено training.json:")
    print(f"   Було: {len(current_training)} записів")
    print(f"   Додано: {len(new_records)} нових")
    print(f"   Стало: {len(enhanced_training)} записів")
    print(f"   Покращення: {len(new_records)/len(current_training)*100:.0f}%")

def generate_answer_for_case(case):
    """Генерувати відповідь для кейсу"""
    category = case['category']
    elements = case.get('expected_elements', [])
    context = case.get('context', '')
    
    if category == 'ціни':
        if 'тризуб' in case['client_question'].lower():
            return "Плетіння Тризуб коштує 170 грн за грам готового виробу. Замок карабін входить у вартість, замок-коробочка +600 грн доплати. Гравірування тризуба +500 грн. Мінімальна маса 50-55 грам. При масі 60 грам: 60×170+600+500 = 11,300 грн."
        elif 'граненій якір' in case['client_question'].lower():
            return "Плетіння Граненій якір коштує 155 грн за грам готового виробу з замком карабіном. Замок-коробочка по доплаті 600 грн. При масі 50г вартість складе 7,750 грн."
        else:
            return "Радо допоможу з розрахунком вартості! Вкажіть, будь ласка, тип плетіння і бажану масу виробу. Ціни залежать від плетіння: Тризуб 170грн/г, Бісмарк 165грн/г, Граненій якір 155грн/г. Подивіться наш каталог з прикладами!"
    
    elif category == 'лом':
        return "Приймаємо лом срібла 925 проби по 85-87 грн за грам. Зараховуємо повну вартість в рахунок нового замовлення. Відправка лому - перед початком виготовлення, щоб зайве не лежало в сейфі."
    
    elif category == 'плетіння':
        return "Плетіння Граненій якір коштує 155 грн за грам готового виробу з замком карабіном. При довжині 60см та масі 50г вартість складе 7,750 грн. Замок-коробочка по доплаті 600 грн."
    
    elif category == 'персоналізація':
        return "Покриття можливе: чорніння (безкоштовно) або родіювання (+95грн/г від маси виробу). Позолота наразі недоступна. Замки: карабін (входить у вартість) або коробочка (+600 грн). Гравірування +500 грн."
    
    elif category == 'виміри':
        return "Для точного розміру браслета: обгорніть руку сантиметром по кісточці на зап'ясті щільно прилягаючи, без зайвого натягу. Це буде розмір від якого майстер відштовхуватиметься при виготовленні. Додаємо 2-3см запас для компенсації товщини виробу."
    
    elif category == 'оплата':
        return "Працюємо офіційно. Оплату на картку не приймаємо - тільки за реквізитами на рахунок ФОП. Після підтвердження замовлення надам IBAN для предоплати. Після оплати прохання сповістити надавши квитанцію або скріншот."
    
    elif category == 'каталог':
        return "Радо надішлю каталог! Про який саме виріб було ваше питання? Який розмір вас цікавить? У нас є кільця, браслети, ланцюжки різних плетінь. Після перегляду каталогу зможу підрахувати точну вартість."
    
    elif category == 'комбіновані':
        return "Для комбінованого замовлення (новий виріб + здача лому) розрахунок: вартість нового виробу мінус зарахування вашого срібла. Приймаємо лом 925° по 87 грн/г. Формула: вартість виробу - (маса лому × 87 грн)."
    
    elif category == 'тайминг':
        return "Відправку лому координуємо з початком виготовлення. Надам адресу за кілька днів до початку роботи, щоб зайве в нас по часу не лежало в сейфі. Це оптимізує процес і мінімізує ризики."
    
    elif category == 'наявність':
        return "Перепрошую, не впевнений чи є точно в наявності (оскільки вихідний). Якщо немає - потрібно буде виготовляти. Терміни виготовлення 2-3 тижні. Чи маєте час зачекати на виготовлення?"
    
    else:
        # Загальна відповідь  
        return "Дякую за запит! Радо допоможу з консультацією. Уточніть, будь ласка, деталі або подивіться наш каталог. Готовий відповісти на питання про ціни, терміни, характеристики виробів."

def get_additional_scenarios():
    """Додаткові сценарії з нових скрінів (партії 5-7)"""
    return [
        {
            "question": "доставка по місту, яка адреса відділення новою поштою",
            "answer": "Доставка здійснюється Новою поштою в будь-яке відділення України. По готовності вишлемо фото готового виробу на вагах та кінцевий розрахунок по фактичній масі. Вкажіть ваше місто і номер відділення для відправки."
        },
        {
            "question": "покажіть готовий виріб на вагах, яка точна маса вийшла",
            "answer": "Обов'язково! По готовності надсилаю фото виробу на електронних вагах з точною масою. Кінцевий розрахунок по фактичній вазі готового виробу. Це забезпечує повну прозорість процесу виготовлення."
        },
        {
            "question": "застібка карабін стандартна чи можна зробити по ширині браслету",
            "answer": "Застібка карабін стандартна входить у вартість. Якщо потрібна застібка по ширині браслету - це можливо зробити за індивідуальним замовленням. Уточню технічну можливість та доплату для вашого конкретного виробу."
        },
        {
            "question": "цепочка рамзес 60см 70г з чорнінням терміни виготовлення",
            "answer": "Ланцюжок Рамзес 60см, орієнтовна маса 70г з покриттям чорнінням. Терміни виготовлення 2-3 тижні. В наявності немає, потрібно виготовляти. Ціну розрахую після уточнення точних параметрів."
        },
        {
            "question": "синхронізація відправки лому з початком роботи чому так важливо",
            "answer": "Ми координуємо отримання лому з початком виготовлення для оптимізації процесу. Надаємо адресу за кілька днів до початку роботи, щоб зайве в нас по часу не лежало в сейфі. Це мінімізує ризики та пришвидшує процес."
        }
    ]

if __name__ == "__main__":
    enhance_training()