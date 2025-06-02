import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from handlers import setup_handlers

from database.queries import VocabularyBattleDB
# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
    
async def main():
    """Initialize and start the bot"""
    # Validate settings
    settings.validate()

    # Initialize database FIRST
    db = VocabularyBattleDB("vocabulary.db")
    
    # Try to initialize database
    db_success = await db.init_database()
    
    if not db_success:
        logger.error("❌ Database initialization failed! Exiting...")
        return
    
    logger.info("✅ Database initialized successfully!")

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    dp["bot"] = bot
    
    # Setup handlers
    setup_handlers(dp, bot)
    
    logger.info("Starting Vocabulary Battle Bot...")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())