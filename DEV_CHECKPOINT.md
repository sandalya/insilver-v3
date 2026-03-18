# InSilver v3 — DEV CHECKPOINT
**Дата:** 2026-03-18
**Статус:** Фаза 1+2 ЗАВЕРШЕНА — бот живий, пошук + фото працюють

## ЩО ЗРОБЛЕНО СЬОГОДНІ
- **Пошук товарів** (core/catalog.py) — keyword+синоніми по 484 товарах з сайту
- **Скрейп сайту** (scripts/scrape_site.py) — 484 товари з insilver.pp.ua
- **Завантаження фото** (scripts/download_photos.py)
  → Playwright перехоплює фото під час рендерингу (Google CDN блокує прямі запити)
  → 2675 фото збережено локально в data/photos/site/
  → Логотип InSilver відфільтрований по розміру (61514 bytes)
- **Відправка фото** в Telegram — медіагрупа або одне фото з підписом
- **Вага товарів** розпарсена для 229/484 (решта — кулони/хрестики без ваги)
- **Чекпоінт** оновлено

## СТАН СИСТЕМИ
- Бот: systemd insilver-v3 — active (running)
- Модель: claude-haiku-4-5-20251001
- Каталог: data/site_catalog.json (484 товари)
- Фото: data/photos/site/ (2675 файлів)

## СТРУКТУРА ПРОЕКТУ
```
insilver-v3/
├── core/
│   ├── config.py      — налаштування (SITE_CATALOG тощо)
│   ├── lock.py        — захист від дублікатів
│   ├── prompt.py      — системний промпт (20 правил)
│   ├── ai.py          — Anthropic API (haiku)
│   └── catalog.py     — пошук по site_catalog.json
├── bot/
│   └── client.py      — handlers + відправка фото
├── scripts/
│   ├── scrape_site.py      — скрейп insilver.pp.ua
│   └── download_photos.py  — завантаження фото через Playwright
├── data/
│   ├── site_catalog.json      — 484 товари (основний каталог)
│   ├── photos/site/           — 2675 локальних фото
│   ├── photos/catalog.json    — TG каталог (резерв, 2399 постів)
│   ├── knowledge/knowledge.json
│   ├── orders/orders.json
│   └── silver.json
└── main.py
```

## НАСТУПНА СЕСІЯ — ФАЗА 3
Пріоритети по порядку:

1. **Форма замовлення в боті** — кнопка "Замовити" під фото товару
   → ConversationHandler: ім'я → телефон → місто → доставка → коментар
   → Зберігати в orders.json
   → Сповіщення Владу в TG
   Файли: bot/order.py (новий)

2. **База знань** — /admin learn (текст + фото), перегляд, видалення
   Файли: core/knowledge.py + bot/admin.py

3. **Оновлення каталогу** — /admin update запускає scrape + download
   Або крон раз на тиждень

4. **Збереження історії в БД** — зараз скидається при рестарті

## КОРИСНІ КОМАНДИ
```bash
sudo systemctl status insilver-v3
sudo systemctl restart insilver-v3
tail -f ~/.openclaw/workspace/insilver-v3/logs/bot.log
python3 scripts/scrape_site.py        # оновити каталог
python3 scripts/download_photos.py    # докачати нові фото
```

## ЗМІННІ СЕРЕДОВИЩА (.env)
- TELEGRAM_TOKEN — токен бота-консультанта
- ANTHROPIC_API_KEY — ключ Anthropic
- ADMIN_IDS — ID адмінів через кому
- OWNER_CHAT_ID=189793675
- MONITOR_CHAT_ID=-1003891541800

## ВІДОМІ ПРОБЛЕМИ / НОТАТКИ
- Google CDN блокує прямі HTTP запити → Playwright обходить перехопленням
- Фото на міліметрівці — це норма для ювелірки
- Логотип (61514 bytes) фільтрується в client.py константою LOGO_SIZE
- Історія розмови в пам'яті — скидається при рестарті (фаза 4: БД)
- TG фото групи Влада — недоступні через API обмеження, не використовуємо
