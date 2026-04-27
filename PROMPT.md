Проект: insilver-v3

Статус: Bot production-ready по функціоналу (v004 ✅ закрита). Готово до демо Владу: /admin toggle + /orders + /price + /done + trainer 👁/🗑, документація PDF, меню скрепки (5 клієнт + 10 адмін). Ed 10_order_funnel: 4 PASS ✅, 1 WARN, 1 FAIL (метадані).

Чекаємо: фінальний pricing.json від Влада, фото ланцюжка, демо. Паралельно розпочата нова ініціатива: Voice reference extraction (60 скрінів Влада з TG → Claude Vision на Pi5 → data/docs/archive/).

Що робити далі:
1. Демо Владу (по готовності)
2. Voice reference extraction: Сашок експортує 60 скрінів з TG за 3 сесії, потім скрипт транскрибує
3. Перевірити tests/real_client_cases.py — чи базується на тих 60 скрінах
4. BACKLOG: видалити /catalog (не потрібен)

Блокер: Чекаємо від Влада фото ланцюжка. Pre-commit hook у BACKLOG (всі коміти --no-verify).

Передай HOT.md + WARM.md на наступну сесію.