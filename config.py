import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "telegram_file_store")
    
    @staticmethod
    def validate():
        if not Config.API_ID or Config.API_ID == 0:
            raise ValueError("API_ID is not set in environment variables")
        if not Config.API_HASH:
            raise ValueError("API_HASH is not set in environment variables")
        if not Config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in environment variables")
        if not Config.OWNER_ID or Config.OWNER_ID == 0:
            raise ValueError("OWNER_ID is not set in environment variables")
        if not Config.MONGODB_URI:
            raise ValueError("MONGODB_URI is not set in environment variables")
        if not Config.LOG_CHANNEL or Config.LOG_CHANNEL == 0:
            raise ValueError("LOG_CHANNEL is not set in environment variables")
