"""AI модуль — спілкування з Anthropic."""
import logging
import anthropic
from core.config import ANTHROPIC_KEY
from core.prompt import SYSTEM_PROMPT

log = logging.getLogger("core.ai")
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

async def ask_ai(user_id: int, message: str, history: list) -> str:
    """Відправляє повідомлення до Claude і повертає відповідь."""
    try:
        messages = history + [{"role": "user", "content": message}]

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        reply = response.content[0].text
        log.info(f"AI відповів для {user_id}: {reply[:80]}...")
        return reply

    except Exception as e:
        log.error(f"AI помилка для {user_id}: {e}")
        return "Вибачте, сталась технічна помилка. Спробуйте ще раз або напишіть нам напряму."
