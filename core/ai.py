"""AI модуль — спілкування з Anthropic."""
import logging
import anthropic
import time
from core.config import ANTHROPIC_KEY
from core.prompt import SYSTEM_PROMPT

log = logging.getLogger("core.ai")

# Initialize client with retry configuration
client = anthropic.Anthropic(
    api_key=ANTHROPIC_KEY,
    max_retries=2,
    timeout=30.0
)

# Memory management for history
MAX_HISTORY_LENGTH = 20  # Maximum conversation turns
MAX_MESSAGE_LENGTH = 2000  # Maximum message length
MAX_TOTAL_TOKENS = 8000  # Approximate token limit

def optimize_history(history: list) -> list:
    """Optimize conversation history for memory and token efficiency."""
    if not history:
        return []
    
    # Limit history length
    history = history[-MAX_HISTORY_LENGTH:]
    
    # Truncate long messages
    optimized = []
    total_length = 0
    
    for msg in reversed(history):
        content = msg.get("content", "")
        if len(content) > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH] + "..."
        
        # Rough token estimation (1 token ≈ 4 characters)
        msg_tokens = len(content) // 4
        
        if total_length + msg_tokens > MAX_TOTAL_TOKENS:
            break
            
        optimized.insert(0, {"role": msg["role"], "content": content})
        total_length += msg_tokens
    
    return optimized

async def ask_ai(user_id: int, message: str, history: list) -> str:
    """Відправляє повідомлення до Claude і повертає відповідь."""
    start_time = time.time()
    
    try:
        # Optimize history for better performance
        optimized_history = optimize_history(history)
        
        # Truncate current message if too long
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH] + "..."
            log.warning(f"Повідомлення для {user_id} обрізано до {MAX_MESSAGE_LENGTH} символів")
        
        messages = optimized_history + [{"role": "user", "content": message}]
        
        log.info(f"AI запит для {user_id}: {len(messages)} повідомлень, {len(optimized_history)} з історії")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        reply = response.content[0].text
        duration = time.time() - start_time
        
        log.info(f"AI відповів для {user_id} за {duration:.2f}с: {reply[:80]}...")
        return reply

    except anthropic.APIError as e:
        log.error(f"Anthropic API помилка для {user_id}: {e}")
        return "Вибачте, сервіс тимчасово недоступний. Спробуйте за хвилину."
    except anthropic.RateLimitError as e:
        log.error(f"Rate limit для {user_id}: {e}")
        return "Забагато запитів, спробуйте за хвилину."
    except Exception as e:
        log.error(f"AI помилка для {user_id}: {e}")
        return "Вибачте, сталась технічна помилка. Спробуйте ще раз або напишіть нам напряму."
