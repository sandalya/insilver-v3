"""
core/catalog.py — пошук товарів по site_catalog.json (insilver.pp.ua)
"""
import json
import html
import re
import logging
from typing import Optional
log = logging.getLogger("core.catalog")

_catalog_cache: Optional[list] = None

def load_catalog() -> list:
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    from core.config import SITE_CATALOG
    try:
        with open(SITE_CATALOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        _catalog_cache = data.get("items", [])
        log.info(f"Каталог сайту завантажено: {len(_catalog_cache)} товарів")
        return _catalog_cache
    except Exception as e:
        log.error(f"Помилка завантаження каталогу: {e}")
        return []

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
