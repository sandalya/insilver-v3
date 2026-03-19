# InSilver v3 — DEV CHECKPOINT
**Дата:** 2026-03-19
**Статус:** Фаза 1+2+3.1+3.2 ЗАВЕРШЕНА

## ЩО ЗРОБЛЕНО СЬОГОДНІ

### Фаза 3.1 — Базова форма замовлення
- `bot/order.py` — ConversationHandler режим A: ім'я → телефон → місто → коментар
- Кнопка "🛒 Замовити" під кожним товаром (inline)
- Кнопка "❌ Скасувати" в флоу
- Замовлення зберігаються в `data/orders/orders.json`
- Сповіщення Владу з кнопкою "💬 Написати клієнту"
- Фікс `OWNER_CHAT_ID` в `core/config.py`
- Фікс `Button_data_invalid` — індекс замість URL в callback_data (`o:{idx}`)

### Фаза 3.2 — Розширена анкета
- `core/order_context.py` — витягує з розмови: тип, плетіння, вагу, довжину, покриття, застібку
- `core/order_config.py` — конфіг анкети для 7 типів виробів (ланцюжок, браслет, хрестик, кулон, перстень, обручка, набір) + спільні кроки
- `bot/order.py` — режим B: повна анкета з автозаповненням з розмови, кнопка "Назад", прогрес [1/6]
- Кнопка "📋 Оформити замовлення" під товарами і при intent detection
- `/order` команда запускає повну анкету
- Фікс конфлікту: під час замовлення `handle_message` не втручається
- Фікс зависання: `B_STEP` тепер приймає і текстовий ввід і кнопки

### Фікси каталогу
- `core/catalog.py` — decode HTML entities (`&quot;` → `"`)
- Додані синоніми множини: ланцюжки, браслети, хрестики, печатки
- Пошук тепер правильно знаходить товари по категорії

## СТАН СИСТЕМИ
- Бот: systemd insilver-v3 — active (running)
- Модель: claude-haiku-4-5-20251001
- Каталог: data/site_catalog.json (484 товари)
- Фото: data/photos/site/ (2675 файлів)

## СТРУКТУРА ПРОЕКТУ
```
insilver-v3/
├── core/
│   ├── config.py         — налаштування + OWNER_CHAT_ID
│   ├── lock.py           — захист від дублікатів
│   ├── prompt.py         — системний промпт
│   ├── ai.py             — Anthropic API (haiku)
│   ├── catalog.py        — пошук + html decode
│   ├── order_context.py  — витяг даних з розмови
│   └── order_config.py   — конфіг анкети по типах виробів
├── bot/
│   ├── client.py         — handlers + фото + кнопки
│   └── order.py          — ConversationHandler (режим A + B)
├── scripts/
│   ├── scrape_site.py
│   └── download_photos.py
├── data/
│   ├── site_catalog.json
│   ├── photos/site/
│   ├── orders/orders.json
│   ├── knowledge/knowledge.json
│   └── silver.json
└── main.py
```

## ВІДОМІ ПРОБЛЕМИ / ЩО ТРЕБА ПРОТЕСТИТИ
- Повний флоу режиму B — пройти анкету до кінця
- Кнопка "Назад" в анкеті
- Intent detection — перевірити що не спрацьовує зайво
- Автозаповнення з розмови — перевірити що правильно пропускає кроки

## НАСТУПНА СЕСІЯ — ФАЗА 4
1. База знань — /admin learn (текст + фото), перегляд, видалення
2. /admin update — оновлення каталогу через команду
3. Збереження історії в БД (зараз скидається при рестарті)

## КОРИСНІ КОМАНДИ
```bash
sudo systemctl status insilver-v3
sudo systemctl restart insilver-v3
tail -f ~/.openclaw/workspace/insilver-v3/logs/bot.log
sudo journalctl -u insilver-v3 -n 30 --no-pager
python3 scripts/scrape_site.py
python3 scripts/download_photos.py
```

## ЗМІННІ СЕРЕДОВИЩА (.env)
- TELEGRAM_TOKEN
- ANTHROPIC_API_KEY
- ADMIN_IDS
- OWNER_CHAT_ID=189793675
- MONITOR_CHAT_ID=-1003891541800
