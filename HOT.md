---
project: insilver-v3
updated: 2026-04-27
---

# HOT — InSilver v3

## Now

Сесія 27.04 розпочата. Статус: контакт майстра централізовано оновлено на @InSilver_925. Змінено MASTER_TELEGRAM у .env, виправлено Markdown-парсинг у bot/client.py (рядки 125, 159) — додано backticks навколо {MASTER_TELEGRAM} бо нік з underscore (_) ламає Telegram MarkdownV2 парсер. Бот production-ready: 8 типів виробів, складні слова (комплект/каблучка/перстень/вушко) → handoff, /price 150 ✅, кнопка 📏 Як заміряти (браслет: hand_measure_1.jpg + hand_measure_2.jpg), адмін-картка з фото НП (order_id: #YYYYMMDD-HHMM), адмінка v2 (/admin toggle + /orders, trainer 👁/🗑 edit, 38 записів у training.json), документація PDF (ADMIN_GUIDE.pdf + USER_GUIDE.pdf), меню скрепки (5 клієнт + 10 адмін). Ed 10_order_funnel: 4 PASS + 1 WARN + 1 FAIL (метадані). **Чекаємо від Влада:** фінальний pricing.json + фото ланцюжка для кнопки 'Як заміряти' + підтвердження нового контакту @InSilver_925.

## Last done

**Сесія 27.04 — Оновлення контакту майстра + Markdown-фіксня**

- ✅ MASTER_TELEGRAM змінено на @InSilver_925 у .env
- ✅ Виправлено Markdown-парсинг у bot/client.py (рядки 125, 159)
- ✅ Додано backticks навколо {MASTER_TELEGRAM} в обох місцях (причина: underscore (_ ) в нічнику ламає MarkdownV2)
- ✅ Centralized контроль через core/config.py: MASTER_TELEGRAM, WEBSITE_URL + fallback на @gamaiunchik
- ✅ Зміна тільки через .env + рестарт сервісу
- ℹ️ Якщо треба синхронізувати @InSilver_925 в USER_GUIDE.md — окремо замінити там (документація може мати свою версію)

## Next

1. **Демо Владу:** /admin, /orders, /price, /done, /help, /admin_help, меню скрепки, toggle — продемонструвати оновлений контакт @InSilver_925
2. **Отримати від Влада:** фінальний pricing.json, фото для ланцюжка, підтвердження що @InSilver_925 — правильний контакт
3. **Синхронізація документації:** якщо Влад наполягає на @InSilver_925 в USER_GUIDE.md — оновити там (поки що основна воронка / prompt посилаються на MASTER_TELEGRAM з .env)
4. **Voice reference extraction:** Сашок експортує 60 скрінів з TG за 3 сесії (20 скрінів за раз), потім скрипт на Pi5 транскрибує через Claude Vision у data/docs/archive/voice_reference_real_clients_*.md
5. **BACKLOG:** видалити /catalog (мертвий ендпоінт)

## Blockers

- Чекаємо від Влада: фінальний pricing.json, фото ланцюжка, підтвердження контакту @InSilver_925
- Pre-commit hook зламаний (BACKLOG) — всі коміти `--no-verify`

## Active branches

- master (workspace repo, Pi5)

## Open questions

- Коли Влад готовий до демо з оновленим контактом @InSilver_925?
- Фото для ланцюжка — Влад надасть при демо?
- Чи @InSilver_925 має замінити @gamaiunchik везде (включно з USER_GUIDE.md)?
- Розклад сесій для експорту скрінів від Сашка (60 скрінів → 3 сесії по 20)?

## Reminders

- Всі коміти: `git commit --no-verify` (pre-commit hook зламаний)
- MASTER_TELEGRAM centralізовано з core/config.py: `os.getenv('MASTER_TELEGRAM', '@gamaiunchik')`
- Backticks у Markdown необхідні для нічників з underscore: `{MASTER_TELEGRAM}` а не {MASTER_TELEGRAM}
- Зміна контакту: .env → MASTER_TELEGRAM=@InSilver_925 → рестарт сервісу
- Voice reference extraction план: Сашок → 60 скрінів з TG → скрипт Pi5 → Claude Vision → data/docs/archive/voice_reference_real_clients_*.md
- Ed `reset_command` з `config/bots.yaml` робить reset автомат — ручні echo НЕ потрібні
- /cancel у trainer: cmd_cancel в client.py через ctx.user_data.clear()
- handle_trainer_photo graceful 'фото поки не підтримується', не handoff
- handle_photo делегує якщо ctx.user_data.trainer присутній
- Ordering: основна воронка зареєстрована ПЕРШОЮ, нова nb_* ДРУГОЮ
- ORDERS_FILE тепер Path в core/config.py, bot/order.py імпортує звідти
- Панель команд: 5 клієнт (menu, help, order, contact, price) + 10 адмін (menu, admin, orders, done, price, help, admin_help, reset, restart, logs)
- PDF: pandoc + chromium headless, fonts-noto-color-emoji + ttf-ancient-fonts встановлені
- data/docs/ + data/admin_active.json у .gitignore
- /catalog endpoint решено НЕ видаляти (Сашок) — у BACKLOG для майбутньої сесії
- Postrelease беклог: Задача 6 (Summary у старій воронці), RAG замість training.json