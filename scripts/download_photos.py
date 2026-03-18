"""
scripts/download_photos.py — завантажує фото перехоплюючи запити браузера
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

CATALOG = "/home/sashok/.openclaw/workspace/insilver-v3/data/site_catalog.json"
PHOTOS_DIR = Path("/home/sashok/.openclaw/workspace/insilver-v3/data/photos/site")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    data = json.load(open(CATALOG, encoding="utf-8"))
    items = data["items"]
    
    # Збираємо унікальні URL сторінок товарів
    pages_to_visit = {}
    for item in items:
        url = item.get("url")
        if url:
            pages_to_visit[url] = item

    print(f"📥 Завантажуємо фото з {len(pages_to_visit)} сторінок...")
    print(f"📁 Папка: {PHOTOS_DIR}\n")

    downloaded = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
        )
        page = context.new_page()

        for i, (page_url, item) in enumerate(pages_to_visit.items()):
            # Словник для перехоплених фото цієї сторінки
            intercepted = {}

            def handle_response(response, _url=page_url):
                if "lh3.googleusercontent.com/sitesv" in response.url:
                    ct = response.headers.get("content-type", "")
                    if "image" in ct:
                        try:
                            intercepted[response.url] = response.body()
                        except:
                            pass

            page.on("response", handle_response)

            try:
                page.goto(page_url, timeout=30000)
                time.sleep(1.5)
            except Exception as e:
                print(f"  ✗ {page_url}: {e}")
                failed += 1
                page.remove_listener("response", handle_response)
                continue

            page.remove_listener("response", handle_response)

            # Зберігаємо перехоплені фото
            local_photos = []
            for j, (img_url, img_bytes) in enumerate(intercepted.items()):
                clean = img_url.split("/sitesv/")[-1].split("=")[0][:40]
                clean = "".join(c for c in clean if c.isalnum() or c in "-_")
                fname = f"{clean}_{j}.jpg"
                fpath = PHOTOS_DIR / fname
                fpath.write_bytes(img_bytes)
                local_photos.append(str(fpath))
                downloaded += 1

            item["local_photos"] = local_photos
            item["local_photo"] = local_photos[0] if local_photos else None

            if (i + 1) % 25 == 0 or (i + 1) == len(pages_to_visit):
                print(f"  [{i+1}/{len(pages_to_visit)}] ✓{downloaded} фото — {item['title'][:40]}")

        browser.close()

    json.dump(data, open(CATALOG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n✅ Готово! Завантажено: {downloaded} фото, помилок: {failed}")

if __name__ == "__main__":
    main()
