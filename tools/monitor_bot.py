#!/usr/bin/env python3
"""
👁️  Monitor Bot — InSilver v3
Health check кожні 5 хвилин + Telegram алерт при падінні.

Запускається як окремий systemd сервіс: insilver-monitor.service
Або вручну: python3 tools/monitor_bot.py

КОНФІГ (змінити тут або через ENV):
  ALERT_CHAT_ID  — Telegram chat_id куди слати алерти (зараз Сашко)
  CHECK_INTERVAL — інтервал перевірки в секундах (default: 300)
"""

import os
import sys
import time
import signal
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Конфіг — змінювати тільки тут
# ─────────────────────────────────────────────────────────────
SERVICE        = "insilver-v3"
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))   # 5 хвилин
BOT_DIR        = Path(__file__).parent.parent              # insilver-v3/
LOG_FILE       = BOT_DIR / "logs" / "monitor.log"
ENV_FILE       = BOT_DIR / ".env"

# Хто отримує алерти. Зараз — Сашко.
# Щоб переключити на Влада: змінити ALERT_CHAT_ID на його chat_id.
ALERT_CHAT_ID: str | None = os.getenv("ALERT_CHAT_ID", None)

# Завантажимо з .env якщо не в env
TELEGRAM_TOKEN: str | None = None

# ─────────────────────────────────────────────────────────────
# Утиліти
# ─────────────────────────────────────────────────────────────

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config():
    """Завантажує TELEGRAM_TOKEN і ALERT_CHAT_ID з .env"""
    global TELEGRAM_TOKEN, ALERT_CHAT_ID

    if not ENV_FILE.exists():
        log(f"⚠️  .env не знайдено: {ENV_FILE}")
        return False

    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("TELEGRAM_TOKEN="):
                TELEGRAM_TOKEN = line.split("=", 1)[1].strip()
            elif line.startswith("ALERT_CHAT_ID=") and not ALERT_CHAT_ID:
                ALERT_CHAT_ID = line.split("=", 1)[1].strip()

    if not TELEGRAM_TOKEN:
        log("❌ TELEGRAM_TOKEN не знайдено в .env")
        return False

    masked = TELEGRAM_TOKEN[:10] + "..."
    log(f"✅ Config завантажено (token: {masked}, alert_chat: {ALERT_CHAT_ID})")
    return True


# ─────────────────────────────────────────────────────────────
# Health checks
# ─────────────────────────────────────────────────────────────

def is_service_active() -> bool:
    """Перевіряє чи systemd сервіс активний"""
    result = subprocess.run(
        ["systemctl", "is-active", SERVICE],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "active"


def is_telegram_api_responding() -> bool:
    """Перевіряє чи бот відповідає через Telegram API /getMe"""
    if not TELEGRAM_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        resp = requests.get(url, timeout=10)
        return resp.status_code == 200 and resp.json().get("ok", False)
    except Exception:
        return False


def get_restart_count() -> str:
    """Повертає кількість рестартів сервісу"""
    result = subprocess.run(
        ["systemctl", "show", SERVICE, "--property=NRestarts"],
        capture_output=True, text=True
    )
    return result.stdout.strip().replace("NRestarts=", "") or "?"


# ─────────────────────────────────────────────────────────────
# Telegram алерт
# ─────────────────────────────────────────────────────────────

def send_alert(message: str):
    """Надсилає алерт в Telegram"""
    if not TELEGRAM_TOKEN or not ALERT_CHAT_ID:
        log(f"⚠️  Алерт не надіслано (немає token або chat_id): {message}")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": ALERT_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            log(f"📨 Алерт надіслано: {message[:60]}...")
        else:
            log(f"⚠️  Алерт не надіслано (HTTP {resp.status_code}): {resp.text[:100]}")
    except Exception as e:
        log(f"❌ Помилка надсилання алерту: {e}")


def format_alert(reason: str, restarted: bool, restart_count: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✅ перезапущено systemd" if restarted else "❌ НЕ вдалося перезапустити"
    return (
        f"🚨 <b>InSilver бот — проблема</b>\n\n"
        f"⏰ Час: {now}\n"
        f"⚠️ Причина: {reason}\n"
        f"🔁 Рестартів всього: {restart_count}\n"
        f"🔄 Дія: {status}\n\n"
        f"<i>Перевір: journalctl -u {SERVICE} -n 30</i>"
    )


# ─────────────────────────────────────────────────────────────
# Restart через systemd
# ─────────────────────────────────────────────────────────────

def restart_service() -> bool:
    """Перезапускає сервіс через systemctl"""
    log(f"🔄 Перезапуск {SERVICE} через systemctl...")
    result = subprocess.run(
        ["sudo", "systemctl", "restart", SERVICE],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        time.sleep(5)
        if is_service_active():
            log(f"✅ {SERVICE} перезапущений успішно")
            return True
        log(f"⚠️  Після рестарту сервіс не active")
        return False
    log(f"❌ Помилка systemctl restart: {result.stderr.strip()}")
    return False


# ─────────────────────────────────────────────────────────────
# Головний health check
# ─────────────────────────────────────────────────────────────

def health_check():
    log("── Health check ──")

    service_ok = is_service_active()
    api_ok     = is_telegram_api_responding()

    log(f"  systemd active : {'✅' if service_ok else '❌'}")
    log(f"  Telegram API   : {'✅' if api_ok     else '❌'}")

    if service_ok and api_ok:
        log("✅ Бот здоровий")
        return

    # Визначаємо причину
    if not service_ok:
        reason = "systemd сервіс не активний (process crash)"
    elif not api_ok:
        reason = "Telegram API не відповідає (бот завис)"
    else:
        reason = "невідома причина"

    log(f"⚠️  Проблема: {reason}")

    # Спроба рестарту
    restarted     = restart_service()
    restart_count = get_restart_count()

    # Алерт тобі
    alert_text = format_alert(reason, restarted, restart_count)
    send_alert(alert_text)

    if not restarted:
        log("🚨 КРИТИЧНО: не вдалося перезапустити бота!")


# ─────────────────────────────────────────────────────────────
# Signal handling
# ─────────────────────────────────────────────────────────────

def signal_handler(signum, frame):
    log("👋 Monitor отримав сигнал завершення")
    sys.exit(0)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    log(f"🚀 InSilver Monitor v3 запущено (інтервал: {CHECK_INTERVAL}s)")

    if not load_config():
        log("❌ Не вдалося завантажити конфіг. Виходжу.")
        sys.exit(1)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT,  signal_handler)

    # Перша перевірка одразу при старті
    health_check()

    # Основний цикл
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            health_check()
        except KeyboardInterrupt:
            log("👋 Monitor зупинений користувачем")
            break
        except Exception as e:
            log(f"❌ Помилка в циклі монітора: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()