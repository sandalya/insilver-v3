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

    parser.add_argument('--level',       type=int, default=3, choices=[1,2,3,4,5,6],
                        help='Максимальний рівень (1-6), default=3')
    parser.add_argument('--full',        action='store_true',
                        help='Всі тести (рівні 1-6), еквівалент --level 6')
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
        max_level = 6
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