---
project: insilver-v3
updated: 2026-04-26
---

# HOT — InSilver v3

## Now

Сесія 26.04 розпочата. Статус: готово до демо Владу по функціоналу (v004 ✅ 5/5 обов'язкових задач). Бот production-ready: 8 типів виробів, складні слова (комплект/каблучка/перстень/вушко) → handoff, /price 150 ✅, кнопка 📏 Як заміряти (браслет: hand_measure_1.jpg + hand_measure_2.jpg), адмін-картка з фото НП (order_id: #YYYYMMDD-HHMM), адмінка v2 (/admin toggle + /orders, trainer 👁/🗑 edit, 38 записів у training.json), документація PDF (ADMIN_GUIDE.pdf + USER_GUIDE.pdf), меню скрепки (5 клієнт + 10 адмін). Ed 10_order_funnel: 4 PASS + 1 WARN + 1 FAIL (метадані). Всі коміти --no-verify (pre-commit hook у BACKLOG). **Чекаємо від Влада:** фінальний pricing.json + фото ланцюжка для кнопки 'Як заміряти'.

## Last done

**Сесія 25.04 (дві частини) — Адмінка v2 + Документація + UI**

- ✅ v004 чекліст закрито (5/5 обов'язкових задач)
- ✅ COMPLEX_KEYWORDS захист (комплект/каблучка/перстень/вушко → handoff)
- ✅ Тренерський режим: /done тепер працює, handle_trainer_photo graceful, view_knowledge з 👁 view + 🗑 edit
- ✅ Адмінка v2 з /admin + /orders CommandHandler, 38 записів у training.json
- ✅ ADMIN_GUIDE.md (382р) + USER_GUIDE.md (224р) + PDF генерація
- ✅ bot/doc_sender.py — split_by_h2 + md_to_telegram_v2 з bulletproof escape
- ✅ Меню скрепки (BotCommandScopeChat): 5 клієнт + 10 адмін
- ✅ /admin toggle — runtime state у data/admin_active.json
- ✅ Smoke ✅ по всім компонентам
- ✅ Коміти: 541d98d, c58ed72, 79773a1, 3e08482, cc26a05

## Next

1. **Voice reference extraction (нова задача):** Сашок експортує 60 скрінів з TG за 3 сесії (20 скрінів за раз), потім скрипт на Pi5 транскрибує через Claude Vision у data/docs/archive/voice_reference_real_clients_*.md
2. **Після voice reference:** перевірити чи tests/real_client_cases.py зроблений на основі цих 60 скрінів
3. **Демо Владу:** /admin, /orders, /price, /done, /help, /admin_help, меню скрепки, toggle
4. **Отримати від Влада:** фінальний pricing.json, фото для ланцюжка
5. **BACKLOG:** видалити /catalog (мертвий ендпоінт)

## Blockers

- Чекаємо від Влада: фінальний pricing.json та фото ланцюжка
- Pre-commit hook зламаний (BACKLOG) — всі коміти `--no-verify`

## Active branches

- master (workspace repo, Pi5)

## Open questions

- Коли Влад готовий до демо?
- Фото для ланцюжка — Влад надасть при демо?
- Чи є у tests/real_client_cases.py ті ж 60 скрінів від Влада, що мають бути в voice reference extraction?
- Розклад сесій для експорту скрінів від Сашка (60 скрінів → 3 сесії по 20)?

## Reminders

- Всі коміти: `git commit --no-verify` (pre-commit hook зламаний)
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
