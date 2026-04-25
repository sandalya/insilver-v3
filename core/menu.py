"""Меню команд для скрепки в Telegram.

Один джерело істини для двох наборів — клієнтського і адмінського.
Використовується в main.py (старт) і bot/admin.py (toggle при /admin).
"""
from telegram import BotCommand

CLIENT_COMMANDS = [
    BotCommand("start", "Почати або перезапустити бота"),
    BotCommand("order", "Оформити замовлення"),
    BotCommand("contact", "Контакти майстра"),
    BotCommand("help", "Інструкція з користування"),
    BotCommand("cancel", "Скасувати поточну дію"),
]

ADMIN_COMMANDS = CLIENT_COMMANDS + [
    BotCommand("admin", "Вийти з адмінки"),  # підказка коли вже в адмінці
    BotCommand("orders", "Список замовлень"),
    BotCommand("price", "Ціни на срібло"),
    BotCommand("done", "Зберегти запис у трейнері"),
    BotCommand("admin_help", "Повна інструкція адміна"),
]
