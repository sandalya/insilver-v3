"""
core/catalog.py — пошук товарів по site_catalog.json (insilver.pp.ua)
"""
import json
import html
import re
import logging
import os
import time
import gc
from typing import Optional
from pathlib import Path

log = logging.getLogger("core.catalog")

# Memory management
_catalog_cache: Optional[list] = None
_cache_time: Optional[float] = None
_cache_file_mtime: Optional[float] = None
CACHE_REFRESH_INTERVAL = 3600  # 1 hour

def load_catalog() -> list:
    """Load catalog with smart caching and memory management."""
    global _catalog_cache, _cache_time, _cache_file_mtime
    
    from core.config import SITE_CATALOG
    current_time = time.time()
    
    try:
        # Check if file exists and get modification time
        if not os.path.exists(SITE_CATALOG):
            log.warning(f"Каталог файл не знайдено: {SITE_CATALOG}")
            return []
            
        file_mtime = os.path.getmtime(SITE_CATALOG)
        
        # Check if cache is valid
        cache_valid = (
            _catalog_cache is not None and
            _cache_time is not None and
            _cache_file_mtime == file_mtime and
            (current_time - _cache_time) < CACHE_REFRESH_INTERVAL
        )
        
        if cache_valid:
            return _catalog_cache
        
        # Load catalog from file
        log.info("Перезавантаження каталогу...")
        with open(SITE_CATALOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Clear old cache and update
        if _catalog_cache is not None:
            _catalog_cache.clear()
            gc.collect()  # Force garbage collection
            
        _catalog_cache = data.get("items", [])
        _cache_time = current_time
        _cache_file_mtime = file_mtime
        
        log.info(f"Каталог сайту завантажено: {len(_catalog_cache)} товарів")
        return _catalog_cache
        
    except Exception as e:
        log.error(f"Помилка завантаження каталогу: {e}")
        # Return cached version if available, even if stale
        if _catalog_cache is not None:
            log.warning("Використовуємо застарілу версію кешу")
            return _catalog_cache
        return []

def clear_catalog_cache():
    """Manually clear catalog cache to free memory."""
    global _catalog_cache, _cache_time, _cache_file_mtime
    if _catalog_cache:
        _catalog_cache.clear()
        _catalog_cache = None
        _cache_time = None
        _cache_file_mtime = None
        gc.collect()
        log.info("Кеш каталогу очищено")

SYNONYMS = {
    "ланцюг":     ["ланцюжок", "цепочка", "chain"],
    "ланцюжок":   ["ланцюг", "цепочка", "ланцюжки", "ланцюгів"],
    "кільце":     ["кольцо", "перстень", "перстінь"],
    "перстень":   ["кільце", "кольцо", "перстінь"],
    "сережки":    ["серьги", "сережка"],
    "браслет":    ["браслети", "браслетів"],
    "хрест":      ["хрестик", "крест", "крестик"],
    "хрестик":    ["хрест", "крестик"],
    "підвіска":   ["кулон", "підвісочка"],
    "кулон":      ["підвіска", "підвісочка"],
    "ладанка":    ["ладанки", "ладанок"],
    "печатка":    ["перстень", "персні", "печатки"],
    "срібло":     ["срібний", "срібна", "срібне", "925"],
    "чорніння":   ["чернение", "чорнений"],
    "рамзес":     ["ramzes"],
    "кардинал":   ["kardinal"],
    "бісмарк":    ["bismark"],
    "водоспад":   ["vodopad"],
    "візантія":   ["vizantia"],
}

def _expand_keywords(query: str) -> list:
    words = re.findall(r'\w+', query.lower())
    expanded = set(words)
    for word in words:
        for base, syns in SYNONYMS.items():
            if word == base or word in syns:
                expanded.add(base)
                expanded.update(syns)
    return list(expanded)

def _score_item(item: dict, keywords: list) -> int:
    title    = (item.get("title") or "").lower()
    category = (item.get("category") or "").lower()
    subcat   = (item.get("subcategory") or "").lower()
    # decode HTML entities перед пошуком
    title    = html.unescape(title)
    category = html.unescape(category)
    subcat   = html.unescape(subcat)
    search_text = f"{title} {category} {subcat}"
    score = 0
    for kw in keywords:
        if kw in search_text:
            score += search_text.count(kw) * 2
            if kw in subcat:
                score += 4
            if kw in category:
                score += 2
    return score

def keyword_search(query: str, top_n: int = 3) -> list:
    catalog  = load_catalog()
    keywords = _expand_keywords(query)
    scored = []
    for item in catalog:
        s = _score_item(item, keywords)
        if s > 0:
            scored.append((s, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [i for _, i in scored[:top_n]]

def format_item_text(item: dict) -> str:
    title    = html.unescape(item.get("title", ""))
    category = item.get("category", "")
    subcat   = item.get("subcategory", "")
    params   = item.get("params", {})

    lines = [f"*{title}*"]
    lines.append(f"Категорія: {category} / {subcat}")
    if params.get("finish"):
        lines.append(f"Оздоблення: {params['finish']}")
    if params.get("clasp"):
        lines.append(f"Замок: {params['clasp']}")
    return "\n".join(lines)

def search_catalog(query: str, top_n: int = 3):
    items = keyword_search(query, top_n)
    return items, bool(items)
