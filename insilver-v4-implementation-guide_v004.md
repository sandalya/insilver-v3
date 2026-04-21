# InSilver v3 — Покрокова інструкція (v004, актуальна)

**Для:** Claude Sonnet (виконавець)
**Від:** Claude Opus (архітектор)
**Дата оновлення:** 2026-04-20 (після ініціалізації HOT/WARM/COLD)
**Проект:** `/home/sashok/.openclaw/workspace/insilver-v3/`
**Сервіс:** `insilver-v3.service`
**Рестарт:** `sudo systemctl restart insilver-v3`

---

## ПРАВИЛА РОБОТИ

1. **SSH:** НІКОЛИ base64. `sed` для малих змін (<20 рядків). `cat > /tmp/patch.py << 'PYEOF'` + `python3 /tmp/patch.py` для середніх (20–200). WinSCP для великих (>200). `\n` → `\\n` в triple-quoted strings.
2. **Після КОЖНОЇ команди:** `Якщо done/ok → Крок N — [команда]`
3. **Перед тестом бота:** нагадай запустити логи `sudo journalctl -u insilver-v3 -f`
4. **API ключі** маскувати. **Не scp, не nano для .md.**
5. **Коміт** після кожного блоку. Якщо pre-commit hook тестів червоний і ми не чіпали код — `--no-verify` ок.
6. **Ed QA** після великих блоків.
7. **Пам'ять — єдине джерело істини:** при старті сесії — `HOT.md` + `WARM.md`. НЕ спирайся на userMemories щодо стану проекту — файли свіжіші.

---

## Ed QA v2 — як працює

**Шлях:** `/home/sashok/.openclaw/workspace/ed/`
**Запуск:**
```bash
cd /home/sashok/.openclaw/workspace/ed && source venv/bin/activate && python3 main.py run --bot insilver --block <BLOCK_NAME> --transport telegram --judge haiku
```

**Тест-кейси:** `ed/suites/data/insilver/blocks/<block_name>.json`
**Рубрики:** `ed/judge/rubrics/insilver.py`
**Target:** `insilver=@insilver_v3_bot`
**Admin verify chat:** `ADMIN_VERIFY_CHAT_ID=8627781342` (id бота, куди дзеркаляться адмін-повідомлення)
**Reset:** `reset_command` з `config/bots.yaml` — виконується автоматично перед кейсом з `"reset_before": true`. Для insilver: `echo '{}' > /home/sashok/.openclaw/workspace/insilver-v3/data/handoff_state.json`. **Ручні echo між блоками НЕ потрібні.**

### Формат тестів

**Тип 1 — одиночне повідомлення:**
```json
{
  "id": "unique_id",
  "input": "текст боту",
  "expect": "очікувана поведінка",
  "tags": ["tag"]
}
```

**Тип 2 — multi-step:**
```json
{
  "id": "unique_id",
  "category": "order_funnel",
  "reset_before": true,
  "steps": [
    {"action": "send", "text": "/order", "assertions": [{"type": "no_error"}, {"type": "has_buttons", "value": true}]},
    {"action": "click_intent", "intent": "Ланцюжок", "assertions": [{"type": "no_error"}]},
    {"action": "send", "text": "30", "assertions": [{"type": "text_contains", "value": "покриття"}]}
  ],
  "context": "Опис що тестуємо",
  "tags": ["funnel"]
}
```

### Actions (Ed v2 runner)

- `send` — відправити текст
- `click_intent` — натиснути кнопку через семантичний matcher (Haiku temp=0, confidence threshold 0.7, кеш у `data/intent_logs/`)
- `click_button` — натиснути кнопку по точному/частковому тексту (без Haiku)
- `photo` — відправити фото (⚠️ **НЕ `send_photo`** — це стара назва з v003)
- `wait` — пауза N секунд (для асинхронних операцій)

### Assertions (Ed v2)

- `no_error` — бот відповів без помилки
- `has_buttons` — відповідь містить inline кнопки
- `text_contains` — відповідь містить підрядок (`value: "..."`)
- `text_not_contains` — відповідь НЕ містить підрядок
- `text_matches` — regex match по відповіді
- `button_present` / `button_count` — перевірка конкретних кнопок
- `has_photos` / `photo_count` — перевірка фото у відповіді
- `response_time` — максимальний час відповіді в мс
- `admin_received` — адмін отримав дзеркальне повідомлення (через `ADMIN_VERIFY_CHAT_ID`)
- `no_bot_response` — бот мовчить (для handoff/pause)
- `price_in_range` — витягнена ціна в діапазоні `{min, max}`
- `order_saved` — запис з'явився в `data/orders/orders.json`

### ⚠️ click_intent — matching

Ed шукає кнопку по частковому збігу тексту (case-insensitive), emoji ігноруються:
- `"⛓️ Ланцюжок"` → intent `"Ланцюжок"` ✅
- `"⚪️ Срібло біле"` → intent `"Срібло біле"` ✅
- `"📦 Коробочка 600грн"` → intent `"Коробочка"` ✅
- `"✍️ Є коментар"` → intent `"Є коментар"` ✅

Текст має бути достатньо унікальним щоб не збігатися з іншою кнопкою.

---

## ПОТОЧНИЙ СТАН (з HOT.md / WARM.md, 2026-04-20)

### ✅ Промпт і guardrails — ЗРОБЛЕНО
- Мультимовність: розуміє всі мови, НІКОЛИ не відповідає російською
- Guardrails: тільки срібло 925, не додавати зайвих елементів, релігійні вироби тільки з бази
- Ed `07_prompt_guardrails` — **green** ✅

### ✅ Воронка замовлення — ЗРОБЛЕНО (дві системи)

**Основна (`build_order_handler`)** — зареєстрована ПЕРШОЮ:
- 8 типів виробів (з `core/order_config.py`): ланцюжок, браслет, хрестик, кулон, обручка, перстень, набір, інше
- Ланцюжок: плетіння → довжина → маса → покриття → застібка → додатково → контакт → коментар
- Браслет: аналогічно
- Хрестик: тип → маса → додатково → контакт → коментар
- Кулон / Перстень / Обручка / Набір: кожен свій набір кроків
- `_waiting_custom` для обробки "✏️ Інше"
- Кнопки "⬅️ Назад" і "❌ Скасувати" на кожному кроці

**Нова (`build_new_order_handler`, nb_*)** — запасна, тільки ланцюжок/браслет, з калькулятором і summary.

### ✅ Калькулятор — ЗРОБЛЕНО
- `core/pricing.py` (`calculate_price`, `format_price`, `get_price_per_gram`)
- `data/pricing.json`
- Працює в новій воронці

### ✅ Human Handoff — ЗРОБЛЕНО
- `core/handoff.py` — pause/resume
- `handle_photo` — фото → адміну + пауза
- `handle_resume` — callback для адміна
- Ed `09_handoff` — **green** ✅

### ✅ Keyword detection — ЗРОБЛЕНО
- `bot/client.py:207` — `HUMAN_TRIGGERS` (людина/менеджер/майстер...)
- `bot/client.py:229` — `COMPLEX_KEYWORDS`
- Працює в `handle_message` — поза ConversationHandler, тому не конфліктує з воронкою

### ✅ Smart Router — ЗРОБЛЕНО
- `core/router.py` — Haiku класифікує intent на SEARCH / QUESTION / ORDER / SOCIAL
- Каталог показується тільки для SEARCH

### ❌ Ed intent cache bug — НЕ ЗАФІКСОВАНО
- Між запусками кеш `data/intent_logs/` дає хибні результати
- Після `Ланцюжок→плетіння` Ed плутає Бісмарк з іншими плетіннями

### ❌ Кнопка "Інше" не просить текст — НЕ ЗАФІКСОВАНО
- Після натискання "✏️ Інше" бот має увійти в `_waiting_custom` і попросити ввести текст
- Зараз — не просить (баг у `bot/order.py`)

### ❌ Ed `10_order_funnel` — блокований двома багами вище

### ⚠️ Summary в старій воронці — НЕ ЗРОБЛЕНО (опціонально)
- Стара воронка створює ордер без попереднього зведення
- Нова має summary + кнопки підтвердження

### ⚠️ Handoff `Chat not found` edge case — НЕ ЗАФІКСОВАНО
- Після рестарту бота peer може бути не в кеші PTB
- `ctx.bot.send_message(admin_id)` падає з `Chat not found`
- Потрібен try/except з fallback або прогрів кешу

---

## ЩО ТРЕБА ЗРОБИТИ

### ЗАДАЧА 1: Зафіксити баг кнопки "Інше" в старій воронці

**Файл:** `bot/order.py`, логіка `_waiting_custom`
**Симптом:** натискання "✏️ Інше" не переводить в режим очікування тексту. Бот або ігнорує, або йде далі по воронці.

**Кроки:**

1. Знайти callback handler для кнопки "Інше":
```bash
grep -n "waiting_custom\|Інше\|custom_input" /home/sashok/.openclaw/workspace/insilver-v3/bot/order.py
```

2. Читати контекст навколо знайдених рядків — з'ясувати чи ставиться `_waiting_custom=True` в user_data і чи перевіряється на наступному message handler.

3. Типовий фікс: в callback кнопки "Інше" додати
```python
context.user_data["_waiting_custom"] = True
context.user_data["_waiting_custom_field"] = <field_name>  # довжина, покриття, тощо
await query.edit_message_text("Напишіть, будь ласка, ваш варіант одним повідомленням:")
return <SAME_STATE>  # лишаємось на тому ж кроці воронки
```
і в text handler того ж стейту:
```python
if context.user_data.get("_waiting_custom"):
    field = context.user_data.pop("_waiting_custom_field")
    context.user_data[field] = update.message.text
    context.user_data.pop("_waiting_custom")
    return await <next_step>(update, context)
```

4. Рестарт і ручна перевірка:
```bash
sudo systemctl restart insilver-v3 && sleep 3 && sudo journalctl -u insilver-v3 -f
```
Далі `/order → Ланцюжок → Бісмарк → ✏️ Інше → ввести "47" → бот приймає як довжину`.

5. Коміт:
```bash
cd /home/sashok/.openclaw/workspace/insilver-v3 && git add -A && git commit -m "fix(order): 'Інше' button enters _waiting_custom and accepts free text"
```

---

### ЗАДАЧА 2: Розібратись з Ed intent cache bug

**Симптом:** між запусками `click_intent` дає хибний результат — Ed клацає не ту кнопку.

**Гіпотези (порядок перевірки):**

1. **Кеш у `ed/data/intent_logs/` не інвалідує ключ коли набір кнопок змінився.** Ключ кешу може бути лише за текстом intent, без хешу кнопок.
```bash
ls -la /home/sashok/.openclaw/workspace/ed/data/intent_logs/ | head -20
cat /home/sashok/.openclaw/workspace/ed/data/intent_logs/*.json 2>/dev/null | head -50
```

2. **Race condition:** після `send` бот ще не встиг відрендерити нові кнопки, а `click_intent` вже працює зі старим markup.
Фікс: додати `wait` перед `click_intent` або збільшити timeout у `runner/engine.py`.

3. **Stale markup у Telethon** — отримує старе повідомлення замість нового.
Перевірити в `transports/telegram.py` як беремо останнє повідомлення.

**Швидка діагностика:**
```bash
# Прогнати один кейс з verbose
cd /home/sashok/.openclaw/workspace/ed && source venv/bin/activate && python3 main.py run --bot insilver --block 10_order_funnel --transport telegram --judge haiku --verbose 2>&1 | tee /tmp/ed_verbose.log
```

Подивитись на `/tmp/ed_verbose.log` — видно буде який markup Ed бачить на кожному кроці і що Haiku повертає.

**Workaround поки фікс не знайдений:** додати `{"action": "wait", "seconds": 1}` перед критичними `click_intent`.

**Потім очистити кеш і прогнати знову:**
```bash
rm -rf /home/sashok/.openclaw/workspace/ed/data/intent_logs/*
```

---

### ЗАДАЧА 3: Оновити `10_order_funnel.json` з реальними assertions

Поточні тести мають тільки `no_error` + `has_buttons`. Це слабко — не перевіряє що бот показав правильну ціну, зберіг ордер, дзеркалив адміну. Треба додати `text_contains`, `price_in_range`, `order_saved`, `admin_received` у фінальних кроках.

**Створити файл через WinSCP:** `/home/sashok/.openclaw/workspace/ed/suites/data/insilver/blocks/10_order_funnel.json` (окремий вивід підготую в наступному кроці після того як Задача 1 і 2 закриті — щоб не переписувати двічі).

---

### ЗАДАЧА 4: Повна регресія Ed (без ручних echo)

```bash
cd /home/sashok/.openclaw/workspace/ed && source venv/bin/activate

# Smoke
python3 main.py run --bot insilver --block 01_smoke --transport telegram --judge haiku

# Pricing
python3 main.py run --bot insilver --block 02_pricing --transport telegram --judge haiku

# Catalog
python3 main.py run --bot insilver --block 03_catalog --transport telegram --judge haiku

# Delivery
python3 main.py run --bot insilver --block 04_delivery --transport telegram --judge haiku

# Orders (legacy)
python3 main.py run --bot insilver --block 06_orders --transport telegram --judge haiku

# Guardrails
python3 main.py run --bot insilver --block 07_prompt_guardrails --transport telegram --judge haiku

# Injections
python3 main.py run --bot insilver --block 08_injections --transport telegram --judge haiku

# Handoff
python3 main.py run --bot insilver --block 09_handoff --transport telegram --judge haiku

# Воронка
python3 main.py run --bot insilver --block 10_order_funnel --transport telegram --judge haiku
```

**`reset_command` з `config/bots.yaml` автоматично скидає handoff_state.json перед кейсами з `reset_before: true`.**

**Ціль:** всі 9 блоків зелені (або ≥8 з 9 при невеликих edge cases).

---

### ЗАДАЧА 5: Handoff `Chat not found` — edge case

**Симптом:** після рестарту `insilver-v3.service` перший `handle_photo` падає з `telegram.error.BadRequest: Chat not found` на `ctx.bot.send_message(admin_id, ...)`.

**Причина:** PTB кеш peer-ів пустий після рестарту. Якщо адмін ще не писав боту в цій сесії — peer не знайдено.

**Фікс у `core/handoff.py` (або `core/photo.py` де шлеться адміну):**
```python
try:
    await ctx.bot.send_message(admin_id, text)
except telegram.error.BadRequest as e:
    if "Chat not found" in str(e):
        logger.warning(f"Admin {admin_id} not in PTB peer cache yet — "
                       f"admin needs to send /start to bot once after restart")
        # Fallback: спробувати через send_chat_action для прогріву
        try:
            await ctx.bot.send_chat_action(admin_id, "typing")
            await ctx.bot.send_message(admin_id, text)
        except Exception:
            logger.error(f"Admin {admin_id} unreachable, handoff notification lost")
    else:
        raise
```

**Валідація:** перезавантажити бота, одразу надіслати фото клієнтом, подивитись логи — має бути warning а не crash, і при повторній спробі (коли адмін активний) — доставитись.

---

### ЗАДАЧА 6: Summary у старій воронці (опціонально, не блокує реліз)

Перенести паттерн з нової воронки (`bot/order.py`, функція `build_new_order_handler`, блок summary) в `finish_order()` старої:
1. Замість одразу `save_order(...)` — показати зведення з калькулятором
2. Кнопки "✅ Підтвердити" / "✏️ Редагувати" / "❌ Скасувати"
3. Після підтвердження — `save_order` + дзеркало адміну

Можна робити після релізу v3 Владу — не блокуюча задача.

---

## ЧЕКЛІСТ (для закриття v3)

- [ ] Задача 1 — кнопка "Інше" просить текст і приймає його у всіх воронках (ланцюжок, браслет, покриття, тощо)
- [ ] Задача 2 — Ed intent cache більше не плутає Бісмарк і інші плетіння між запусками
- [ ] Задача 3 — `10_order_funnel.json` з повним набором assertions
- [ ] Задача 4 — всі 9 Ed блоків зелені
- [ ] Задача 5 — `Chat not found` більше не валить бота після рестарту
- [ ] Ручна перевірка: `/order` → хрестик → повний флоу → замовлення в `data/orders/orders.json`
- [ ] Ручна перевірка: `/order` → ланцюжок → "✏️ Інше" на довжині → бот приймає текст
- [ ] Ручна перевірка: Фото → адміну → пауза → "Повернути бота" → бот продовжує
- [ ] Показати Владу: `/admin` + `/orders`
- [ ] Pricing від Влада — остаточні ціни в `data/pricing.json`
- [ ] Оновити `HOT.md` перед чекпоінтом

---

## БЕКЛОГ InSilver v3 (після релізу)

- Summary в стару воронку (Задача 6 з цього доку)
- RAG замість плоского `training.json` (15 Q&A → векторна БД) — для масштабування під більше продуктів
- Pricing editor в `/admin` — щоб Влад міг сам редагувати ціни без розгортання
- Photo analysis: клієнт присилає фото — Claude описує що це, пропонує схоже з каталогу

---

## InSilver v4 — що стартує після закриття v3

Це окрема гілка, поки не чіпати. Коли почнемо — перша дія: зробити v005 цього доку з реальним планом v4.

---

## ФІНАЛЬНИЙ ЧЕКПОІНТ (коли чекліст зелений)

```
chkp insilver-v3 "Ed зелений, 'Інше' фікс, intent cache фікс, Chat not found фікс, повна регресія" "Summary в стару воронку (опц), показати Владу /admin /orders, pricing від Влада" "v3 production ready. Ed: 9 блоків ≥8 green. Воронка: 8 типів, 'Інше' працює. Handoff: photo+complex+human + Chat not found resilient."
```