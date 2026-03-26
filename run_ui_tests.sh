#!/bin/bash
# UI Workflow Tester - Wrapper Script
# Автоматично використовує правильний venv Python

cd "$(dirname "$0")"

if [ ! -f "venv/bin/python3" ]; then
    echo "❌ ERROR: venv/bin/python3 не знайдено"
    echo "Запустіть: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

echo "🎭 Запуск UI Workflow Tester з venv..."
exec ./venv/bin/python3 tests/ui_workflow_tester.py "$@"