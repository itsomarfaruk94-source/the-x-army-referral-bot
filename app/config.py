import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/xarmy.db")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")
REFERRAL_REWARD = int(os.getenv("REFERRAL_REWARD", "10"))
PACKAGES = {
    "1 Hour": int(os.getenv("PACKAGE_1H_POINTS", "30")),
    "2 Hours": int(os.getenv("PACKAGE_2H_POINTS", "50")),
    "3 Hours": int(os.getenv("PACKAGE_3H_POINTS", "70")),
}
