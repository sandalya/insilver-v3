"""AI модуль — спілкування з Anthropic."""
import logging
import anthropic
import time
from core.config import ANTHROPIC_KEY
from core.prompt import ENHANCED_SYSTEM_PROMPT

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

def analyze_message_context(message: str, history: list) -> dict:
    """Аналіз контексту повідомлення для context-aware відповідей."""
    context = {
        "type": "general",
        "category": "загальне", 
        "priority": "medium",
        "previous_context": ""
    }
    
    message_lower = message.lower()
    
    # Аналіз типу запиту
    if any(word in message_lower for word in ["ціна", "скільки", "вартість", "коштує", "розрахунок", "грн"]):
        context["type"] = "pricing"
        context["category"] = "ціни"
        context["priority"] = "high"
    
    elif any(word in message_lower for word in ["замовлення", "замовити", "купити", "оформити", "підтвердити"]):
        context["type"] = "order"
        context["category"] = "замовлення"
        context["priority"] = "high"
    
    elif any(word in message_lower for word in ["доставка", "відправ", "новою поштою", "адреса"]):
        context["type"] = "logistics"
        context["category"] = "доставка"
        context["priority"] = "medium"
    
    elif any(word in message_lower for word in ["лом", "срібло", "здати", "прийом", "обмін"]):
        context["type"] = "scrap"
        context["category"] = "лом"
        context["priority"] = "high"
    
    elif any(word in message_lower for word in ["розмір", "виміряти", "довжина", "см", "обхват"]):
        context["type"] = "measurements" 
        context["category"] = "виміри"
        context["priority"] = "medium"
    
    elif any(word in message_lower for word in ["плетіння", "тризуб", "бісмарк", "якір", "рамзес"]):
        context["type"] = "technical"
        context["category"] = "технічні"
        context["priority"] = "medium"
    
    elif any(word in message_lower for word in ["каталог", "фото", "показати", "подивитись"]):
        context["type"] = "catalog"
        context["category"] = "каталог"
        context["priority"] = "medium"
    
    # Аналіз попереднього контексту
    if history:
        last_messages = " ".join([msg.get("content", "") for msg in history[-3:]])
        if "ціна" in last_messages.lower():
            context["previous_context"] = "pricing_discussion"
        elif "замовлення" in last_messages.lower():
            context["previous_context"] = "order_process"
        elif any(word in last_messages.lower() for word in ["плетіння", "тризуб", "бісмарк", "якір", "рамзес", "снейк", "кардинал"]):
            context["previous_context"] = "weaving_discussion"
    
    return context

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
        # 🧠 Context-aware analysis
        context = analyze_message_context(message, history)
        
        # Optimize history for better performance
        optimized_history = optimize_history(history)
        
        # Truncate current message if too long
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH] + "..."
            log.warning(f"Повідомлення для {user_id} обрізано до {MAX_MESSAGE_LENGTH} символів")
        
        # 🎯 Context-aware prompt enhancement
        enhanced_message = message
        context_hints = []
        
        # Додати поточний контекст
        if context["type"] != "general":
            context_hints.append(f"Запит категорії '{context['category']}', тип '{context['type']}', пріоритет {context['priority']}")
        
        # Додати попередній контекст
        if context["previous_context"]:
            if context["previous_context"] == "weaving_discussion":
                context_hints.append("ПОПЕРЕДНІЙ КОНТЕКСТ: розмова про плетіння ланцюжків/браслетів")
            elif context["previous_context"] == "pricing_discussion":  
                context_hints.append("ПОПЕРЕДНІЙ КОНТЕКСТ: обговорення цін")
            elif context["previous_context"] == "order_process":
                context_hints.append("ПОПЕРЕДНІЙ КОНТЕКСТ: процес оформлення замовлення")
        
        # Додати context hints до повідомлення
        if context_hints:
            enhanced_message = message + f"\n\n[КОНТЕКСТ: {'; '.join(context_hints)}]"
        
        messages = optimized_history + [{"role": "user", "content": enhanced_message}]
        
        log.info(f"AI запит для {user_id} ({context['category']}): {len(messages)} повідомлень, {len(optimized_history)} з історії")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=ENHANCED_SYSTEM_PROMPT,
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
