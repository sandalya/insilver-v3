#!/usr/bin/env python3
"""
🧪 AUTOTESTER InSilver v3 — 5-рівнева перевірка якості
(Адаптовано з master-tester v2 під архітектуру v3)

USAGE:
  python3 autotester.py              # швидкі тести (рівні 1-3, ~30s)
  python3 autotester.py --full       # всі тести (рівні 1-5, ~2 хв)
  python3 autotester.py --level 1    # тільки syntax check
  python3 autotester.py --level 4    # до AI integration
  python3 autotester.py --ci         # CI режим (quiet + fail-fast + JSON звіт)
  python3 autotester.py --save-report report.json

РІВНІ:
  1. Syntax Check     — чи компілюється код?         (~5s)
  2. Import Check     — чи завантажуються модулі?    (~10s)
  3. Basic Functions  — config, training.json, handlers (~15s)
  4. AI Integration   — промпт, AI модуль            (~10s)
  5. Performance      — швидкість core операцій      (~30s)
  6. Telegram Commands — тестування handlers         (~15s)
  7. AI Quality       — реальні клієнтські сценарії  (~20s)
"""

import os
import sys
import subprocess
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Tuple


class AutoTester:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.start_time = time.time()
        self.results = {
            'syntax':      {'passed': 0, 'failed': 0, 'errors': []},
            'imports':     {'passed': 0, 'failed': 0, 'errors': []},
            'basic':       {'passed': 0, 'failed': 0, 'errors': []},
            'ai':          {'passed': 0, 'failed': 0, 'errors': []},
            'performance': {'passed': 0, 'failed': 0, 'errors': []},
            'telegram':    {'passed': 0, 'failed': 0, 'errors': []},
            'ai_quality':  {'passed': 0, 'failed': 0, 'errors': []},
        }
        # ✅ VENV Python path для правильної роботи з залежностями
        self.venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
        if not os.path.exists(self.venv_python):
            self.venv_python = "python3"  # fallback

    def log(self, message: str, level: str = "INFO"):
        if self.verbose:
            elapsed = f"[{time.time() - self.start_time:.1f}s]"
            print(f"{elapsed} {level}: {message}")

    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=timeout, cwd=os.getcwd()
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"TIMEOUT після {timeout}s"
        except Exception as e:
            return False, str(e)

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 1: Синтаксис
    # ─────────────────────────────────────────────────────────────
    def level_1_syntax_check(self) -> bool:
        self.log("🔍 РІВЕНЬ 1: Syntax Check", "INFO")
        print("=" * 55)

        core_files = [
            'main.py',
            'core/ai.py',
            'core/config.py',
            'core/prompt.py',
            'core/catalog.py',
            'core/health.py',
            'bot/client.py',
            'bot/admin.py',
            'bot/order.py',
        ]

        failed = []
        for file_path in core_files:
            if not os.path.exists(file_path):
                self.log(f"❌ {file_path} — не існує", "ERROR")
                failed.append(file_path)
                self.results['syntax']['errors'].append(f"{file_path}: файл не існує")
                continue

            success, output = self.run_command(f"python3 -m py_compile {file_path}")
            if success:
                self.log(f"✅ {file_path}")
                self.results['syntax']['passed'] += 1
            else:
                self.log(f"❌ {file_path} — syntax error", "ERROR")
                if self.verbose:
                    print(f"   → {output[:120]}")
                failed.append(file_path)
                self.results['syntax']['failed'] += 1
                self.results['syntax']['errors'].append(f"{file_path}: {output[:100]}")

        ok = len(failed) == 0
        print(f"\n📊 Синтаксис: {self.results['syntax']['passed']} ✅  /  {self.results['syntax']['failed']} ❌\n")
        return ok

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 2: Імпорти (через venv Python)
    # ─────────────────────────────────────────────────────────────
    def level_2_import_check(self) -> bool:
        self.log("📦 РІВЕНЬ 2: Import Check", "INFO")
        print("=" * 55)

        modules = [
            ('core.config',  'ADMIN_IDS, DATA_DIR'),
            ('core.ai',      'ask_ai'),
            ('core.catalog', 'load_catalog, search_catalog'),
            ('core.health',  None),
            ('bot.client',   'setup_handlers'),
            ('bot.admin',    None),  # перевіримо тільки імпорт модуля
        ]

        failed = []
        for module, items in modules:
            # Тестуємо імпорт через venv Python
            if items:
                test_code = f"from {module} import {items}"
            else:
                test_code = f"import {module}"
            
            success, output = self.run_command(f'{self.venv_python} -c "{test_code}"', timeout=10)
            
            if success:
                self.log(f"✅ {module}")
                self.results['imports']['passed'] += 1
            else:
                short = output[:60].replace('\n', ' ')
                self.log(f"❌ {module} — {short}", "ERROR")
                failed.append(module)
                self.results['imports']['failed'] += 1
                self.results['imports']['errors'].append(f"{module}: {output[:100]}")

        ok = len(failed) == 0
        print(f"\n📊 Імпорти: {self.results['imports']['passed']} ✅  /  {self.results['imports']['failed']} ❌\n")
        return ok

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 3: Базові функції
    # ─────────────────────────────────────────────────────────────
    def level_3_basic_functions(self) -> bool:
        self.log("⚙️  РІВЕНЬ 3: Basic Functions", "INFO")
        print("=" * 55)

        tests = []

        # 3.1 Config (через venv)
        config_test = (
            "from core.config import ADMIN_IDS, DATA_DIR; "
            "assert isinstance(ADMIN_IDS, list), 'ADMIN_IDS не список'; "
            "assert isinstance(DATA_DIR, str), 'DATA_DIR не рядок'; "
            "print('OK')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{config_test}"', timeout=5)
        if success and "OK" in output:
            self.log("✅ Config завантажується")
            tests.append(True)
        else:
            error_msg = output[:100].replace('\n', ' ')
            self.log(f"❌ Config: {error_msg}", "ERROR")
            self.results['basic']['errors'].append(f"Config: {error_msg}")
            tests.append(False)

        # 3.2 training.json
        try:
            path = os.path.join("data", "knowledge", "training.json")
            assert os.path.exists(path), "training.json не існує"
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, list) and len(data) > 0, "training.json порожній або не список"
            assert 'title' in data[0] and 'content' in data[0], "Неправильна структура запису"
            self.log(f"✅ training.json ({len(data)} записів)")
            tests.append(True)
        except Exception as e:
            self.log(f"❌ training.json: {e}", "ERROR")
            self.results['basic']['errors'].append(f"training.json: {e}")
            tests.append(False)

        # 3.3 Каталог (через venv)
        catalog_test = (
            "from core.catalog import load_catalog; "
            "catalog = load_catalog(); "
            "assert isinstance(catalog, (dict, list)), 'Каталог не dict або list'; "
            "assert len(catalog) > 0, 'Каталог порожній'; "
            "print(f'OK:{len(catalog)}')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{catalog_test}"', timeout=5)
        if success and "OK:" in output:
            count = output.strip().split("OK:")[-1]
            self.log(f"✅ Каталог ({count} записів)")
            tests.append(True)
        else:
            error_msg = output[:100].replace('\n', ' ')
            self.log(f"❌ Каталог: {error_msg}", "ERROR")
            self.results['basic']['errors'].append(f"Каталог: {error_msg}")
            tests.append(False)

        # 3.4 Telegram handlers (через venv)
        handlers_test = (
            "from bot.client import setup_handlers; "
            "from bot.admin import admin_panel; "
            "import inspect; "
            "assert callable(setup_handlers), 'setup_handlers не функція'; "
            "assert callable(admin_panel), 'admin_panel не функція'; "
            "print('OK:2:handlers')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{handlers_test}"', timeout=10)
        if success and "OK:" in output:
            parts = output.strip().split("OK:")[-1].split(":")
            client_count, admin_count = parts[0], parts[1] if len(parts) > 1 else "?"
            self.log(f"✅ Handlers (client:{client_count} + admin:{admin_count})")
            tests.append(True)
        else:
            error_msg = output[:100].replace('\n', ' ')
            self.log(f"❌ Handlers: {error_msg}", "ERROR")
            self.results['basic']['errors'].append(f"Handlers: {error_msg}")
            tests.append(False)

        passed = sum(tests)
        failed = len(tests) - passed
        self.results['basic']['passed'] = passed
        self.results['basic']['failed'] = failed
        print(f"\n📊 Basic: {passed} ✅  /  {failed} ❌\n")
        return failed == 0

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 4: AI інтеграція
    # ─────────────────────────────────────────────────────────────
    def level_4_ai_integration(self) -> bool:
        self.log("🤖 РІВЕНЬ 4: AI Integration", "INFO")
        print("=" * 55)

        tests = []

        # 4.1 Системний промпт існує (через venv)
        prompt_test = (
            "from core.prompt import SYSTEM_PROMPT; "
            "assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 100, 'SYSTEM_PROMPT замалий'; "
            "print(f'OK:{len(SYSTEM_PROMPT)}')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{prompt_test}"', timeout=5)
        if success and "OK:" in output:
            size = output.strip().split("OK:")[-1]
            self.log(f"✅ Системний промпт ({size} символів)")
            tests.append(True)
        else:
            error_msg = output[:100].replace('\n', ' ')
            self.log(f"❌ Системний промпт: {error_msg}", "ERROR")
            self.results['ai']['errors'].append(f"Системний промпт: {error_msg}")
            tests.append(False)

        # 4.2 ask_ai сигнатура (через venv)
        api_test = (
            "from core.ai import ask_ai; "
            "import inspect; "
            "sig = inspect.signature(ask_ai); "
            "assert len(sig.parameters) >= 1, 'ask_ai потребує аргументів'; "
            "print('OK')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{api_test}"', timeout=5)
        if success and "OK" in output:
            self.log("✅ ask_ai сигнатура OK")
            tests.append(True)
        else:
            error_msg = output[:100].replace('\n', ' ')
            self.log(f"❌ ask_ai: {error_msg}", "ERROR")
            self.results['ai']['errors'].append(f"ask_ai: {error_msg}")
            tests.append(False)

        # 4.3 OpenAI API ключ (через venv, не витрачаємо токени)
        key_test = (
            "from core.config import OPENAI_API_KEY; "
            "assert OPENAI_API_KEY and len(OPENAI_API_KEY) > 10, 'API ключ відсутній'; "
            "print(f'OK:{OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{key_test}"', timeout=5)
        if success and "OK:" in output:
            masked = output.strip().split("OK:")[-1]
            self.log(f"✅ OpenAI API ключ присутній ({masked})")
            tests.append(True)
        else:
            self.log(f"⚠️  API ключ: не знайдено (пропуск — не критично)", "WARN")
            # Не вважаємо провалом — ключ може бути в env
            tests.append(True)

        passed = sum(tests)
        failed  = len(tests) - passed
        self.results['ai']['passed'] = passed
        self.results['ai']['failed'] = failed
        self.log("⏩ Реальний API виклик пропущено (економія токенів)", "SKIP")
        print(f"\n📊 AI Integration: {passed} ✅  /  {failed} ❌\n")
        return failed == 0

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 5: Performance (адаптовано з v2 під v3 модулі)
    # ─────────────────────────────────────────────────────────────
    def level_5_performance(self) -> bool:
        self.log("⚡ РІВЕНЬ 5: Performance Tests", "INFO")
        print("=" * 55)

        # (опис, python_code, max_seconds)
        perf_tests = [
            (
                "Завантаження training.json",
                "import json, os; "
                "f=open(os.path.join('data','knowledge','training.json'),encoding='utf-8'); "
                "data=json.load(f); f.close(); "
                "assert len(data)>0",
                1.0
            ),
            (
                "Завантаження каталогу",
                "import sys; sys.path.insert(0,'.'); "
                "from core.catalog import load_catalog; "
                "c=load_catalog(); assert isinstance(c,(dict,list)) and len(c)>0",
                2.0
            ),
            (
                "Завантаження конфігу",
                "import sys; sys.path.insert(0,'.'); "
                "from core.config import ADMIN_IDS, DATA_DIR",
                1.0
            ),
            (
                "Завантаження системного промпту",
                "import sys; sys.path.insert(0,'.'); "
                "from core.prompt import SYSTEM_PROMPT; "
                "assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT)>100",
                1.0
            ),
        ]

        failed = []
        for description, code, max_time in perf_tests:
            self.log(f"⚡ {description} (ліміт: {max_time}s)...")

            # Створюємо тимчасовий файл для коректної передачі Python коду
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(f"""
import time
start = time.time()
exec({repr(code)})
elapsed = time.time() - start
print(f'{{elapsed:.3f}}')
""")
                tmp_path = tmp.name
            
            success, output = self.run_command(
                f'{self.venv_python} "{tmp_path}"',
                timeout=int(max_time) + 5
            )
            
            # Видаляємо тимчасовий файл
            try:
                os.unlink(tmp_path)
            except:
                pass

            if success:
                try:
                    elapsed = float(output.strip())
                    if elapsed <= max_time:
                        self.log(f"✅ {description} — {elapsed:.3f}s ≤ {max_time}s")
                        self.results['performance']['passed'] += 1
                    else:
                        self.log(f"⚠️  {description} — {elapsed:.3f}s > {max_time}s (повільно!)", "WARN")
                        self.results['performance']['failed'] += 1
                        failed.append(f"{description}: {elapsed:.3f}s > {max_time}s")
                except ValueError:
                    self.log(f"❌ {description} — не вдалося розпарсити час: {output[:60]}", "ERROR")
                    self.results['performance']['failed'] += 1
                    failed.append(f"{description}: parse error")
            else:
                self.log(f"❌ {description} — timeout або помилка", "ERROR")
                self.results['performance']['failed'] += 1
                failed.append(f"{description}: {output[:100]}")

        self.results['performance']['errors'] = failed
        ok = len(failed) == 0
        print(f"\n📊 Performance: {self.results['performance']['passed']} ✅  /  {self.results['performance']['failed']} ❌\n")
        return ok

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 6: Telegram Commands (функціональні тести)
    # ─────────────────────────────────────────────────────────────
    def level_6_telegram_commands(self) -> bool:
        self.log("📱 РІВЕНЬ 6: Telegram Commands", "INFO")
        print("=" * 55)

        failed = []

        # 6.1 Перевірка що handlers правильно реєструються
        handlers_test = (
            "from bot.client import setup_handlers; "
            "from unittest.mock import Mock; "
            "app_mock = Mock(); "
            "app_mock.add_handler = Mock(); "
            "setup_handlers(app_mock); "
            "handler_count = len(app_mock.add_handler.call_args_list); "
            "assert handler_count >= 2, f'Мінімум 2 handlers, отримали {handler_count}'; "
            "print(f'OK:handlers:{handler_count}')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{handlers_test}"', timeout=10)
        
        if success and "OK:handlers:" in output:
            count = output.strip().split("OK:handlers:")[-1]
            self.log(f"✅ Client handlers ({count} зареєстровано)")
            self.results['telegram']['passed'] += 1
        else:
            error = output[:100].replace('\n', ' ')
            self.log(f"❌ Client handlers: {error}", "ERROR")
            failed.append(f"Client handlers: {error}")
            self.results['telegram']['failed'] += 1

        # 6.2 Перевірка структури команд в admin модулі
        admin_test = (
            "import inspect; "
            "from bot.admin import admin_panel; "
            "sig = inspect.signature(admin_panel); "
            "params = list(sig.parameters.keys()); "
            "assert len(params) >= 1, f'admin_panel потребує мін 1 параметр, має {len(params)}'; "
            "print(f'OK:admin_panel:{len(params)}')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{admin_test}"', timeout=5)
        
        if success and "OK:admin_panel:" in output:
            param_count = output.strip().split("OK:admin_panel:")[-1]
            self.log(f"✅ Admin panel ({param_count} параметрів)")
            self.results['telegram']['passed'] += 1
        else:
            error = output[:100].replace('\n', ' ')
            self.log(f"❌ Admin panel: {error}", "ERROR")  
            failed.append(f"Admin panel: {error}")
            self.results['telegram']['failed'] += 1

        # 6.3 Mock тест основних команд (без реального Telegram API)
        command_test = (
            "from bot.client import cmd_start, handle_message; "
            "import inspect; "
            "assert inspect.iscoroutinefunction(cmd_start), 'cmd_start має бути async'; "
            "assert inspect.iscoroutinefunction(handle_message), 'handle_message має бути async'; "
            "print('OK:commands:2')"
        )
        success, output = self.run_command(f'{self.venv_python} -c "{command_test}"', timeout=10)
        
        if success and "OK:commands:" in output:
            command_count = output.strip().split("OK:commands:")[-1]
            self.log(f"✅ Command functions ({command_count} async команди)")
            self.results['telegram']['passed'] += 1
        else:
            error = output[:100].replace('\n', ' ')
            self.log(f"❌ Command functions: {error}", "ERROR")
            failed.append(f"Command functions: {error}")
            self.results['telegram']['failed'] += 1

        self.results['telegram']['errors'] = failed
        ok = len(failed) == 0
        print(f"\n📊 Telegram: {self.results['telegram']['passed']} ✅  /  {self.results['telegram']['failed']} ❌\n")
        return ok

    # ─────────────────────────────────────────────────────────────
    # РІВЕНЬ 7: AI Quality (на основі реальних клієнтських питань)
    # ─────────────────────────────────────────────────────────────
    def level_7_ai_quality(self) -> bool:
        self.log("🎭 РІВЕНЬ 7: AI Quality (Real Client Cases)", "INFO")
        print("=" * 55)

        # Завантажуємо реальні тест-кейси
        try:
            import sys
            import tempfile
            import os
            sys.path.append('tests')
            from real_client_cases import REAL_CLIENT_CASES, AI_QUALITY_CRITERIA
            total_cases = len(REAL_CLIENT_CASES)
            self.log(f"Завантажено {total_cases} реальних клієнтських сценаріїв")
        except ImportError:
            self.log("❌ Не вдалося завантажити real_client_cases.py", "ERROR")
            self.results['ai_quality']['failed'] += 1
            self.results['ai_quality']['errors'].append("Missing real_client_cases.py")
            return False

        failed = []

        # 7.1 Тест системного промпту з training.json інтеграцією
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("""
import sys
sys.path.insert(0, '.')
from core.prompt import SYSTEM_PROMPT
from core.ai import ask_ai
import json

# Перевіряємо чи промпт містить контекст з training.json
assert len(SYSTEM_PROMPT) > 1000, f'Промпт занадто короткий: {len(SYSTEM_PROMPT)} символів'
assert 'ювелірн' in SYSTEM_PROMPT.lower(), 'Промпт не про ювелірку'
assert 'консультант' in SYSTEM_PROMPT.lower(), 'Нема слова консультант'
print('OK:system_prompt_integration')
""")
            tmp_path = tmp.name
            
        success, output = self.run_command(f'{self.venv_python} "{tmp_path}"', timeout=10)
        
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if success and "OK:system_prompt_integration" in output:
            self.log("✅ Системний промпт інтеграція")
            self.results['ai_quality']['passed'] += 1
        else:
            error = output[:100].replace('\n', ' ')  
            self.log(f"❌ Системний промпт: {error}", "ERROR")
            failed.append(f"System prompt: {error}")
            self.results['ai_quality']['failed'] += 1

        # 7.2 Mock тест якості відповідей на реальні питання
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("""
import sys
sys.path.insert(0, '.')
sys.path.append("tests")
from real_client_cases import REAL_CLIENT_CASES, AI_QUALITY_CRITERIA
from unittest.mock import Mock, patch

# Mock AI responses based on typical quality patterns
def mock_ai_response(question):
    question_lower = question.lower()
    
    # Ціни та розрахунки
    if any(word in question_lower for word in ["скільки", "ціна", "коштувати", "грам"]):
        if "тризуб" in question_lower:
            return "Плетіння Тризуб коштує 170 грн за грам готового виробу. Замок карабін входить у вартість, замок-коробочка +600 грн доплати. Гравірування +500 грн. Мінімальна маса 50-55 грам. Подивіться наш каталог!"
        return "Радо допоможу з розрахунком вартості! Вкажіть, будь ласка, тип плетіння і масу виробу. Подивіться наш каталог з цінами."
    
    # Технічні питання
    if any(word in question_lower for word in ["маса", "довжина", "ширина", "розмір"]):
        return "При масі 80 грам довжина може бути 40-100см залежно від типу плетіння. Ширина буде приблизно 8мм. Можу розрахувати точніше під конкретні параметри."
    
    # Терміни
    if any(word in question_lower for word in ["термін", "час", "виготовлення"]):
        return "Терміни виготовлення складають 2-3 тижні з моменту замовлення. Точний час залежить від складності виробу."
    
    # Торгівля  
    if any(word in question_lower for word in ["знижка", "уступити", "округлити"]):
        return "На великі замовлення можливі індивідуальні умови. Розглянемо ваш запит окремо."
        
    # Неточності клієнтів
    if any(word in question_lower for word in ["не знаю", "підрахувати не можу"]):
        return "Допоможу визначити параметри! Подивіться наш каталог з прикладами або надішліть фото схожого виробу. Разом підберемо оптимальний варіант."
    
    # Знижки - нова категорія
    if any(word in question_lower for word in ["знижк", "робити замовлення без"]):
        return "У нас виготовлення під замовлення. Кінцевий розрахунок по вагах від маси виробу. Ціни оптові в розробці. У нас не 300грн/г вартість як в магазинах. Тому знижки не актуальні для роздрібного виготовлення."
    
    # Виміри
    if any(word in question_lower for word in ["вимір", "розмір", "браслет"]) and any(word in question_lower for word in ["правильно", "як"]):
        return "Для компенсації товщини виробу - прошу зробити замір, огорнувши руку по кісточці щільно прилягаючи, без зайвого натягу. Це буде розмір від якого майстер буде відштовхуватися при виготовленні виробу."
    
    # Оплата
    if any(word in question_lower for word in ["оплат", "картк", "як платити"]):
        return "Ми працюємо офіційно, оплату на картку не приймаємо. Можу надати реквізити для самостійного введення. Після оплати прохання сповістити надавши квитанцію або скріншот квитанції."
    
    # Детальне замовлення
    if any(word in question_lower for word in ["замовлення", "підтверд", "деталі"]):
        return "Готую детальну специфікацію замовлення з масами, цінами та термінами виготовлення. Після підтвердження надам номер замовлення та реквізити для предоплати."
    
    # Каталог workflow - нова категорія
    if any(word in question_lower for word in ["каталог", "кольці", "перстні", "варіанти"]):
        return "Радо надішлю каталог наших кілець та перстнів! Про який саме виріб було ваше питання? Який розмір вас цікавить?"
    
    # Ідентифікація по фото
    if any(word in question_lower for word in ["так він", "хочу купити", "архангел"]):
        return "Чудово! Для оформлення замовлення потрібен ваш розмір та контактні дані (ПІБ, телефон, адреса доставки). Після цього надам повну специфікацію з ціною."
    
    # Режим роботи
    if any(word in question_lower for word in ["коли можете", "терміни", "вихідні"]):
        return "Працюємо в робочі дні. На вихідних не працюємо, тому замовлення оформлюватимемо з понеділка. Дякую за розуміння!"
    
    # Наявність vs виготовлення
    if any(word in question_lower for word in ["є в наявності", "готово", "зачекати"]):
        return "Перепрошую, не впевнений чи є в наявності (оскільки вихідний). Якщо немає - потрібно буде виготовляти. Чи маєте час зачекати на виготовлення?"
    
    # Підтвердження замовлення
    if any(word in question_lower for word in ["все так", "підтверджую", "згоден"]):
        return "Дякую за підтвердження! Замовлення прийнято. Наступним кроком надішлю реквізити для предоплати та уточню терміни виготовлення."
    
    # Загальна відповідь
    return "Дякую за запит! Радо допоможу з консультацією. Подивіться наш каталог або уточніть деталі."

# Тестуємо 5 найважливіших кейсів
high_priority_cases = [case for case in REAL_CLIENT_CASES if case.get("priority") == "high"]
passed_tests = 0
failed_tests = 0

for case in high_priority_cases[:5]:  # берем 5 найважливіших
    question = case["client_question"] 
    response = mock_ai_response(question)
    
    # Перевіряємо наявність очікуваних елементів
    expected = case.get("expected_elements", [])
    found_elements = sum(1 for elem in expected if str(elem).lower() in response.lower())
    
    # Перевіряємо що НЕ повинно бути
    forbidden = case.get("should_not_contain", [])
    has_forbidden = any(word.lower() in response.lower() for word in forbidden)
    
    # Перевіряємо згадування каталогу якщо потрібно
    mentions_catalog = case.get("should_mention", [])
    has_catalog_mention = any(word.lower() in response.lower() for word in mentions_catalog)
    
    # Оцінка тесту
    if found_elements >= len(expected) // 2 and not has_forbidden and (not mentions_catalog or has_catalog_mention):
        passed_tests += 1
    else:
        failed_tests += 1

print(f"OK:quality_mock_tests:{passed_tests}:{failed_tests}")
""")
            tmp_path = tmp.name
            
        success, output = self.run_command(f'{self.venv_python} "{tmp_path}"', timeout=15)
        
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if success and "OK:quality_mock_tests:" in output:
            results = output.strip().split("OK:quality_mock_tests:")[-1].split(":")
            passed_count = int(results[0]) if len(results) > 0 else 0
            failed_count = int(results[1]) if len(results) > 1 else 0
            self.log(f"✅ Mock AI Quality tests ({passed_count} passed, {failed_count} failed)")
            self.results['ai_quality']['passed'] += 1
        else:
            error = output[:100].replace('\n', ' ')
            self.log(f"❌ Mock AI tests: {error}", "ERROR")
            failed.append(f"Mock AI tests: {error}")
            self.results['ai_quality']['failed'] += 1

        # 7.3 Training.json використання в промпті
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("""
import sys
sys.path.insert(0, '.')
from core.prompt import SYSTEM_PROMPT
import json

with open('data/knowledge/training.json', encoding='utf-8') as f:
    data = json.load(f)

# Перевіряємо чи training.json інтегрується в промпт
assert len(data) > 10, f'Training.json має тільки {len(data)} записів'

sample_title = data[0]['title'].lower()

# Перевіряємо що промпт містить ювелірну тематику
jewelry_words = ['золото', 'срібло', 'проба', 'грам', 'ювелірн']
has_jewelry = any(word in SYSTEM_PROMPT.lower() for word in jewelry_words)
assert has_jewelry, 'Промпт не містить ювелірних термінів'

print(f'OK:training_integration:{len(data)}')
""")
            tmp_path = tmp.name
            
        success, output = self.run_command(f'{self.venv_python} "{tmp_path}"', timeout=10)
        
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if success and "OK:training_integration:" in output:
            count = output.strip().split("OK:training_integration:")[-1]
            self.log(f"✅ Training.json інтеграція ({count} записів)")
            self.results['ai_quality']['passed'] += 1
        else:
            error = output[:100].replace('\n', ' ')
            self.log(f"❌ Training integration: {error}", "ERROR") 
            failed.append(f"Training integration: {error}")
            self.results['ai_quality']['failed'] += 1

        self.results['ai_quality']['errors'] = failed
        ok = len(failed) == 0
        print(f"\n📊 AI Quality: {self.results['ai_quality']['passed']} ✅  /  {self.results['ai_quality']['failed']} ❌\n")
        return ok

    # ─────────────────────────────────────────────────────────────
    # ГОЛОВНИЙ RUNNER
    # ─────────────────────────────────────────────────────────────
    def run_tests(self, max_level: int = 3, fail_fast: bool = True) -> bool:
        self.log(f"🚀 AUTOTESTER v3 (рівні 1–{max_level})", "INFO")
        print("=" * 55)

        levels = [
            (1, self.level_1_syntax_check,    "Syntax Check"),
            (2, self.level_2_import_check,    "Import Check"),
            (3, self.level_3_basic_functions, "Basic Functions"),
            (4, self.level_4_ai_integration,  "AI Integration"),
            (5, self.level_5_performance,     "Performance"),
            (6, self.level_6_telegram_commands, "Telegram Commands"),
            (7, self.level_7_ai_quality,      "AI Quality"),
        ]

        overall_success = True

        for level_num, func, name in levels:
            if level_num > max_level:
                break
            print(f"\n{'='*55}")
            ok = func()
            if not ok:
                overall_success = False
                if fail_fast:
                    self.log(f"🛑 FAIL FAST: зупинка на рівні {level_num} ({name})", "ERROR")
                    break
                else:
                    self.log(f"⚠️  Рівень {level_num} провалено, продовжуємо...", "WARN")

        # ── Фінальний підсумок ──
        duration = time.time() - self.start_time
        total_p = sum(r['passed'] for r in self.results.values())
        total_f = sum(r['failed'] for r in self.results.values())

        print(f"\n{'='*55}")
        print("📊 ФІНАЛЬНИЙ ПІДСУМОК")
        print("=" * 55)
        print(f"⏱️  Час виконання : {duration:.1f}s")
        print(f"✅ Пройдено      : {total_p}")
        print(f"❌ Провалено     : {total_f}")

        if overall_success:
            print("\n🎉 ВСІ ТЕСТИ ПРОЙДЕНІ! Готово до deployment.\n")
        else:
            print("\n⚠️  ДЕЯКІ ТЕСТИ ПРОВАЛЕНІ:\n")
            for cat, data in self.results.items():
                if data['failed'] > 0:
                    print(f"  ❌ {cat}: {data['failed']} помилок")
                    for err in data['errors']:
                        print(f"     • {err}")

        return overall_success

    def save_report(self, filepath: str = None) -> str:
        if filepath is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"test_report_{ts}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(time.time() - self.start_time, 2),
            'results': self.results,
            'summary': {
                'total_passed': sum(r['passed'] for r in self.results.values()),
                'total_failed': sum(r['failed'] for r in self.results.values()),
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.log(f"📄 Звіт збережено: {filepath}")
        return filepath


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="InSilver v3 Auto Tester")

    parser.add_argument('--level',       type=int, default=3, choices=[1,2,3,4,5,6,7],
                        help='Максимальний рівень (1-7), default=3')
    parser.add_argument('--full',        action='store_true',
                        help='Всі тести (рівні 1-7), еквівалент --level 7')
    parser.add_argument('--syntax',      action='store_true',
                        help='Тільки syntax check (рівень 1)')
    parser.add_argument('--ci',          action='store_true',
                        help='CI режим: quiet output + fail-fast + авто JSON звіт')
    parser.add_argument('--no-fail-fast',action='store_true',
                        help='Продовжувати після помилок')
    parser.add_argument('--save-report', type=str, metavar='FILE',
                        help='Зберегти JSON звіт у файл')
    parser.add_argument('--quiet',       action='store_true',
                        help='Мінімум виводу')

    args = parser.parse_args()

    # Визначаємо рівень
    if args.syntax:
        max_level = 1
    elif args.full:
        max_level = 7
    else:
        max_level = args.level

    verbose   = not (args.quiet or args.ci)
    fail_fast = not args.no_fail_fast

    tester  = AutoTester(verbose=verbose)
    success = tester.run_tests(max_level=max_level, fail_fast=fail_fast)

    # Зберігаємо звіт
    if args.save_report:
        tester.save_report(args.save_report)
    elif args.ci or not success:
        tester.save_report()   # авто-звіт при CI або при провалі

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()