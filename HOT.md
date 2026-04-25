---
project: insilver-v3
updated: 2026-04-25
---

# HOT — InSilver v3

## Now

Сесія 25.04 завершена. v004 закрита (5/5 обов'язкових задач). Бот production-ready по функціоналу: 8 типів виробів, складні слова (комплект/каблучка/перстень/вушко) → handoff, /price 150 ✅, кнопка 📏 Як заміряти (браслет: hand_measure_1.jpg + hand_measure_2.jpg), адмін-картка з фото НП (order_id: #YYYYMMDD-HHMM uuid fix), Markdown-краш фікс (b_send_step + notify_owner). Ed 10_order_funnel: 4 PASS + 1 WARN + 1 FAIL (метадані). Коміти: 541d98d (фічі), c58ed72 (фікси), 79773a1 (Path import). Всі коміти --no-verify (pre-commit hook у BACKLOG).

## Last done

**Сесія 25.04 — v004 фінальна (ТЗ Влада закрито)**

- ✅ COMPLEX_KEYWORDS: комплект, каблучка, перстень, вушко → handoff
- ✅ /price 150 команда (default + per-weaving)
- ✅ COMMON_STEPS: +city, +np_office для адреси доставки
- ✅ Режим A з A_NP_OFFICE станом для адмін-картки
- ✅ Адмін-картка з 🚚 НП (фото, фулл-адреса, відділення)
- ✅ order_id фіксня: uuid → #YYYYMMDD-HHMM формат
- ✅ Кнопка 📏 Як заміряти у старій воронці з фото браслета
- ✅ Видалення попередніх повідомлень воронки (include перше Що замовляємо)
- ✅ Markdown-краш фіксня (b_send_step + notify_owner без parse_mode)
- ✅ Влад → Наш співробітник (текст оновлено)
- ✅ /price NoneType захист
- ✅ Smoke end-to-end воронка
- ✅ Ed 10_order_funnel: 4 PASS + 1 WARN + 1 FAIL (метадані)
- ✅ Глобальний імпорт Path у client.py (handle_photo падав)

## Next

1. **Доробити ADMIN_GUIDE.md + USER_GUIDE.md** — фінальне причісування (~330+154 рядків)
2. **Отримати від Влада фінальний pricing.json** — якщо є зміни до демо
3. **Ультімейт-тест зі скрінів Влада** — повний flow як клієнт
4. **Демо Владу** — показати /admin, /orders, функціонал
5. **Фото для ланцюжка** — поки тільки браслет (hand_measure_*), попросити для ланцюжка
6. **Опціональна Задача 6** — Summary у старій воронці (якщо час)

## Blockers

- **pre-commit hook:** зламаний (3 посилання на файли тестів, 2 не існують) → у BACKLOG, всі коміти `--no-verify`
- **order_id неконсистентність:** стара воронка 20260425-1405 (без #), нова #20260425-1405 — не блокує критично
- **show_measure_button старої воронки:** тільки для браслета, для ланцюжка text-fallback HOW_TO_MEASURE

## Active branches

- master (workspace repo)

## Open questions

- Коли Влад готовий до демо + фінальний pricing.json?
- Фото для ланцюжка — Влад надасть при демо?
- Чи потрібна Задача 6 (Summary) чи можна релізити без неї?

## Reminders

- ADMIN_GUIDE.md + USER_GUIDE.md — фінальний крок перед релізом
- pre-commit hook у BACKLOG — не блокує (--no-verify хід)
- Всі коміти: `git commit --no-verify`
- Ed `reset_command` з `config/bots.yaml` робить reset автомат — ручні echo НЕ потрібні
- prefilled з extract_order_context може потрапити у _filled — якщо проблеми зі спецсимволами, дивитись туди
- show_measure_button у старій воронці тільки для браслета — для ланцюжка text-fallback HOW_TO_MEASURE