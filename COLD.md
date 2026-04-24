---
project: insilver-v3
started: 2026-04-20
---

# COLD — InSilver v3

Історія проекту. Append-only. Не редагувати старі записи.

---

## 2026-04-20: Ініціалізація триярусної пам'яті

Перехід з `SESSION.md` + `DEV_CHECKPOINT.md` на `HOT.md` + `WARM.md` + `COLD.md`. Раніше стан проекту розкидано між двома файлами: SESSION.md (останній чекпоінт) і DEV_CHECKPOINT.md (архітектура + файли). Новий підхід: HOT (переписується кожну сесію), WARM (архітектура, інкрементально), COLD (append-only архів).

---

## 2026-04-20: InSilver v3 архітектура (baseline)

```yaml
archived_at: 2026-04-20
reason: baseline snapshot при міграції на три яруси
tags: [baseline, architecture]
```

InSilver v3 — ювелірний консультант для Влада (@insilver_v3_bot). Smart Router класифікує 4 інтенти (SEARCH/QUESTION/ORDER/SOCIAL) через Haiku. Каталог плоский, Q&A з training.json вбудовані в промпт. Order funnel з автозаповненням. Admin панель: /admin + /orders. Handoff для передачі оператору. Деплой: systemd на Pi5.

---

## 2026-04-25: /order race condition в Ed (таймаут 90с)

```yaml
archivals_at: 2026-04-25
reason: critical bug discovered, needs urgent investigation
tags: [bug, ed, order, timing, race-condition]
```

Виявлено КРИТИЧНИЙ баг: /order не долітає до бота під Ed flow — 90с таймаут. У ручному тесті спрацьовує миттєво. Баг не в коді бота (логіка OK), ймовірно в Ed flow timing або network. Задача 1 (Інше) підтверджена й працює. 10_order_funnel.json оновлений (weaving/length ключі, коментар-flow, wait після /start). httpx токен-логи закриті в main.py. Дебажити через журнали (`journalctl -u insilver-v3 -f`), порівняти timing ручного тесту vs Ed. Демо Владу перенесено на після фіксу.
