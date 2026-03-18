"""core/photo.py — завантаження фото для відправки в Telegram."""
import urllib.request
import logging
import io
log = logging.getLogger("core.photo")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.insilver.pp.ua/",
}

def fetch_photo_bytes(url: str) -> bytes | None:
    """Завантажує фото по URL і повертає bytes."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read()
    except Exception as e:
        log.warning(f"Не вдалось завантажити фото {url[:60]}: {e}")
        return None

def fetch_photo_file(url: str) -> io.BytesIO | None:
    """Повертає BytesIO об'єкт для відправки в Telegram."""
    data = fetch_photo_bytes(url)
    if data:
        buf = io.BytesIO(data)
        buf.name = "photo.jpg"
        return buf
    return None
