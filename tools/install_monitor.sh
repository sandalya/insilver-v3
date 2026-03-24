#!/bin/bash
"""
🚀 Встановлення системи моніторингу InSilver v3

Що робить:
1. Копіює insilver-monitor.service в systemd
2. Перезавантажує systemd daemon
3. Запускає monitor сервіс  
4. Показує статус

USAGE:
  sudo bash tools/install_monitor.sh
"""

set -e

SERVICE_FILE="tools/insilver-monitor.service"
SYSTEMD_PATH="/etc/systemd/system/insilver-monitor.service"

echo "🚀 Встановлення InSilver Monitor v3..."

# Перевірка що запущено з sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запускай з sudo: sudo bash $0"
    exit 1
fi

# Перевірка що файл сервісу існує
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Файл $SERVICE_FILE не знайдено"
    exit 1
fi

echo "📄 Копіювання сервісу..."
cp "$SERVICE_FILE" "$SYSTEMD_PATH"
echo "✅ Скопійовано: $SYSTEMD_PATH"

echo "🔄 Перезавантаження systemd..."
systemctl daemon-reload

echo "🎯 Увімкнення автозапуску..."
systemctl enable insilver-monitor

echo "🚀 Запуск monitor сервісу..."
systemctl start insilver-monitor

echo "⏳ Очікування 3 секунди..."
sleep 3

echo "📊 Статус:"
systemctl status insilver-monitor --no-pager -l

echo ""
echo "✅ ВСТАНОВЛЕННЯ ЗАВЕРШЕНО!"
echo ""
echo "📋 КОРИСНІ КОМАНДИ:"
echo "  sudo systemctl status insilver-monitor    # статус"
echo "  sudo systemctl restart insilver-monitor   # перезапуск"
echo "  journalctl -u insilver-monitor -f         # логи"
echo "  python3 tools/bot_manager.py status       # статус бота"
echo "  python3 tools/bot_manager.py health       # health check"
echo ""
echo "🚨 НАЛАШТУВАННЯ АЛЕРТІВ:"
echo "  Додай в .env: ALERT_CHAT_ID=123456789 (chat_id Влада)"
echo "  Або в systemd: sudo systemctl edit insilver-monitor"
echo ""