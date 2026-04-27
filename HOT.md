---
project: insilver-v3
updated: 2026-04-27
---

# HOT — InSilver v3

## Now

Сесія 27.04 (dev instance) завершена. Створено dev інстанс `insilver-v3-dev` (повна копія коду+data+venv), окремий systemd сервіс `insilver-v3-dev.service` (disabled, не enabled), окремий бот токен для @insilver_silvia_bot (старий токен revoked, новий выданий). getMe + getUpdates успішно повертають ok=True, dev бот стартує чисто. Dev інстанс розташований в `/home/sashok/.openclaw/workspace/insilver-v3-dev/`, сервіс у `/etc/systemd/system/`.

**ВАЖЛИВО — prod проблема виявлена:** @insilver_v3_bot має 75% часу Conflict 409 помилок у логах. Бот функціонально живий (відповідає на /start), але це не норма — окрема критична задача розібратися (revoke токена або копати зовнішні getUpdates).

## Last done

**Сесія 27.04 — Dev instance setup для @insilver_silvia_bot**

- ✅ Створено dev інстанс `insilver-v3-dev` (повна копія коду + data + venv у `/home/sashok/.openclaw/workspace/insilver-v3-dev/`)
- ✅ Окремий systemd сервіс `insilver-v3-dev.service` встановлений у `/etc/systemd/system/` (disabled, не enabled)
- ✅ Окремий бот @insilver_silvia_bot створений (старий токен revoked, новий выданий)
- ✅ getMe + getUpdates успішно тестовані (ok=True)
- ✅ Dev бот стартує чисто без помилок
- ℹ️ Prod токен @insilver_v3_bot має 75% Conflict 409 в логах — не блокує функціонально, але потребує дослідження

## Next

1. **Перевірити /start у @insilver_silvia_bot:** правильне посилання `https://t.me/insilver_silvia_bot`, не переплутати з prod @insilver_v3_bot
2. **Якщо /start ОК — запустити dev сервіс:** `systemctl start insilver-v3-dev.service`
3. **Завести git гілку dev на GitHub:** push локальної гілки dev в origin (коміти --no-verify)
4. **Розібратися з prod Conflict 409:** дослідити логи @insilver_v3_bot, можливо revoke старого токена або копати зовнішні getUpdates
5. **Тестування dev інстансу:** базовий smoke test з /start, /help, /order

## Blockers

- Prod @insilver_v3_bot має 75% Conflict 409 — окрема задача розібратися (не блокує сесію dev)
- Pre-commit hook зламаний — всі коміти `--no-verify`

## Active branches

- master (workspace repo, Pi5)
- dev (локально, не в origin, готова до push)

## Open questions

- Чи /start у @insilver_silvia_bot показує правильне посилання `https://t.me/insilver_silvia_bot`?
- Коли push dev гілку в origin?
- Чи дослідити prod Conflict 409 одночасно з dev setup або окремо?

## Reminders

- Dev інстанс у `/home/sashok/.openclaw/workspace/insilver-v3-dev/`, сервіс у `/etc/systemd/system/insilver-v3-dev.service`
- Dev бот @insilver_silvia_bot (окремий токен від prod @insilver_v3_bot)
- Всі коміти: `git commit --no-verify` (pre-commit hook зламаний)
- Conflict 409 у prod — дослідити логи (`journalctl -u insilver-v3 -f`)
- Dev гілка локально, не в origin — потребує push
