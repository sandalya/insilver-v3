import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge", "knowledge.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders", "orders.json")
PHOTOS_INDEX = os.path.join(DATA_DIR, "photos", "index.json")
PHOTOS_CATALOG = os.path.join(DATA_DIR, "photos", "catalog.json")
SILVER_FILE = os.path.join(DATA_DIR, "silver.json")

# Single process lock
PID_FILE = os.path.join(BASE_DIR, "bot.pid")
SITE_CATALOG = os.path.join(DATA_DIR, "site_catalog.json")
