# ==================== 2. UPDATED handlers/basic_handlers.py ====================
"""
Enhanced basic handlers with database integration
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandObject

from keyboards.inline import get_main_menu_keyboard
from strings.messages import Messages
from utils.states import clear_user_session
from database.queries import VocabularyBattleDB
from config.settings import settings

router = Router()
db = VocabularyBattleDB(settings.DATABASE_PATH)

@router.message(CommandStart(deep_link=True))
async def start_handler(message: Message, command: CommandObject, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    clear_user_session(message.from_user.id)
    
    # Handle battle link sharing (friend battles)
    if len(command.args) > 0 and command.args.startswith("battle_"):
        # TODO: Handle friend battle joining in future enhancement
        await message.answer("🔗 Battle link feature coming soon!")
        return
    
    await message.answer(
        Messages.WELCOME,
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command"""
    await message.answer(Messages.HELP_MESSAGE)

@router.message(Command("stats"))
async def stats_handler(message: Message):
    """Handle /stats command"""
    try:
        stats = await db.get_user_battle_stats(message.from_user.id)
        
        if stats["total_battles"] == 0:
            stats_message = "📊 **Your Statistics**\n\nNo battles completed yet.\nStart your first battle to see stats!"
        else:
            stats_message = f"""📊 **Your Statistics**

🎯 **Battles:** {stats['total_battles']}
🏆 **Wins:** {stats['wins']}
❌ **Losses:** {stats['losses']}
📈 **Win Rate:** {stats['win_rate']:.1f}%
⭐ **Average Score:** {stats['avg_score']}/10
"""
        
        await message.answer(
            stats_message,
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await message.answer(
            "❌ Error fetching statistics.",
            reply_markup=get_main_menu_keyboard()
        )

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Handle /cancel command"""
    await state.clear()
    clear_user_session(message.from_user.id)
    
    await message.answer(
        "❌ Operation cancelled.\n\n" + Messages.MAIN_MENU,
        reply_markup=get_main_menu_keyboard()
    )

@router.message(F.text)
async def unknown_message_handler(message: Message):
    """Handle unknown text messages"""
    await message.answer(
        Messages.MAIN_MENU,
        reply_markup=get_main_menu_keyboard()
    )

def register_basic_handlers(dp, bot):
    """Register basic handlers"""
    dp.include_router(router)