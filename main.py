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

async def test_database_connection():
    """Test database connection on startup"""
    try:
        db = VocabularyBattleDB("vocabulary.db")

        # Check connection status
        connection_ok = await db.check_database_connection()

        # Initialize database (your existing method with better logging)
        init_ok = await db.init_database()

        # Test basic operations
        test_ok = await db.test_simple_operation()    
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False
    
async def main():
    """Initialize and start the bot"""
    # Validate settings
    settings.validate()
    await test_database_connection()
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Setup handlers
    setup_handlers(dp)
    
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