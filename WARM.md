---
project: insilver-v3
updated: 2026-04-20
---

# WARM — InSilver v3

## Архітектура — Smart Router

```yaml
last_touched: 2026-04-20
tags: [architecture, router, ai]
status: active
```

`core/router.py` — класифікує intent через Haiku. 4 інтенти: SEARCH / QUESTION / ORDER / SOCIAL. Каталог показується ТІЛЬКИ для SEARCH intent. Модель: `claude-haiku-4-5-20251001`. **Баг:** intent cache не очищується між запусками, дає хибні результати.

## Order funnel

```yaml
last_touched: 2026-04-20
tags: [order, funnel, ui]
status: active
```

`bot/order.py` — форма замовлення. `core/order_config.py` — конфіг анкети. `core/order_context.py` — автозаповнення полів з історії діалогу. **Баг:** кнопка "Інше" не запитує текстовий ввід після натискання.

## Каталог і пошук

```yaml
last_touched: 2026-04-16
tags: [catalog, search]
status: active
```

`core/catalog.py` — пошук у каталозі ювелірних виробів. Поки плоский пошук, без RAG. Дані у `data/`.

## Prompt і training

```yaml
last_touched: 2026-04-17
tags: [prompt, training, ai]
status: active
```

`core/prompt.py` — системний промпт + 15 Q&A з `training.json`. Q&A вбудовані плоско у контекст. Roadmap: замінити на RAG для масштабування.

## Handoff (human escalation)

```yaml
last_touched: 2026-04-17
tags: [handoff, admin]
status: active
```

`core/handoff.py` — механізм передачі розмови живому оператору (Владу). Prompt guardrails забезпечують коректне переключення.

## Admin панель

```yaml
last_touched: 2026-04-16
tags: [admin, ui]
status: active
```

`bot/admin.py` — адмін панель (спрощена, 279 рядків). `bot/admin_orders.py` — управління замовленнями. Команди: `/admin`, `/orders`.

## Conversation logger

```yaml
last_touched: 2026-04-16
tags: [logging, infrastructure]
status: active
```

`core/conversation_logger.py` — логування розмов з клієнтами. Логи у `logs/`.

## Photo handling

```yaml
last_touched: 2026-04-16
tags: [photo, media]
status: active
```

`core/photo.py` — обробка фото від клієнтів (присилають фото виробів для оцінки/пошуку аналогів).

## Pricing

```yaml
last_touched: 2026-04-16
tags: [pricing, catalog]
status: active
```

`core/pricing.py` — логіка ціноутворення для ювелірних виробів.

## Інфраструктура

```yaml
last_touched: 2026-04-17
tags: [infrastructure, deployment]
status: active
```

Сервіс: `insilver-v3.service` (systemd). Бот: `@insilver_v3_bot`. Health checker: `core/health.py`. Lock: `core/lock.py` (single process). Pi5, workspace `/home/sashok/.openclaw/workspace/insilver-v3/`.

## Layout проекту

```yaml
last_touched: 2026-04-20
tags: [layout, files]
status: active
```

```
insilver-v3/
├── main.py              — точка входу
├── bot/
│   ├── client.py        — обробка повідомлень + router
│   ├── order.py         — форма замовлення
│   ├── admin.py         — адмін панель
│   └── admin_orders.py  — управління замовленнями
├── core/
│   ├── ai.py            — Anthropic API
│   ├── router.py        — intent classification
│   ├── catalog.py       — пошук в каталозі
│   ├── prompt.py        — системний промпт
│   ├── config.py        — конфігурація
│   ├── handoff.py       — human escalation
│   ├── health.py        — health checker
│   ├── conversation_logger.py
│   ├── lock.py          — single process lock
│   ├── order_config.py  — конфіг анкети
│   ├── order_context.py — автозаповнення
│   ├── photo.py         — фото
│   ├── pricing.py       — ціноутворення
│   ├── backup_system.py
│   └── log_analyzer.py
├── data/                — каталог, training.json
├── logs/
├── tests/               — Ed QA тести
└── scripts/
```