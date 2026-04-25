"""Утиліта для відправки великих .md документів у Telegram секціями.

Розбиває .md по заголовках "## " і шле кожну секцію окремим повідомленням
з parse_mode=MarkdownV2. Спецсимволи ескейпляться згідно з Telegram MarkdownV2 spec.
"""
import asyncio
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

MAX_MSG_SIZE = 4000
ESCAPE_CHARS = r'_*[]()~`>#+-=|{}.!\\'


def split_by_h2(content: str) -> list:
    """Розбити markdown на секції за заголовками '## '."""
    lines = content.split('\n')
    sections = []
    current = []
    for line in lines:
        if line.startswith('## '):
            if current:
                sections.append('\n'.join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append('\n'.join(current).strip())
    return [s for s in sections if s]


def _escape(text: str) -> str:
    """Ескейпити ВСІ MarkdownV2 спецсимволи."""
    return re.sub(rf'([{re.escape(ESCAPE_CHARS)}])', r'\\\1', text)


def md_to_telegram_v2(text: str) -> str:
    """Конвертувати markdown секцію у MarkdownV2.

    Стратегія: витягуємо в плейсхолдери все що має форматування або
    залишається як є (code, links, bold), ескейпимо весь решта текст,
    повертаємо плейсхолдери з правильно ескейпнутим вмістом.
    """
    placeholders = []

    def stash(replacement):
        idx = len(placeholders)
        placeholders.append(replacement)
        return f'KZPLHK{idx:04d}KZPLHK'

    # 1. Code blocks ```...``` — вміст не ескейпиться, ` всередині треба замінити
    def code_block(m):
        body = m.group(1)
        body = body.replace('\\', '\\\\').replace('`', '\\`')
        return stash(f'```\n{body.strip()}\n```')
    text = re.sub(r'```(?:\w+)?\n([\s\S]*?)```', code_block, text)

    # 2. Inline code `...` — те саме
    def inline_code(m):
        body = m.group(1).replace('\\', '\\\\').replace('`', '\\`')
        return stash(f'`{body}`')
    text = re.sub(r'`([^`\n]+)`', inline_code, text)

    # 3. Links [text](url) — text ескейпиться, url теж
    def link(m):
        link_text = _escape(m.group(1))
        url = m.group(2).replace('\\', '\\\\').replace(')', '\\)')
        return stash(f'[{link_text}]({url})')
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)

    # 4. Заголовки ### і ## → bold (зберігаємо як плейсхолдер з ескейпнутим вмістом)
    def header(m):
        body = _escape(m.group(1))
        return stash(f'*{body}*')
    text = re.sub(r'^#{1,6}\s+(.+)$', header, text, flags=re.MULTILINE)

    # 5. **bold** → bold (з ескейпом всередині)
    def bold(m):
        body = _escape(m.group(1))
        return stash(f'*{body}*')
    text = re.sub(r'\*\*([^*\n]+?)\*\*', bold, text)

    # 6. *italic* (одинарні зірки) — рідко, але буває в .md
    # Пропускаємо — у наших гайдах одинарні * не використовуються

    # 7. Ескейпити ВЕСЬ решта текст
    text = _escape(text)

    # 8. Повернути плейсхолдери. Деякі плейсхолдери (header, bold) містять
    # вкладені маркери інших плейсхолдерів (code, link). Тому робимо в циклі
    # поки всі не повернуться.
    import re as _re
    for _ in range(10):  # max 10 ітерацій вистачить на будь-який реальний документ
        if not _re.search(r'KZPLHK\d+KZPLHK', text):
            break
        for i, replacement in enumerate(placeholders):
            marker = f'KZPLHK{i:04d}KZPLHK'
            text = text.replace(marker, replacement)

    return text


async def send_doc_in_sections(bot, chat_id: int, md_path: Path, delay: float = 0.4):
    """Прочитати .md, розбити по '## ', надіслати в Telegram секціями."""
    if not md_path.exists():
        await bot.send_message(chat_id, f"❌ Файл не знайдено: {md_path.name}")
        return 0

    content = md_path.read_text(encoding='utf-8')
    sections = split_by_h2(content)
    if not sections:
        await bot.send_message(chat_id, "❌ Файл порожній")
        return 0

    sent = 0
    for i, section in enumerate(sections):
        if len(section) > MAX_MSG_SIZE:
            log.warning(f"Section {i} too long ({len(section)}), truncating")
            section = section[:MAX_MSG_SIZE - 50] + "\n\n…(скорочено)"

        try:
            tg_text = md_to_telegram_v2(section)
            await bot.send_message(chat_id, tg_text, parse_mode="MarkdownV2", disable_web_page_preview=True)
            sent += 1
        except Exception as e:
            log.error(f"Failed section {i} of {md_path.name}: {e}")
            try:
                await bot.send_message(chat_id, section, disable_web_page_preview=True)
                sent += 1
            except Exception as e2:
                log.error(f"Plain fallback also failed: {e2}")

        if i < len(sections) - 1:
            await asyncio.sleep(delay)

    return sent
