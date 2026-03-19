"""
Витягування контексту замовлення з історії чату.
Використовується для автозаповнення анкети.
"""
import re


def extract_weaving_from_text(text: str) -> str:
    weavings = ['бісмарк', 'якір', 'панцир', 'пітон', 'фігаро', 'рамзес',
                'козацьк', 'фараон', 'emperador', 'кардинал', 'водоспад',
                'тризуб', 'лисячий', 'візант', 'біт']
    text_lower = text.lower()
    for weaving in weavings:
        if weaving in text_lower:
            return weaving
    return ''


def extract_weight_from_text(text: str) -> float | None:
    patterns = [
        r'(\d+(?:\.\d+)?)\s*г(?!рн)',
        r'маса\s*(?:~)?\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*грам',
    ]
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                pass
    return None


def extract_length_from_text(text: str) -> int | None:
    patterns = [
        r'(\d+)\s*см',
        r'довжина\s*(?:~)?\s*(\d+)',
        r'(\d+)\s*сантиметр',
    ]
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    return None


def extract_product_type_from_text(text: str) -> str:
    types = ['браслет', 'ланцюжок', 'кулон', 'хрестик', 'ладанка', 'перстень', 'обручка', 'набір']
    text_lower = text.lower()
    for t in types:
        if t in text_lower:
            return t
    return ''


def extract_order_context(chat_history: list) -> dict:
    """
    Витягує з історії чату все що може бути корисним для анкети.
    Повертає тільки непусті поля.
    """
    full_text = '\n'.join([
        msg.get('content', '')
        for msg in chat_history
        if msg.get('role') == 'user'
    ])
    full_text_lower = full_text.lower()

    context = {}

    # Тип виробу
    product_type = extract_product_type_from_text(full_text)
    if product_type:
        context['type'] = product_type

    # Плетіння
    weaving = extract_weaving_from_text(full_text)
    if weaving:
        context['weaving'] = weaving

    # Вага
    weight = extract_weight_from_text(full_text)
    if weight:
        context['weight'] = f'{weight}г'

    # Довжина
    length = extract_length_from_text(full_text)
    if length:
        context['length'] = f'{length}см'

    # Покриття
    coatings = {'чорніння': '⚫️ Чорніння', 'родіювання': '✨ Родіювання +95грн/г'}
    for key, val in coatings.items():
        if key in full_text_lower:
            context['plating'] = val
            break

    # Застібка
    clasps = {'карабін': '🔗 Карабін', 'коробочка': '📦 Коробочка 600грн'}
    for key, val in clasps.items():
        if key in full_text_lower:
            context['clasp'] = val
            break

    return context


def has_order_intent(text: str) -> bool:
    """
    Перевіряє чи є в тексті чіткий намір оформити замовлення.
    Навмисно вузький — щоб не спрацьовував на просте питання ціни.
    """
    strong_intents = [
        'оформити замовлення', 'зробити замовлення', 'хочу замовити',
        'готовий замовити', 'готова замовити', 'беру', 'купую',
        'оформляємо', 'давай оформимо', 'як замовити',
    ]
    text_lower = text.lower()
    return any(intent in text_lower for intent in strong_intents)
