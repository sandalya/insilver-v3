---
project: insilver-v3
updated: 2026-04-25
---

# HOT — InSilver v3

## Now

Закрито httpx токен-логи в main.py. Задача 1 (Інше) підтверджена — працює. 10_order_funnel.json оновлений (weaving/length ключі, коментар-flow, wait після /start). Основний баг тепер — /order race condition під Ed flow: у ручному тесті летить миттєво, в Ed — 90с таймаут. 3 з 6 задач v004 фактично закриті (Задача 1, частково 2).

## Last done

**Сесія 25.04**

- Закрито httpx токен-логи в main.py
- Задача 1 (Інше) підтверджена — працює
- 10_order_funnel.json оновлений: weaving/length ключі, коментар-flow, wait після /start
- Виявлено основний баг: /order race condition під Ed flow (90с таймаут)
- Ручний тест /order спрацьовує миттєво, Ed — гальмує

## Next

1. **Дебажити /order таймаут** — з'ясувати чому /order не долітає до бота в Ed (журнали, timing, network)
2. **Ed коментар-assertions** — додати assertions для коментар-flow
3. **Повна регресія Ed** — після фіксу таймауту прогнати всі блоки
4. **Демо Владу** — /admin, /orders на реальних замовленнях (невстигли цього тижня)

## Blockers

- **КРИТИЧНИЙ:** /order race condition в Ed (90с таймаут). У ручному тесті OK, в Ed не спрацьовує. Баг не в коді бота — в Ed flow або в timing запиту.
- Ed: коментар-assertions потребують розширення
- Демо Владу перенесено (результат таймаут-бага)

## Active branches

- master (workspace repo)

## Open questions

- Чому /order таймаутує в Ed (90с)? Де саме гальмує — в роутері, в order_handler, в API?
- Чи проблема в `click_intent` частковому співпаданні для /order кнопки в Ed?
- Коли Влад готовий до демо (після фіксу таймауту)?
- RAG замість training.json — після демо Владу?

## Reminders

- Перед тестуванням — запустити `journalctl -u insilver-v3 -f` **до** надсилання повідомлення боту
- Використовувати `/home/sashok/.openclaw/workspace/insilver-v3/`
- API keys маскувати до останніх 4 символів
- **Для дебагу /order таймауту:** порівняти журнали ручного тесту vs Ed (timing, stacktrace)
- **Між Ed-блоками:** `echo '{}' > data/handoff_state.json && sudo systemctl restart insilver-v3 && sleep 3`
- **Ed правило:** Ed first для тестів (у цьому випадку — Ed виявив баг, який руками не видно)
