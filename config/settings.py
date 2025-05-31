import os
from typing import Optional

class Settings:
    # Bot configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8113426976:AAFa6DJI1sjWE_S8HVrWERy14BCTMmLGZlg")
    
    # Database configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "vocabulary.db")
    
    # Battle configuration
    BATTLE_TIMEOUT_MINUTES: int = 10
    QUESTIONS_PER_BATTLE: int = 10
    BATTLE_LINK_EXPIRY_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        if cls.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("BOT_TOKEN must be set in environment variables")
        return True

settings = Settings()
