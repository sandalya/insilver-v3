#!/usr/bin/env python3
"""
🤖 Bot Manager — InSilver v3
Wrapper над systemctl для керування ботом.
PID логіка прибрана — systemd сам керує процесом.

USAGE:
  python3 tools/bot_manager.py status
  python3 tools/bot_manager.py restart
  python3 tools/bot_manager.py logs
  python3 tools/bot_manager.py logs --lines 50
  python3 tools/bot_manager.py follow
  python3 tools/bot_manager.py health
"""

import sys
import subprocess
import time
import argparse
from datetime import datetime

SERVICE = "insilver-v3"


def run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def is_active() -> bool:
    return run(["systemctl", "is-active", SERVICE]).stdout.strip() == "active"


# ─────────────────────────────────────────────────────────────
# Команди
# ─────────────────────────────────────────────────────────────

def cmd_status():
    result = run(["systemctl", "status", SERVICE])
    print(result.stdout or result.stderr)

    if is_active():
        print(f"✅ {SERVICE} — активний")
        props = run(["systemctl", "show", SERVICE,
                     "--property=MainPID,MemoryCurrent"])
        for line in props.stdout.strip().splitlines():
            key, _, val = line.partition("=")
            if key == "MainPID":
                print(f"📍 PID        : {val}")
            elif key == "MemoryCurrent" and val.isdigit():
                print(f"🧠 RAM        : {int(val)/1024/1024:.1f} MB")
    else:
        print(f"❌ {SERVICE} — не активний")

    ts = run(["systemctl", "show", SERVICE,
              "--property=ActiveEnterTimestamp"])
    val = ts.stdout.strip().replace("ActiveEnterTimestamp=", "")
    if val:
        print(f"⏰ Останній старт: {val}")


def cmd_start() -> bool:
    print(f"🚀 Запуск {SERVICE}...")
    result = run(["sudo", "systemctl", "start", SERVICE])
    if result.returncode == 0:
        time.sleep(2)
        if is_active():
            print("✅ Бот успішно запущений")
            return True
        print("⚠️  Запущено але не active — перевір логи")
        return False
    print(f"❌ Помилка: {result.stderr.strip()}")
    return False


def cmd_stop() -> bool:
    print(f"🛑 Зупинка {SERVICE}...")
    result = run(["sudo", "systemctl", "stop", SERVICE])
    if result.returncode == 0:
        print("✅ Бот зупинений")
        return True
    print(f"❌ Помилка: {result.stderr.strip()}")
    return False


def cmd_restart() -> bool:
    print(f"🔄 Перезапуск {SERVICE}...")
    result = run(["sudo", "systemctl", "restart", SERVICE])
    if result.returncode == 0:
        time.sleep(3)
        if is_active():
            print("✅ Бот перезапущений")
            return True
        print("⚠️  Після рестарту не active — перевір логи")
        return False
    print(f"❌ Помилка: {result.stderr.strip()}")
    return False


def cmd_logs(lines: int = 30):
    result = run(["journalctl", "-u", SERVICE, f"-n{lines}", "--no-pager"])
    print(result.stdout or result.stderr)


def cmd_follow():
    print(f"📡 Live логи {SERVICE} (Ctrl+C для виходу)...\n")
    try:
        subprocess.run(["journalctl", "-u", SERVICE, "-f", "--no-pager"])
    except KeyboardInterrupt:
        print("\n👋 Вийшов")


def cmd_health() -> bool:
    state = run(["systemctl", "is-active", SERVICE]).stdout.strip()
    restarts = run(["systemctl", "show", SERVICE,
                    "--property=NRestarts"]).stdout.strip().replace("NRestarts=", "") or "?"
    print(f"{'✅' if state == 'active' else '❌'} Стан     : {state}")
    print(f"🔁 Рестарти : {restarts}")
    print(f"🕐 Час      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return state == "active"


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=f"Bot Manager — {SERVICE}")
    parser.add_argument("command",
        choices=["start", "stop", "restart", "status", "logs", "follow", "health"])
    parser.add_argument("--lines", type=int, default=30,
        help="Кількість рядків для logs (default=30)")
    args = parser.parse_args()

    dispatch = {
        "start":   lambda: sys.exit(0 if cmd_start()        else 1),
        "stop":    lambda: sys.exit(0 if cmd_stop()         else 1),
        "restart": lambda: sys.exit(0 if cmd_restart()      else 1),
        "status":  cmd_status,
        "logs":    lambda: cmd_logs(args.lines),
        "follow":  cmd_follow,
        "health":  lambda: sys.exit(0 if cmd_health()       else 1),
    }
    dispatch[args.command]()


if __name__ == "__main__":
    main()