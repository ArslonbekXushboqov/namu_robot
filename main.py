import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from handlers import setup_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection on startup"""
    try:
        db = DatabaseManager(settings.DATABASE_PATH)
        tester = DatabaseTester()
        
        logger.info("Testing database connection...")
        success = await tester.test_basic_queries(db)
        
        if success:
            logger.info("✅ Database connection successful!")
            return True
        else:
            logger.error("❌ Database test failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False
    
async def main():
    """Initialize and start the bot"""
    # Validate settings
    settings.validate()
    
    db_ok = test_database_connection()
    print(db_ok)
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