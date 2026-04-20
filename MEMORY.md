---
project: insilver-v3
---

# MEMORY — InSilver v3

## Ідентичність

- **Що:** Telegram-бот ювелірний консультант
- **Для кого:** клієнт Влад, його покупці
- **Бот:** @insilver_v3_bot
- **Сервіс:** insilver-v3.service (systemd, Pi5)

## Бізнес-контекст

- Влад — власник ювелірного бізнесу
- Бот допомагає покупцям: пошук виробів, відповіді на питання, оформлення замовлень
- Handoff — передача складних запитів живому Владу
- Admin панель для Влада: перегляд замовлень, управління

## Технічний стек

- Python + python-telegram-bot
- Anthropic API (Haiku для роутера і відповідей)
- Systemd deployment на Pi5
- Git через workspace-репо

## QA

- Ed QA agent (`workspace/ed/`) — автоматизоване тестування
- Тестові файли: `tests/real_client_cases.py`, `tests/e2e_tester.py`

## Ключові принципи

- Бот має бути ввічливим, знати асортимент, не вигадувати ціни
- Prompt guardrails — не дозволяти jailbreak або виходити за роль
- При невпевненості — handoff до Влада
