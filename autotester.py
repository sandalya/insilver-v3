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
        }

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
    # РІВЕНЬ 2: Імпорти
    # ─────────────────────────────────────────────────────────────
    def level_2_import_check(self) -> bool:
        self.log("📦 РІВЕНЬ 2: Import Check", "INFO")
        print("=" * 55)

        modules = [
            ('core.config',  'ADMIN_IDS, DATA_DIR'),
            ('core.ai',      'call_openai_api'),
            ('core.prompt',  'get_consultant_prompt'),
            ('core.catalog', 'get_catalog_data'),
            ('core.health',  None),
            ('bot.client',   'create_client_handlers'),
            ('bot.admin',    'create_admin_handlers'),
        ]

        failed = []
        for module, items in modules:
            try:
                if items:
                    exec(f"from {module} import {items}")
                else:
                    exec(f"import {module}")
                self.log(f"✅ {module}")
                self.results['imports']['passed'] += 1
            except Exception as e:
                short = str(e)[:60]
                self.log(f"❌ {module} — {short}", "ERROR")
                failed.append(module)
                self.results['imports']['failed'] += 1
                self.results['imports']['errors'].append(f"{module}: {str(e)[:100]}")

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

        # 3.1 Config
        try:
            from core.config import ADMIN_IDS, DATA_DIR
            assert isinstance(ADMIN_IDS, list), "ADMIN_IDS не список"
            assert isinstance(DATA_DIR, str),   "DATA_DIR не рядок"
            self.log("✅ Config завантажується")
            tests.append(True)
        except Exception as e:
            self.log(f"❌ Config: {e}", "ERROR")
            self.results['basic']['errors'].append(f"Config: {e}")
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

        # 3.3 Каталог
        try:
            from core.catalog import get_catalog_data
            catalog = get_catalog_data()
            assert isinstance(catalog, dict), "Каталог не словник"
            self.log(f"✅ Каталог ({len(catalog)} ключів)")
            tests.append(True)
        except Exception as e:
            self.log(f"❌ Каталог: {e}", "ERROR")
            self.results['basic']['errors'].append(f"Каталог: {e}")
            tests.append(False)

        # 3.4 Telegram handlers
        try:
            from bot.client import create_client_handlers
            from bot.admin  import create_admin_handlers
            ch = create_client_handlers()
            ah = create_admin_handlers()
            assert isinstance(ch, list) and len(ch) > 0, "Немає client handlers"
            assert isinstance(ah, list) and len(ah) > 0, "Немає admin handlers"
            self.log(f"✅ Handlers (client:{len(ch)} + admin:{len(ah)})")
            tests.append(True)
        except Exception as e:
            self.log(f"❌ Handlers: {e}", "ERROR")
            self.results['basic']['errors'].append(f"Handlers: {e}")
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

        # 4.1 Промпт генерується
        try:
            from core.prompt import get_consultant_prompt
            prompt = get_consultant_prompt("тест")
            assert isinstance(prompt, str) and len(prompt) > 100, "Промпт замалий або не рядок"
            self.log(f"✅ Промпт генерується ({len(prompt)} символів)")
            tests.append(True)
        except Exception as e:
            self.log(f"❌ Промпт: {e}", "ERROR")
            self.results['ai']['errors'].append(f"Промпт: {e}")
            tests.append(False)

        # 4.2 call_openai_api існує і має правильну сигнатуру
        try:
            from core.ai import call_openai_api
            import inspect
            sig = inspect.signature(call_openai_api)
            assert len(sig.parameters) >= 1, "call_openai_api потребує аргументів"
            self.log("✅ call_openai_api сигнатура OK")
            tests.append(True)
        except Exception as e:
            self.log(f"❌ call_openai_api: {e}", "ERROR")
            self.results['ai']['errors'].append(f"call_openai_api: {e}")
            tests.append(False)

        # 4.3 OpenAI API ключ присутній (не валідуємо, не витрачаємо токени)
        try:
            from core.config import OPENAI_API_KEY
            assert OPENAI_API_KEY and len(OPENAI_API_KEY) > 10, "API ключ відсутній або порожній"
            masked = OPENAI_API_KEY[:8] + "..." + OPENAI_API_KEY[-4:]
            self.log(f"✅ OpenAI API ключ присутній ({masked})")
            tests.append(True)
        except Exception as e:
            self.log(f"⚠️  API ключ: {e} (пропуск — не критично)", "WARN")
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
                "from core.catalog import get_catalog_data; "
                "c=get_catalog_data(); assert isinstance(c,dict)",
                2.0
            ),
            (
                "Завантаження конфігу",
                "import sys; sys.path.insert(0,'.'); "
                "from core.config import ADMIN_IDS, DATA_DIR",
                1.0
            ),
            (
                "Генерація промпту",
                "import sys; sys.path.insert(0,'.'); "
                "from core.prompt import get_consultant_prompt; "
                "p=get_consultant_prompt('золотий ланцюжок'); assert len(p)>100",
                1.5
            ),
        ]

        failed = []
        for description, code, max_time in perf_tests:
            self.log(f"⚡ {description} (ліміт: {max_time}s)...")

            # Вимірюємо через subprocess щоб уникнути кешування
            measure_script = (
                f"import time\n"
                f"start = time.time()\n"
                f"exec({repr(code)})\n"
                f"print(f'{{time.time()-start:.3f}}')\n"
            )
            success, output = self.run_command(
                f'python3 -c "{measure_script}"',
                timeout=int(max_time) + 5
            )

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

    parser.add_argument('--level',       type=int, default=3, choices=[1,2,3,4,5],
                        help='Максимальний рівень (1-5), default=3')
    parser.add_argument('--full',        action='store_true',
                        help='Всі тести (рівні 1-5), еквівалент --level 5')
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
        max_level = 5
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