Проект: insilver-v3

Стан: Задача 1 (Інше) підтверджена. Критичний баг — /order таймаутує 90с в Ed (ручно OK). Не в коді бота, баг в Ed flow або timing. 10_order_funnel.json оновлений. httpx логи закриті.

Зробити: 1) Дебажити /order таймаут (журнали, timing, click_intent). 2) Ed коментар-assertions. 3) Повна регресія Ed. 4) Демо Владу (після фіксу).

Блокери: /order race condition (КРИТИЧНИЙ).

Почни з: Подели HOT.md + WARM.md, потім порівняй journalctl для ручного тесту /order vs Ed. Перевір click_intent в 10_order_funnel.json.
