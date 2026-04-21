---
project: insilver-v3
updated: 2026-04-21
---

# WARM — InSilver v3
## 🚨 ПРАВИЛО: Ed first для тестів

```yaml
last_touched: 2026-04-21
tags: [testing, workflow, critical]
status: active
```

**Будь-який функціональний тест бота — через Ed, НЕ руками.** Якщо у `ed/suites/data/insilver/blocks/` немає потрібного кейсу — спочатку оцінити час на додання. ≤30 хв → додати в Ed і прогнати. >30 хв → попередити і запропонувати ручний тест як виняток. Не застосовувати тільки для інфраструктурних перевірок (systemd, файли, shell).


## Архітектура — Smart Router

```yaml
last_touched: 2026-04-17
tags: [architecture, router, ai]
status: active
```

`core/router.py` — класифікує intent через Haiku. 4 інтенти: SEARCH / QUESTION / ORDER / SOCIAL. Каталог показується ТІЛЬКИ для SEARCH intent. Модель: `claude-haiku-4-5-20251001`.

## Order funnel — дві системи

```yaml
last_touched: 2026-04-17
tags: [order, funnel, ui]
status: active
```

**Основна (стара, `build_order_handler`)** — зареєстрована ПЕРШОЮ в `setup_handlers`. `bot/order.py` + `core/order_config.py` + `core/order_context.py` (автозаповнення з історії). 8 типів виробів: ланцюжок, браслет, хрестик, кулон, обручка, перстень, набір, інше. Кожен тип має свої кроки (напр. ланцюжок: плетіння→довжина→маса→покриття→застібка→додатково→контакт→коментар). Кнопки "⬅️ Назад" і "❌ Скасувати" на кожному кроці. `_waiting_custom` для обробки "✏️ Інше" — бот просить текстовий ввід.

**Нова (nb_*, `build_new_order_handler`)** — зареєстрована ДРУГОЮ (запасна). Тільки ланцюжок/браслет. Має калькулятор і summary перед підтвердженням.

**Відомі баги:** кнопка "Інше" не запитує текстовий ввід (баг у `_waiting_custom`). Стара воронка створює замовлення без попереднього summary.

## Prompt і guardrails

```yaml
last_touched: 2026-04-17
tags: [prompt, training, ai, guardrails]
status: done
```

`core/prompt.py` — системний промпт + 15 Q&A з `training.json`. Q&A вбудовані плоско у контекст. Мультимовність: розуміє всі мови, НІКОЛИ не відповідає російською. Guardrails: тільки срібло 925, не додавати зайвих елементів, релігійні вироби тільки з бази. Ed тести `07_prompt_guardrails` — green. Roadmap: замінити плоский training на RAG для масштабування.

## Handoff (human escalation)

```yaml
last_touched: 2026-04-17
tags: [handoff, admin]
status: done
```

`core/handoff.py` — pause/resume. `handle_photo` — фото → адміну + пауза. `handle_resume` — callback для адміна. Ed тести `09_handoff` — green. Між Ed-блоками треба скидати `data/handoff_state.json` → `{}`, інакше бот мовчить.

## Keyword detection (складні вироби)

```yaml
last_touched: 2026-04-17
tags: [keywords, handoff, routing]
status: planned
```

Має спрацьовувати в `handle_message` (`bot/client.py`) для вільного чату — НЕ всередині ConversationHandler (воронки). ConversationHandler природно ізолює — `handle_message` не викликається коли клієнт у воронці. Статус: не перевірено чи є в коді. Треба `grep -n "COMPLEX_KEYWORDS\|HUMAN_TRIGGERS" bot/client.py`.

## Калькулятор

```yaml
last_touched: 2026-04-16
tags: [pricing, calculator]
status: done
```

`core/pricing.py` з `calculate_price()`, `format_price()`, `get_price_per_gram()`. `data/pricing.json` — ціни. Працює в новій воронці (nb_*).

## Каталог і пошук

```yaml
last_touched: 2026-04-16
tags: [catalog, search]
status: active
```

`core/catalog.py` — пошук у каталозі ювелірних виробів. Поки плоский пошук, без RAG. Дані у `data/`.

## Admin панель

```yaml
last_touched: 2026-04-16
tags: [admin, ui]
status: active
```

`bot/admin.py` — адмін панель (спрощена, 279 рядків). `bot/admin_orders.py` — управління замовленнями. Команди: `/admin`, `/orders`. Ще не показано Владу.

## Photo handling

```yaml
last_touched: 2026-04-16
tags: [photo, media]
status: active
```

`core/photo.py` — обробка фото від клієнтів. Фото → адміну → handoff пауза → "Повернути бота".

## Conversation logger

```yaml
last_touched: 2026-04-16
tags: [logging, infrastructure]
status: active
```

`core/conversation_logger.py` — логування розмов з клієнтами. Логи у `logs/`.

## Ed QA integration

```yaml
last_touched: 2026-04-17
tags: [testing, ed, qa]
status: active
```

Ed QA agent (`workspace/ed/`). Target: `@insilver_v3_bot`. Запуск: `cd ~/.openclaw/workspace/ed && source venv/bin/activate && python3 main.py run --bot insilver --block <BLOCK> --transport telegram --judge haiku`. Тест-кейси: `ed/suites/data/insilver/blocks/`. Рубрики: `ed/judge/rubrics/insilver.py`.

Блоки: `01_smoke`, `07_prompt_guardrails` (✅ green), `09_handoff` (✅ green), `10_order_funnel` (❌ intent cache баг, кнопка Інше баг). Два типи тестів: одиночні і multi-step з кнопками (`click_intent` — часткове співпадіння тексту, emoji ігноруються).

**⚠️ Між блоками скидати handoff:** `echo '{}' > data/handoff_state.json && sudo systemctl restart insilver-v3 && sleep 3`

**Відомий баг:** Ed intent cache дає хибні результати між запусками. Funnel: після Ланцюжок→плетіння Ed плутає Бісмарк.

## Інфраструктура

```yaml
last_touched: 2026-04-17
tags: [infrastructure, deployment]
status: active
```

Сервіс: `insilver-v3.service` (systemd). Бот: `@insilver_v3_bot`. Health checker: `core/health.py`. Lock: `core/lock.py` (single process). Pi5, workspace `/home/sashok/.openclaw/workspace/insilver-v3/`.

## Roadmap (з implementation guide v003)

```yaml
last_touched: 2026-04-20
tags: [roadmap, planning]
status: active
```

**Задача 1** — Пофіксити Ed тести для воронки (`10_order_funnel`): intent cache, кнопка Інше. ← ПОТОЧНА
**Задача 2** — Перевірити keyword detection в `client.py` (складні вироби).
**Задача 3** — Повна регресія Ed (ціль: всі блоки зелені).
**Задача 4** — Summary в стару воронку (опціонально, не блокує).
**Далі:** pricing від Влада, показати Владу /admin і /orders, RAG замість плоского training.

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
│   ├── order.py         — форма замовлення (стара, основна)
│   ├── admin.py         — адмін панель
│   └── admin_orders.py  — управління замовленнями
├── core/
│   ├── ai.py            — Anthropic API
│   ├── router.py        — intent classification
│   ├── catalog.py       — пошук в каталозі
│   ├── prompt.py        — системний промпт + guardrails
│   ├── config.py        — конфігурація
│   ├── handoff.py       — human escalation
│   ├── health.py        — health checker
│   ├── conversation_logger.py
│   ├── lock.py          — single process lock
│   ├── order_config.py  — конфіг анкети (8 типів виробів)
│   ├── order_context.py — автозаповнення з історії
│   ├── photo.py         — фото → адмін
│   ├── pricing.py       — калькулятор цін
│   ├── backup_system.py
│   └── log_analyzer.py
├── data/                — каталог, training.json, pricing.json
├── logs/
├── tests/               — Ed QA тести (legacy)
└── scripts/
```
