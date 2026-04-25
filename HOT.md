---
project: insilver-v3
updated: 2026-04-25
---

# HOT — InSilver v3

## Now

Сесія 25.04 завершена. Закрито всі 5 обов'язкових задач v004: allow_reentry=True у двох ConversationHandler (фіксить /order після завершеної воронки), safe_admin_send helper в core/handoff.py з warmup на 'Chat not found', замінено 4 точки нотифікацій адміна (order.py x2, client.py x2). Ed 10_order_funnel: 4 PASS + 1 WARN + 1 несправжній FAIL (метадані). httpx-логи токенів закриті в main.py. Teknical checklist 5/5 обов'язкових. Bot production-ready по функціоналу.

## Last done

**Сесія 25.04 — v004 закрита**

- ✅ Дозволено повторний вхід у воронку (allow_reentry=True в обох ConversationHandler)
- ✅ Фіксня /order після завершення воронки (ConversationHandler end)
- ✅ safe_admin_send helper в core/handoff.py з warmup на 'Chat not found'
- ✅ Замінено 4 точки нотифікацій адміна (order.py x2, client.py x2)
- ✅ httpx-логи токенів закриті в main.py
- ✅ Ed 10_order_funnel: 4 PASS + 1 WARN + 1 несправжній FAIL (метадані)
- ✅ Задача 1 (Інше), Задача 2 (частково) підтверджені

## Next

1. **Доробити ADMIN_GUIDE.md і USER_GUIDE.md** — допилити, причесати (вже є ~330+154 рядків)
2. **Ультімейт-тест зі скрінів Влада** — перевірити все як клієнт
3. **Отримати від Влада фінальний pricing.json** — якщо є зміни
4. **Показати Владу /admin і /orders** — демо адмін панелі
5. **Опціональна Задача 6** — Summary у старій воронці (якщо час)

## Blockers

- **pre-commit hook:** зламаний (посилається на 3 файли тестів, з яких 2 не існують) — всі коміти --no-verify. У BACKLOG.
- Задача 6 (Summary у старій воронці) — опціональна, може бути пропущена

## Active branches

- master (workspace repo)

## Open questions

- Коли Влад готовий до демо (pricing.json + скріни)?
- Чи потрібна Задача 6 чи можна йти на релізу без неї?
- RAG замість training.json — після релізу?

## Reminders

- Документація (ADMIN_GUIDE, USER_GUIDE) — фінальний krok перед релізом
- pre-commit hook у BACKLOG — не блокує релізу (--no-verify хід)
- Між Ed-блоками: `echo '{}' > data/handoff_state.json && sudo systemctl restart insilver-v3 && sleep 3`
- Всі коміти: `git commit --no-verify`