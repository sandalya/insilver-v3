import os
import sys
import atexit
from core.config import PID_FILE

def acquire_lock():
    """Гарантує що тільки один процес бота запущений."""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            old_pid = f.read().strip()
        if old_pid:
            try:
                os.kill(int(old_pid), 0)
                print(f"❌ Бот вже запущений (PID {old_pid}). Зупиніть його спочатку.")
                sys.exit(1)
            except (OSError, ValueError):
                # Процес не існує — старий PID файл, видаляємо
                os.remove(PID_FILE)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(release_lock)
    print(f"✅ Lock отримано (PID {os.getpid()})")

def release_lock():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        print("🔓 Lock знято")
