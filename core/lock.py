import os
import sys
import atexit
import time
import signal
import tempfile
import logging
from core.config import PID_FILE

log = logging.getLogger("lock")

def _is_bot_process(pid):
    """Перевіряє що процес справді наш бот."""
    try:
        with open(f"/proc/{pid}/cmdline", "r") as f:
            cmdline = f.read()
            return "main.py" in cmdline or "insilver" in cmdline.lower()
    except (OSError, IOError):
        return False

def acquire_lock():
    """Гарантує що тільки один процес бота запущений."""
    current_pid = os.getpid()
    
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid_str = f.read().strip()
            
            if old_pid_str and old_pid_str.isdigit():
                old_pid = int(old_pid_str)
                
                # Перевіряємо чи процес живий
                try:
                    os.kill(old_pid, 0)
                    # Процес живий - перевіряємо чи це наш бот
                    if _is_bot_process(old_pid):
                        print(f"❌ Бот вже запущений (PID {old_pid}). Використай: sudo systemctl restart insilver-v3")
                        sys.exit(1)
                    else:
                        log.warning(f"PID {old_pid} не є ботом, очищаємо lock")
                except (OSError, ProcessLookupError):
                    # Процес не існує
                    log.info(f"Stale PID file removed (PID {old_pid} не існує)")
                
                # Видаляємо stale lock
                os.remove(PID_FILE)
        
        except (ValueError, IOError) as e:
            log.warning(f"Пошкоджений PID file: {e}, очищаємо")
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
    
    # Атомічний запис PID файлу
    temp_file = PID_FILE + ".tmp"
    try:
        with open(temp_file, "w") as f:
            f.write(str(current_pid))
            f.flush()
            os.fsync(f.fileno())
        
        os.rename(temp_file, PID_FILE)
        log.info(f"✅ Lock отримано (PID {current_pid})")
        
        # Cleanup при завершенні
        atexit.register(release_lock)
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
        
    except (IOError, OSError) as e:
        print(f"❌ Не можу створити lock file: {e}")
        sys.exit(1)

def _signal_handler(signum, frame):
    """Коректне завершення при отриманні сигналу."""
    log.info(f"Отримано сигнал {signum}, завершуємо...")
    release_lock()
    sys.exit(0)

def release_lock():
    """Звільняє lock."""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                file_pid = f.read().strip()
            
            # Видаляємо тільки якщо це наш PID
            if file_pid == str(os.getpid()):
                os.remove(PID_FILE)
                log.info("🔓 Lock знято")
            else:
                log.warning(f"PID file містить інший PID: {file_pid} (наш: {os.getpid()})")
    except (OSError, IOError) as e:
        log.error(f"Помилка при звільненні lock: {e}")
