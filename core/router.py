"""Smart Router — класифікує намір повідомлення."""
import logging
import anthropic
from core.config import ANTHROPIC_KEY

log = logging.getLogger("core.router")

INTENTS = ("SEARCH", "QUESTION", "ORDER", "SOCIAL")

_SYSTEM = (
    "Ти класифікатор намірів для бота ювелірної майстерні. "
    "Відповідай ТІЛЬКИ одним словом: SEARCH, QUESTION, ORDER або SOCIAL.\n\n"
    "SEARCH — клієнт хоче побачити товари: 'покажіть ланцюжки', 'є браслети бісмарк?', "
    "'які є хрестики', 'каталог', 'фото рамзес'.\n"
    "QUESTION — клієнт задає питання: 'скільки коштує', 'як виміряти руку', "
    "'які терміни', 'яка різниця між карабіном і коробочкою', 'розмір пальця'.\n"
    "ORDER — клієнт хоче замовити: 'хочу замовити', 'оформити', 'купую', 'беру'.\n"
    "SOCIAL — привітання, прощання, подяка: 'привіт', 'дякую', 'добре', 'ок', "
    "'до побачення', 'зрозуміло'."
)

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_KEY, max_retries=1, timeout=10.0)
    return _client

def classify_intent(message: str) -> str:
    """Повертає SEARCH / QUESTION / ORDER / SOCIAL. Fallback: QUESTION."""
    if not message or not message.strip():
        return "SOCIAL"
    try:
        raw = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=5,
            system=_SYSTEM,
            messages=[{"role": "user", "content": message[:500]}]
        )
        text = raw.content[0].text.strip().upper() if raw.content else ""
        intent = text if text in INTENTS else "QUESTION"
        log.info(f"Router: '{message[:60]}' -> {intent}")
        return intent
    except Exception as e:
        log.error(f"Router помилка: {e}")
        return "QUESTION"
