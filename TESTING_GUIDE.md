# 🧪 InSilver Testing Guide

## Швидкий старт

```bash
# 1. Базове тестування (3.6s) — ловить 70% багів
python3 autotester.py --level 5

# 2. UI Workflow тестування (2-3s) — ловить UI/логіка баги  
./run_ui_tests.sh --quick

# 3. Повне тестування (якщо потрібно)
python3 autotester.py --full        # 7 рівнів + 31 бізнес-сценарій
./run_ui_tests.sh --full           # E2E workflow тестування
```

---

## Два тестери в системі

### 🔧 **Autotester** (основний)
- **7 рівнів:** Syntax → Imports → Basic → AI → Performance → Telegram → AI Quality
- **31 реальний сценарій** з клієнтських скрінів  
- **Швидкість:** 3.6 секунди
- **Використання:** `python3 autotester.py --level N`

### 🎭 **UI Workflow Tester** (додатковий)
- **E2E тестування** без Telegram API
- **Mock interactions** + file system + логіка
- **4 сценарії:** Complete Workflow, File System, Callbacks, AI
- **Використання:** `./run_ui_tests.sh --quick`

---

## Коли що запускати

### Перед кожним commit:
```bash
python3 autotester.py --level 3     # 2.1s — syntax, imports, basic
```

### Перед тестуванням нових фіч:
```bash
python3 autotester.py --level 5     # 3.6s — основне тестування
./run_ui_tests.sh --quick          # 2s — UI workflows
```

### Перед production deploy:
```bash
python3 autotester.py --full        # повне тестування
./run_ui_tests.sh --full           # E2E тестування
```

---

## Очікувані результати

✅ **Якщо пройшли обидва:** продукт готовий до мануального тестування, 80% базових багів відловлено

❌ **Якщо не пройшли:** не витрачай час на ручне тестування, спочатку виправ автотести

---

## Cost: ~$0.05 за повний цикл тестування

**Економія:** ~2-3 години ручного тестування на кожну ітерацію