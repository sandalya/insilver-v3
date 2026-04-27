---
project: insilver-v3
updated: 2026-04-27
---

# HOT — InSilver v3

## Now

Сесія 27.04 завершена. Статус: контакт майстра централізовано оновлено на @InSilver_925. Замінено MASTER_TELEGRAM у .env, виправлено Markdown-парсинг у bot/client.py (рядки 125, 159) — додано backticks навколо {MASTER_TELEGRAM} бо нік з underscore (_) ламає Telegram MarkdownV2 парсер. Замінено 4 входження OWNER_CHAT_ID на ADMIN_IDS[0] в bot/order.py (нотифікації про замовлення тепер йдуть Владу напряму). ADMIN_IDS = [467578687, 189793675] (Влад перший). Бот production-ready: 8 типів виробів, складні слова (комплект/каблучка/перстень/вушко) → handoff, /price 150 ✅, кнопка 📏 Як заміряти (браслет: hand_measure_1.jpg + hand_measure_2.jpg), адмін-картка з фото НП (order_id: #YYYYMMDD-HHMM), адмінка v2 (/admin toggle + /orders, trainer 👁/🗑 edit, 38 записів у training.json), документація PDF (ADMIN_GUIDE.pdf + USER_GUIDE.pdf), меню скрепки (5 клієнт + 10 адмін). Ed 10_order_funnel: 4 PASS + 1 WARN + 1 FAIL (метадані). **Чекаємо від Влада:** підтвердження що замовлення #20260427-1829 дійшло на новий контакт; потім cleanup OWNER_CHAT_ID з .env і core/config.py; синхронізація @InSilver_925 в USER_GUIDE.md (2 місця).

## Last done

**Сесія 27.04 — Оновлення контакту майстра + Markdown-фіксня + нотифікації**

- ✅ MASTER_TELEGRAM змінено на @InSilver_925 у .env
- ✅ Виправлено Markdown-парсинг у bot/client.py (рядки 125, 159) — додано backticks навколо {MASTER_TELEGRAM}
- ✅ Замінено 4 входження OWNER_CHAT_ID на ADMIN_IDS[0] в bot/order.py (notify_admin x2, notify_owner х2 → ADMIN_IDS[0])
- ✅ ADMIN_IDS = [467578687, 189793675] встановлено (Влад перший адмін)
- ✅ Централізований контроль через core/config.py: MASTER_TELEGRAM, WEBSITE_URL + fallback на @gamaiunchik
- ✅ Імпорт ADMIN_IDS у bot/order.py закритий
- ℹ️ USER_GUIDE.md поки не оновлений — чекаємо підтвердження від Влада

## Next

1. **Чекаємо від Влада:** підтвердження що замовлення #20260427-1829 дійшло на @InSilver_925 (Владі в особистий чат)
2. **Після підтвердження:** cleanup OWNER_CHAT_ID з .env і core/config.py (видалити всі посилання)
3. **Синхронізація USER_GUIDE.md:** замінити @gamaiunchik на @InSilver_925 (2 місця) у разі необхідності
4. **Демо Владу:** /admin, /orders, /price, /done, /help, /admin_help, меню скрепки, toggle — з оновленим контактом
5. **Отримати від Влада:** фінальний pricing.json, фото для ланцюжка, підтвердження ціновки
6. **Voice reference extraction:** Сашок експортує 60 скрінів з TG за 3 сесії (20 скрінів за раз), потім скрипт на Pi5 транскрибує через Claude Vision у data/docs/archive/voice_reference_real_clients_*.md
7. **BACKLOG:** видалити /catalog (мертвий ендпоінт)

## Blockers

- Чекаємо від Влада: підтвердження що замовлення #20260427-1829 дійшло; потім cleanup OWNER_CHAT_ID
- Pre-commit hook зламаний (BACKLOG) — всі коміти `--no-verify`

## Active branches

- master (workspace repo, Pi5)

## Open questions

- Коли Влад підтвердить что замовлення дійшло на @InSilver_925?
- Потім чи видалити OWNER_CHAT_ID з .env і config.py?
- Чи синхронізувати @InSilver_925 в USER_GUIDE.md або залишити @gamaiunchik?
- Розклад сесій для експорту скрінів від Сашка (60 скрінів → 3 сесії по 20)?

## Reminders

- Всі коміти: `git commit --no-verify` (pre-commit hook зламаний)
- MASTER_TELEGRAM centralізовано з core/config.py: `os.getenv('MASTER_TELEGRAM', '@gamaiunchik')`
- ADMIN_IDS[0] тепер використовується для нотифікацій замовлення (449 рядок, замість OWNER_CHAT_ID)
- Backticks у Markdown необхідні для нічників з underscore: `` `{MASTER_TELEGRAM}` `` а не {MASTER_TELEGRAM}
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
- /catalog endpoint рішено НЕ видаляти (Сашок) — у BACKLOG для майбутньої сесії
- Postrelease беклог: Задача 6 (Summary у старій воронці), RAG замість training.json
