#!/usr/bin/env python3
"""Розробницький функціонал відновлення даних."""

import json
import asyncio
import sys
import os
from pathlib import Path

# Додати поточну директорію в PATH
sys.path.append(os.getcwd())

from core.backup_system import list_backup_files, restore_from_backup, convert_backup_to_training_record
from core.log_analyzer import auto_recover_lost_data, get_unconfirmed_records
from bot.admin import load_training_data, save_training_data

async def full_recovery():
    """Повне відновлення всіх даних."""
    print("🚀 Починаю повне відновлення даних...")
    
    results = {
        "backups_found": 0,
        "backups_restored": 0,
        "logs_recovered": 0,
        "total_restored": 0,
        "errors": []
    }
    
    try:
        # 1. Бекапи
        print("\n📦 Сканування бекапів...")
        backups = list_backup_files()
        results["backups_found"] = len(backups)
        
        if backups:
            print(f"Знайдено {len(backups)} бекапів:")
            for backup in backups[-5:]:  # Останні 5
                timestamp = backup["timestamp"][:16] if backup["timestamp"] else "?"
                backup_type = "📦 збірка" if backup["type"] == "trainer_collection" else "📝 запис"  
                size_info = f"({backup['size']})" if backup["size"] > 1 else ""
                print(f"  - {backup_type} {timestamp} {size_info}")
        else:
            print("Бекапів не знайдено")
        
        # 2. Логи
        print("\n🔍 Сканування логів...")
        try:
            from core.ai import ask_ai
            recovered_records = await auto_recover_lost_data(189793675, ask_ai)
            results["logs_recovered"] = len(recovered_records)
            
            if recovered_records:
                print(f"Відновлено з логів: {len(recovered_records)} записів")
                
                # Додаємо до бази
                training_data = load_training_data()
                training_data.extend(recovered_records)
                
                if save_training_data(training_data):
                    results["total_restored"] = len(recovered_records)
                    print("✅ Записи з логів збережено в базу")
                else:
                    results["errors"].append("Помилка збереження записів з логів")
            else:
                print("Втрачених записів у логах не знайдено")
                
        except Exception as e:
            error_msg = f"Помилка сканування логів: {e}"
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
        
        # 3. Показуємо поточний стан
        print("\n📊 Поточний стан бази:")
        training_data = load_training_data()
        confirmed = [r for r in training_data if r.get("id", 0) > 0]
        unconfirmed = [r for r in training_data if r.get("status") == "unconfirmed"]
        
        print(f"  Підтверджені записи: {len(confirmed)}")
        print(f"  Непідтверджені записи: {len(unconfirmed)}")
        
        # 4. Підсумок
        print(f"\n🎯 Результат відновлення:")
        print(f"  📦 Бекапів знайдено: {results['backups_found']}")
        print(f"  🔍 З логів відновлено: {results['logs_recovered']}")
        print(f"  💾 Всього записів додано: {results['total_restored']}")
        
        if results["errors"]:
            print(f"\n⚠️ Помилки:")
            for error in results["errors"]:
                print(f"  - {error}")
        
        if results["total_restored"] > 0:
            print(f"\n📝 Непідтверджені записи потребують схвалення в /admin")
        
        return results
        
    except Exception as e:
        print(f"❌ Критична помилка відновлення: {e}")
        return None

async def show_recovery_status():
    """Показати статус відновлення без змін."""
    print("📊 Статус системи відновлення:")
    
    # Бекапи  
    backups = list_backup_files()
    print(f"\n📦 Бекапи: {len(backups)} файлів")
    if backups:
        for backup in backups[-3:]:  # Останні 3
            timestamp = backup["timestamp"][:16]
            backup_type = "збірка" if backup["type"] == "trainer_collection" else "запис"
            print(f"  - {backup_type} {timestamp}")
    
    # База даних
    training_data = load_training_data()
    confirmed = [r for r in training_data if r.get("id", 0) > 0] 
    unconfirmed = [r for r in training_data if r.get("status") == "unconfirmed"]
    
    print(f"\n📚 База знань:")
    print(f"  Підтверджені: {len(confirmed)}")
    print(f"  Непідтверджені: {len(unconfirmed)}")
    
    # Логи
    log_file = Path("logs/conversations.log")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"\n📄 Логи розмов: {size:,} байт")
    else:
        print(f"\n📄 Логи розмов: не знайдено")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Розробницький функціонал відновлення")
    parser.add_argument("--status", action="store_true", help="Показати статус без змін")
    parser.add_argument("--recover", action="store_true", help="Повне відновлення")
    
    args = parser.parse_args()
    
    if args.status:
        asyncio.run(show_recovery_status())
    elif args.recover:
        asyncio.run(full_recovery())
    else:
        print("Використання:")
        print("  python3 dev_recovery.py --status   # Показати статус")
        print("  python3 dev_recovery.py --recover  # Повне відновлення")