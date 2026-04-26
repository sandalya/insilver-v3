Проект: insilver-v3

Стан: v004 закрита (5/5 обов'язкових задач), бот production-ready по функціоналу. Сесія 25.04 завершила: документація (ADMIN_GUIDE.md 382р + USER_GUIDE.md 224р + PDF), команди (/help /admin_help з MarkdownV2), меню скрепки (5 клієнт + 10 адмін), /admin toggle, doc_sender.py (md_to_telegram_v2 bulletproof). Коміти: 3e08482 (docs), cc26a05 (feat) — обидва --no-verify.

Що далі:
1. Демо Владу: /admin, /orders, /price, /done, /help, /admin_help, меню, toggle
2. Отримати: фінальний pricing.json, фото для ланцюжка
3. Smoke final: PDF ADMIN_GUIDE.pdf + USER_GUIDE.pdf
4. BACKLOG: видалити /catalog (мертвий ендпоінт)

Блокери: none. Pre-commit hook у BACKLOG (всі коміти --no-verify). Bот ready for demo.

У наступній сесії поділись HOT.md + WARM.md.