---
project: insilver-v3
updated: 2026-04-22
---

# HOT — InSilver v3

## Now

По підсумкам сесії 22.04: Summary+Confirm крок у воронці готовий, Ed matcher виконує layered match без помилок, reset_conversation /cancel флоу зафіксено, handoff warmup протестовано. Додано нові assertions у блок 10_order_funnel. Влад підтвердив pricing і готовий до демо /admin та /orders. Залишаються дрібні race-баги в Ed (беклог).

## Last done

**Сесія 22.04**

- Summary+Confirm крок у воронці реалізовано
- Ed matcher: layered match без помилок
- reset_conversation /cancel флоу зафіксено
- Handoff warmup протестовано
- Нові assertions додані до `10_order_funnel` блоку
- Pricing підтверджено Владом
- Задачі 1-6 з v004 закриті (крім дрібних race-багів Ed)

## Next

1. **Влад: демо** — показати /admin, /orders на реальних замовленнях
2. **Влад: pricing** — запустити калькулятор з підтвердженими цінами
3. **Ed тести допрацювати** — race state leak, додати текст коментаря в comment_flow, з'ясувати пусте фінальне повідомлення у happy_path
4. **Беклог Ed race-баги** — низький пріоритет, не блокує релізу

## Blockers

- Ed: race state leak в `10_order_funnel` (низький пріоритет, в беклозі)
- Ed: comment_flow — треба додати текст коментаря в assertions
- Ed: happy_path — невідомо чому остаточне повідомлення пусте (дослідження)

## Active branches

- master (workspace repo)

## Open questions

- Коли Влад готовий до демо /admin + /orders? (визначити день/час)
- RAG замість training.json — коли починати? (після демо Владу?)
- Keyword detection (складні вироби) — вже в коді чи треба додати? (`grep -n "COMPLEX_KEYWORDS" bot/client.py`)

## Reminders

- Перед тестуванням — запустити `journalctl -u insilver-v3 -f` **до** надсилання повідомлення боту
- Використовувати `/home/sashok/.openclaw/workspace/insilver-v3/`
- API keys маскувати до останніх 4 символів
- Для UI/діалог тестів — пропонувати Ed (не ручне тестування)
- **Між Ed-блоками:** `echo '{}' > data/handoff_state.json && sudo systemctl restart insilver-v3 && sleep 3`
- Демо для Влада: запустити бота, показати /admin сторінку, демонструвати /orders з реальними замовленнями
