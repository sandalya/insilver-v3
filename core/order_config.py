"""
Конфігурація анкети замовлення.
Для кожного типу виробу — свої кроки.
"""

PRODUCT_CONFIGS = {
    "ланцюжок": {
        "emoji": "⛓️",
        "steps": [
            {
                "key": "weaving",
                "text": "Плетіння?",
                "hint": "ℹ️ Якір, Бісмарк, Рамзес, Візантія, Водоспад, Панцир, Фараон, Лисячий хвіст, Кардинал",
                "options": ["Якір", "Бісмарк", "Рамзес", "Візантія", "Водоспад", "Панцир", "Фараон", "Лисячий хвіст", "Інше"],
                "show_photos": True,
            },
            {
                "key": "length",
                "text": "Довжина (см)?",
                "hint": "ℹ️ Напишіть цифру або виберіть",
                "options": ["40см", "45см", "50см", "55см", "60см", "65см", "70см", "75см", "Інше"],
                "show_measure_button": True,
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "hint": "ℹ️ Напишіть: 50г, 100г або \'не знаю\'",
                "options": None,
            },
            {
                "key": "plating",
                "text": "Покриття?",
                "options": ["⚪️ Срібло біле", "⚫️ Чорніння", "✨ Родіювання +95грн/г", "✏️ Інше"],
                "show_photos": True,
            },
            {
                "key": "clasp",
                "text": "Застібка?",
                "options": ["🔗 Карабін", "📦 Коробочка 600грн", "📦 Коробочка XL 1500грн", "✏️ Інше"],
                "show_photos": True,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✍️ Гравіювання 500-700грн", "✏️ Інше"],
            },
        ],
    },

    "браслет": {
        "emoji": "📿",
        "steps": [
            {
                "key": "weaving",
                "text": "Плетіння?",
                "hint": "ℹ️ Бісмарк, Рамзес, Якір, Панцир, Фараон, Козацька та інші",
                "options": ["Бісмарк", "Рамзес", "Якір", "Панцир", "Фараон", "Козацька", "Візантія", "Тризуб", "Інше"],
                "show_photos": True,
            },
            {
                "key": "length",
                "text": "Розмір (см)?",
                "hint": "ℹ️ Обхват руки",
                "options": ["18см", "19см", "20см", "21см", "22см", "23см", "24см", "25см", "Інше"],
                "show_measure_button": True,
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "options": None,
            },
            {
                "key": "plating",
                "text": "Покриття?",
                "options": ["⚪️ Срібло біле", "⚫️ Чорніння", "✨ Родіювання +95грн/г", "✏️ Інше"],
                "show_photos": True,
            },
            {
                "key": "clasp",
                "text": "Застібка?",
                "options": ["🔗 Карабін", "📦 Коробочка 600грн", "📦 Коробочка XL 1500грн", "✏️ Інше"],
                "show_photos": True,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✍️ Гравіювання 500-700грн", "✏️ Інше"],
            },
        ],
    },

    "хрестик": {
        "emoji": "✝️",
        "steps": [
            {
                "key": "cross_type",
                "text": "Тип хреста?",
                "options": ["✝️ Класичні", "✨ Із покриттям", "🙏 Із розп\'яттям", "⛪ Католицькі"],
                "show_photos": True,
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "hint": "ℹ️ Напишіть: 5г, 10г або \'не знаю\'",
                "options": None,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✏️ Інше"],
            },
        ],
    },

    "кулон": {
        "emoji": "🔮",
        "steps": [
            {
                "key": "collection",
                "text": "Колекція/Мотив?",
                "options": ["Інші мотиви", "Memento Mori", "Зодіак", "✏️ Інше"],
                "show_photos": True,
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "options": None,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✏️ Інше"],
            },
        ],
    },

    "перстень": {
        "emoji": "👑",
        "steps": [
            {
                "key": "motif",
                "text": "Мотив/Стиль?",
                "options": ["Memento Mori", "Оберіг / Символ", "Інші", "З чорненням"],
                "show_photos": True,
            },
            {
                "key": "size",
                "text": "Розмір пальця?",
                "hint": "ℹ️ Напишіть або виберіть",
                "options": ["15", "16", "17", "18", "19", "20", "21", "22", "Інше"],
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "options": None,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✏️ Інше"],
            },
        ],
    },

    "обручка": {
        "emoji": "💍",
        "steps": [
            {
                "key": "style",
                "text": "Стиль?",
                "options": ["Класичні", "З камінням", "Memento Mori", "З написом"],
                "show_photos": True,
            },
            {
                "key": "size",
                "text": "Розмір пальця?",
                "options": ["15", "16", "17", "18", "19", "20", "21", "22", "Інше"],
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "options": None,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✍️ Гравіювання 500-700грн", "✏️ Інше"],
            },
        ],
    },

    "набір": {
        "emoji": "🎁",
        "steps": [
            {
                "key": "set_composition",
                "text": "Склад набору?",
                "options": ["Браслет+Ланцюжок", "Ланцюжок+Кулон", "Авторський комбо", "✏️ Інше"],
            },
            {
                "key": "weight",
                "text": "Загальна маса (г)?",
                "options": None,
            },
            {
                "key": "note",
                "text": "Додатково? (опціонально)",
                "options": ["➖ Немає", "✏️ Інше"],
            },
        ],
    },
}

# Спільні кроки в кінці для всіх типів
COMMON_STEPS = [
    {
        "key": "contact",
        "text": "Ваше імʼя та телефон?",
        "hint": "ℹ️ Наприклад: Іван +38099 123 45 67",
        "options": None,
    },
    {
        "key": "city",
        "text": "Місто доставки?",
        "hint": "ℹ️ Наприклад: Київ",
        "options": None,
    },
    {
        "key": "np_office",
        "text": "Номер відділення Нової Пошти?",
        "hint": "ℹ️ Наприклад: 42 або «Поштомат №1234»",
        "options": None,
    },
    {
        "key": "comment",
        "text": "Щось уточнити? (опціонально)",
        "options": ["➖ Немає", "✍️ Є коментар"],
    },
]

# Крок вибору типу (перший в режимі B)
TYPE_STEP = {
    "key": "type",
    "text": "Що замовляємо?",
    "hint": "ℹ️ Виберіть тип виробу",
    "options": ["⛓️ Ланцюжок", "📿 Браслет", "✝️ Хрестик", "🔮 Кулон", "💍 Обручка", "👑 Перстень", "🎁 Набір", "✏️ Інше"],
}

TYPE_MAP = {
    "⛓️ ланцюжок": "ланцюжок",
    "📿 браслет": "браслет",
    "✝️ хрестик": "хрестик",
    "🔮 кулон": "кулон",
    "💍 обручка": "обручка",
    "👑 перстень": "перстень",
    "🎁 набір": "набір",
}


def normalize_type(raw: str) -> str:
    """Нормалізує тип з кнопки або тексту → ключ для PRODUCT_CONFIGS."""
    normalized = raw.lower().strip()
    if normalized in TYPE_MAP:
        return TYPE_MAP[normalized]
    # Пробуємо знайти по слову
    for key in PRODUCT_CONFIGS:
        if key in normalized:
            return key
    return "інше"


def get_steps_for_type(product_type: str, prefilled: dict = None) -> list:
    """
    Повертає кроки для типу виробу, пропускаючи вже заповнені.

    Args:
        product_type: нормалізований тип (ланцюжок, браслет...)
        prefilled: дані витягнуті з розмови

    Returns:
        Список кроків
    """
    prefilled = prefilled or {}
    config = PRODUCT_CONFIGS.get(product_type)

    if config:
        all_steps = config["steps"] + COMMON_STEPS
    else:
        all_steps = [
            {
                "key": "description",
                "text": "Опишіть що замовляєте?",
                "options": None,
            },
            {
                "key": "weight",
                "text": "Маса (г)?",
                "options": None,
            },
        ] + COMMON_STEPS

    # Пропускаємо вже заповнені кроки
    return [s for s in all_steps if not prefilled.get(s["key"])]


def get_keyboard(step: dict, step_index: int = 0) -> list | None:
    """
    Повертає список рядів кнопок для кроку.
    Повертає None якщо крок — текстовий ввід.

    Returns:
        [[InlineKeyboardButton, ...], ...] або None
    """
    from telegram import InlineKeyboardButton

    options = step.get("options")
    if not options:
        return None

    step_key = step["key"]
    buttons = []

    # Кнопки опцій (по 2 в ряду)
    for i in range(0, len(options), 2):
        row = []
        for j in range(2):
            if i + j < len(options):
                opt = options[i + j]
                idx = i + j
                row.append(InlineKeyboardButton(opt, callback_data=f"f:{step_key}:{idx}"))
        buttons.append(row)

    # Кнопка "Як заміряти" (для кроків довжини/розміру)
    if step.get("show_measure_button"):
        buttons.append([InlineKeyboardButton("📏 Як заміряти?", callback_data="f:measure")])

    # Службові кнопки
    if step_index > 0:
        buttons.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="f:back"),
            InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel"),
        ])
    else:
        buttons.append([InlineKeyboardButton("❌ Скасувати", callback_data="f:cancel")])

    return buttons


def format_step_message(step: dict, step_index: int, total_steps: int, filled: dict) -> str:
    """Форматує текст кроку з прогресом і вже заповненим."""
    key_names = {
        "type": "Тип", "weaving": "Плетіння", "style": "Стиль",
        "cross_type": "Тип хреста", "collection": "Колекція",
        "motif": "Мотив", "length": "Довжина", "size": "Розмір",
        "weight": "Маса", "plating": "Покриття", "clasp": "Застібка",
        "note": "Додатково", "set_composition": "Склад",
        "contact": "Контакт", "comment": "Коментар",
    }

    text = f"[{step_index + 1}/{total_steps}] {step['text']}"
    if step.get("hint"):
        text += f"\n{step['hint']}"

    if filled:
        text += "\n\n📝 Вже вказано:"
        for key, val in filled.items():
            if val and not key.startswith("_"):
                text += f"\n  • {key_names.get(key, key)}: {val}"

    return text
