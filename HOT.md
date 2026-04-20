---
project: insilver-v3
updated: 2026-04-20
---

# HOT — InSilver v3

## Now

Триярусна пам'ять ініціалізована. Міграція з SESSION.md завершена. Ed QA виявив критичні баги: intent cache дає хибні результати між запусками, кнопка "Інше" в order funnel не запитує текст. Цілі: зафіксити кеш, зафіксити funnel, показати Владу /admin.

## Last done

**Сесія 20.04**

- Ініціалізація HOT.md, WARM.md, COLD.md
- Міграція історії з SESSION.md → COLD.md
- Аналіз активних багів від Ed QA

## Next

1. Дебаг Ed intent cache — знайти місце де кеш не очищується між запусками
2. Зафіксити кнопка "Інше" — мав запитувати текстовий ввід після натискання
3. Запустити Ed QA повний прогін (ціль: 8+ з 12)
4. Демо для Влада: /admin + /orders

## Blockers

- Ed intent cache дає хибні результати — проблема в `bot/client.py` або `core/router.py`
- Order funnel: після вибору опції "Інше" бот не просить текст (баг у `bot/order.py`)

## Active branches

- master (workspace repo)

## Open questions

- RAG замість плоского training.json — коли починати?
- Чи варто додати логування для intent cache дебагу?

## Reminders

- Перед тестуванням — запустити `journalctl -u insilver-v3 -f` **до** надсилання повідомлення боту
- Використовувати `/home/sashok/.openclaw/workspace/insilver-v3/`
- API keys маскувати до останніх 4 символів
- Для UI/діалог тестів — пропонувати Ed