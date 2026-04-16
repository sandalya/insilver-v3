# DEV_CHECKPOINT — InSilver v3
Оновлено: 2026-04-16

## Стан проекту
- Сервіс: active (insilver-v3.service)
- Бот: @insilver_v3_bot
- Модель: claude-haiku-4-5-20251001

## Архітектура
- Smart Router (core/router.py) — класифікує intent через Haiku
- 4 інтенти: SEARCH / QUESTION / ORDER / SOCIAL
- Каталог показується ТІЛЬКИ для SEARCH intent
- Admin: /admin + /orders (спрощений, 279 рядків)

## Файли
- main.py — точка входу
- bot/client.py — обробка повідомлень + router
- bot/order.py — форма замовлення
- bot/admin.py — адмін панель (спрощена)
- bot/admin_orders.py — управління замовленнями
- core/ai.py — Anthropic API
- core/router.py — intent classification
- core/catalog.py — пошук в каталозі
- core/prompt.py — системний промпт + 15 Q&A з training.json
- core/config.py — конфігурація
- core/health.py — health checker
- core/conversation_logger.py — логування розмов
- core/lock.py — single process lock
- core/order_config.py — конфіг анкети замовлення
- core/order_context.py — автозаповнення з історії
- core/photo.py — робота з фото

## Наступні кроки
1. Запустити Ed QA і перевірити покращення (ціль: 8+ з 12)
2. Підключити Влада — показати /admin і /orders
3. Розглянути: RAG замість плоского training в промпті
