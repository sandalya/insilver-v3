"""Калькулятор вартості виробу."""
import json
from pathlib import Path

PRICING_FILE = Path(__file__).parent.parent / "data" / "pricing.json"


def load_pricing() -> dict:
    if PRICING_FILE.exists():
        with open(PRICING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"weaving_prices": {}, "locks": [], "extras": {}, "default_price_per_gram": 155, "currency": "грн"}


def save_pricing(data: dict):
    with open(PRICING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_price_per_gram(weaving: str = "") -> float:
    """Повертає ціну за грам для конкретного плетіння."""
    pricing = load_pricing()
    weaving_lower = weaving.lower().strip()
    for price_str, weavings in pricing.get("weaving_prices", {}).items():
        for w in weavings:
            if w.lower() == weaving_lower:
                return float(price_str)
    return float(pricing.get("default_price_per_gram", 155))


def get_locks() -> list:
    return load_pricing().get("locks", [])


def calculate_price(weight: float, lock_name: str = "", weaving: str = "") -> dict:
    pricing = load_pricing()
    ppg = get_price_per_gram(weaving)
    silver_cost = ppg * weight
    lock_cost = 0
    for lock in pricing.get("locks", []):
        if lock["name"].lower() == lock_name.lower():
            lock_cost = lock.get("price", 0)
            break
    total = silver_cost + lock_cost
    return {
        "silver_cost": silver_cost,
        "lock_cost": lock_cost,
        "lock_name": lock_name,
        "total": total,
        "price_per_gram": ppg,
        "weight": weight,
        "currency": pricing.get("currency", "грн")
    }


def format_price(calc: dict) -> str:
    c = calc["currency"]
    lines = [f"⚖️ Срібло: {calc['price_per_gram']:.0f} {c} × {calc['weight']:.0f} г = {calc['silver_cost']:.0f} {c}"]
    if calc["lock_cost"] > 0:
        lines.append(f"🔒 Замок ({calc['lock_name']}): {calc['lock_cost']:.0f} {c}")
    elif calc["lock_name"]:
        lines.append(f"🔒 Замок ({calc['lock_name']}): входить у вартість")
    lines.append(f"💰 Разом: {calc['total']:.0f} {c}")
    return "\n".join(lines)


def get_weaving_price_hint() -> str:
    """Текст з цінами по плетінням для промпту."""
    pricing = load_pricing()
    lines = []
    for price_str, weavings in pricing.get("weaving_prices", {}).items():
        lines.append(f"{price_str} грн/г: {', '.join(weavings)}")
    return "\n".join(lines)
