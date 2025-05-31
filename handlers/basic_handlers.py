from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.inline import get_main_menu_keyboard
from strings.messages import Messages
from utils.states import clear_user_session

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    clear_user_session(message.from_user.id)
    
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
    """Handle /stats command - placeholder for now"""
    await message.answer(
        "📊 Your statistics will be available soon!",
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
        "🤔 I don't understand that command.\n\n" + Messages.MAIN_MENU,
        reply_markup=get_main_menu_keyboard()
    )

def register_basic_handlers(dp):
    """Register basic handlers"""
    dp.include_router(router)