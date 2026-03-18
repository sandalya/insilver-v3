# InSilver v3 — DEV CHECKPOINT
**Дата:** 2026-03-18
**Статус:** Фундамент готовий, бот живий

## ЩО ЗРОБЛЕНО
- v2 заморожено в git (snapshot commit)
- Створено чисту структуру insilver-v3/
- Single-process lock (core/lock.py) — дублікатів більше не буде
- Перенесено дані: 2360 постів каталогу, знання, замовлення, баланс срібла
- Системний промпт з 20 правилами консультанта (core/prompt.py)
- Працюючий AI консультант (core/ai.py — claude-haiku)
- Telegram бот (bot/client.py) — /start + обробка повідомлень
- Systemd сервіс insilver-v3.service — автозапуск при ребуті
- Логування в logs/bot.log

## СТАН СИСТЕМИ
- Бот: systemd insilver-v3 — active (running)
- Модель: claude-haiku-4-5-20251001
- Дані: /data/photos/catalog.json (2360 постів), /data/photos/index.json (1028)
- Фото: ВІДСУТНІ локально — потрібен ре-скрейп групи Влада з збереженням file_id

## СТРУКТУРА ПРОЕКТУ
```
insilver-v3/
├── core/
│   ├── config.py      — налаштування, шляхи
│   ├── lock.py        — захист від дублікатів
│   ├── prompt.py      — системний промпт консультанта
│   └── ai.py          — Anthropic API
├── bot/
│   └── client.py      — Telegram handlers
├── data/
│   ├── photos/catalog.json   — 2360 постів з TG групи
│   ├── photos/index.json     — 1028 оброблених записів
│   ├── knowledge/knowledge.json
│   ├── orders/orders.json
│   └── silver.json
└── main.py
```

## НАСТУПНА СЕСІЯ — ФАЗА 2
Пріоритети по порядку:

1. **Пошук товарів** — коли клієнт описує що хоче, бот шукає в catalog.json
   і відповідає описом товару (поки без фото)
   Файл: core/catalog.py (новий)

2. **База знань** — /admin learn (текст + фото), перегляд, видалення
   Файл: core/knowledge.py (новий) + bot/admin.py (новий)

3. **Ре-скрейп фото** — окремий скрипт який проходить по catalog.json,
   знаходить пости в TG групі Влада і зберігає file_id
   ВАЖЛИВО: зберігати file_id а не локальні файли

## КОРИСНІ КОМАНДИ
```bash
# Статус
sudo systemctl status insilver-v3

# Перезапуск
sudo systemctl restart insilver-v3

# Логи
tail -f ~/.openclaw/workspace/insilver-v3/logs/bot.log

# Зупинити
sudo systemctl stop insilver-v3
```

## ЗМІННІ СЕРЕДОВИЩА (.env)
- TELEGRAM_TOKEN — токен бота консультанта
- ANTHROPIC_API_KEY — ключ Anthropic
- ADMIN_IDS — ID адмінів через кому

## ВІДОМІ ПРОБЛЕМИ / НОТАТКИ
- parse_mode="Markdown" увімкнено в bot/client.py
- Промпт інструктує бота бути гендерно нейтральним
- Історія розмови зберігається в пам'яті (ctx.user_data) — скидається при рестарті бота
  → В фазі 3 треба перенести в БД
