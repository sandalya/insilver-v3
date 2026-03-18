"""
scripts/scrape_site.py — скрейп сайту insilver.pp.ua
"""
import json
import time
import re
import urllib.request
import urllib.parse
from datetime import datetime

BASE_URL = "https://www.insilver.pp.ua"
OUTPUT = "/home/sashok/.openclaw/workspace/insilver-v3/data/site_catalog.json"

CATEGORY_URLS = [
    ("/плетіння/ланцюжки/рамзес",         "Ланцюжки", "Рамзес"),
    ("/плетіння/ланцюжки/водоспад",        "Ланцюжки", "Водоспад"),
    ("/плетіння/ланцюжки/бісмарк",         "Ланцюжки", "Бісмарк"),
    ("/плетіння/ланцюжки/кардинал",        "Ланцюжки", "Кардинал"),
    ("/плетіння/ланцюжки/імператор",       "Ланцюжки", "Імператор"),
    ("/плетіння/ланцюжки/тризуб",          "Ланцюжки", "Тризуб"),
    ("/плетіння/ланцюжки/козацький",       "Ланцюжки", "Козацький"),
    ("/плетіння/ланцюжки/якірний",         "Ланцюжки", "Якірний"),
    ("/плетіння/ланцюжки/фараон",          "Ланцюжки", "Фараон"),
    ("/плетіння/ланцюжки/пітон",           "Ланцюжки", "Пітон"),
    ("/плетіння/ланцюжки/лисячий-хвіст",  "Ланцюжки", "Лисячий Хвіст"),
    ("/плетіння/ланцюжки/візантія",        "Ланцюжки", "Візантія"),
    ("/плетіння/ланцюжки/панцирне",        "Ланцюжки", "Панцирне"),
    ("/плетіння/ланцюжки/фігаро",          "Ланцюжки", "Фігаро"),
    ("/плетіння/ланцюжки/біт",             "Ланцюжки", "Біт"),
    ("/плетіння/браслети/рамзес-брасет",      "Браслети", "Рамзес"),
    ("/плетіння/браслети/водоспад-брасет",    "Браслети", "Водоспад"),
    ("/плетіння/браслети/бісмарк-брасет",     "Браслети", "Бісмарк"),
    ("/плетіння/браслети/кардинал-брасет",    "Браслети", "Кардинал"),
    ("/плетіння/браслети/імператор-брасет",   "Браслети", "Імператор"),
    ("/плетіння/браслети/тризуб-брасет",      "Браслети", "Тризуб"),
    ("/плетіння/браслети/козацький-брасет",   "Браслети", "Козацький"),
    ("/плетіння/браслети/якірний-брасет",     "Браслети", "Якірний"),
    ("/плетіння/браслети/фараон-брасет",      "Браслети", "Фараон"),
    ("/плетіння/браслети/пітон-брасет",       "Браслети", "Пітон"),
    ("/плетіння/браслети/лисячий-хвіст-браслет", "Браслети", "Лисячий Хвіст"),
    ("/плетіння/браслети/візантія-браслет",   "Браслети", "Візантія"),
    ("/плетіння/браслети/панцирне-брасет",    "Браслети", "Панцирне"),
    ("/плетіння/браслети/тракторний-брасет",  "Браслети", "Тракторний"),
    ("/кулони/хрестики",   "Кулони", "Хрестики"),
    ("/кулони/кулони",     "Кулони", "Кулони"),
    ("/кулони/ладанки",    "Кулони", "Ладанки"),
    ("/набори/ланцюжок-браслет",   "Набори", "Ланцюжок + Браслет"),
    ("/набори/ланцюжок-хрестик",   "Набори", "Ланцюжок + Хрестик"),
    ("/набори/ланцюжок-ладанка",   "Набори", "Ланцюжок + Ладанка"),
    ("/печатки-та-персні", "Печатки та Персні", "Печатки та Персні"),
    ("/ексклюзив",         "Ексклюзив", "Ексклюзив"),
    ("/фурнітура-та-застібки", "Фурнітура", "Фурнітура та Застібки"),
]

def fetch(url):
    url = urllib.parse.quote(url, safe=":/?=#&.@")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8")

def extract_product_links(html, base_path):
    pattern = rf'href="({re.escape(base_path)}/[^"]+)"'
    links = re.findall(pattern, html)
    seen = set()
    result = []
    for l in links:
        if l not in seen and "#" not in l and l != base_path:
            seen.add(l)
            result.append(l)
    return result

def extract_photos(html):
    pattern = r'https://lh3\.googleusercontent\.com/sitesv/[^")\s]+'
    photos = re.findall(pattern, html)
    seen = set()
    result = []
    for p in photos:
        clean = p.split("=w")[0]
        if clean not in seen and "w16383" not in p:
            seen.add(clean)
            result.append(p)
    return result

def clean_text(text):
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_order_text(html):
    m = re.search(r'ЗАМОВИТИ:\s*([^<"\n]{5,120})', html, re.IGNORECASE)
    if m:
        raw = m.group(1).strip().rstrip('"').rstrip("'")
        return clean_text(raw)
    return None

def extract_title(html, fallback=""):
    m = re.search(r'<title>([^<]+)</title>', html)
    if m:
        title = m.group(1).strip()
        title = re.sub(r'InSilver[^-]*-\s*', '', title).strip()
        return title or fallback
    return fallback

def parse_product_params(text):
    params = {}
    weight = re.search(r'[Мм]ас[аи]?\s*[~≈]?\s*(\d+)', text)
    if weight:
        params["weight"] = weight.group(1) + "г"
    if "чорніння" in text.lower() or "чернение" in text.lower():
        params["finish"] = "чорніння"
    if "коробочка" in text.lower():
        params["clasp"] = "замок-коробочка"
    return params

def scrape_product_page(url, category, subcategory):
    try:
        html = fetch(url)
        product_photos = extract_photos(html)
        title = extract_title(html, url.split("/")[-1])
        product_text = extract_order_text(html) or title
        params = parse_product_params(product_text + " " + url)
        return {
            "url": url,
            "category": category,
            "subcategory": subcategory,
            "title": product_text or title,
            "text": product_text or title,
            "params": params,
            "photos": product_photos[:5],
            "photo": product_photos[0] if product_photos else None,
        }
    except Exception as e:
        print(f"  ⚠ Помилка {url}: {e}")
        return None

def main():
    print("🔍 Починаємо скрейп insilver.pp.ua...")
    catalog = []
    errors = 0

    for path, category, subcategory in CATEGORY_URLS:
        url = BASE_URL + path
        print(f"\n📂 {category} / {subcategory}")
        try:
            html = fetch(url)
            time.sleep(0.5)
            product_links = extract_product_links(html, path)
            if product_links:
                print(f"   Знайдено {len(product_links)} товарів")
                for link in product_links:
                    item = scrape_product_page(BASE_URL + link, category, subcategory)
                    if item:
                        catalog.append(item)
                        print(f"   ✓ {item['title'][:60]} — {len(item['photos'])} фото")
                    time.sleep(0.3)
            else:
                product_photos = extract_photos(html)
                if product_photos:
                    title = extract_order_text(html) or extract_title(html, subcategory)
                    catalog.append({
                        "url": url, "category": category, "subcategory": subcategory,
                        "title": title, "text": title, "params": {},
                        "photos": product_photos[:5], "photo": product_photos[0],
                    })
                    print(f"   ✓ {title[:60]} — {len(product_photos)} фото")
                else:
                    print(f"   — товарів не знайдено")
        except Exception as e:
            print(f"   ✗ Помилка: {e}")
            errors += 1
        time.sleep(0.5)

    result = {
        "scraped_at": datetime.now().isoformat(),
        "total": len(catalog),
        "source": "insilver.pp.ua",
        "items": catalog
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово! Зібрано {len(catalog)} товарів, помилок: {errors}")
    print(f"📁 Збережено: {OUTPUT}")

if __name__ == "__main__":
    main()
