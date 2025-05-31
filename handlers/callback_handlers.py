from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from keyboards.inline import (
    get_main_menu_keyboard, get_battle_type_keyboard, 
    get_book_selection_keyboard, get_scope_selection_keyboard,
    get_topic_selection_keyboard, get_back_to_main_keyboard
)
from strings.messages import Messages
from utils.states import BattleStates, get_user_session, clear_user_session

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Handle back to main menu"""
    await state.clear()
    clear_user_session(callback.from_user.id)
    
    await callback.message.edit_text(
        Messages.MAIN_MENU,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "start_battle")
async def start_battle_handler(callback: CallbackQuery, state: FSMContext):
    """Handle battle start"""
    await state.set_state(BattleStates.waiting_for_battle_type)
    
    await callback.message.edit_text(
        Messages.CHOOSE_BATTLE_TYPE,
        reply_markup=get_battle_type_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.in_(["battle_random", "battle_friend"]))
async def battle_type_handler(callback: CallbackQuery, state: FSMContext):
    """Handle battle type selection"""
    battle_type = "random" if callback.data == "battle_random" else "friend"
    
    # Store user choice
    session = get_user_session(callback.from_user.id)
    session.battle_type = battle_type
    
    await state.set_state(BattleStates.waiting_for_book_selection)
    
    # TODO: Fetch books from database (Part 3)
    # For now, show placeholder
    await callback.message.edit_text(
        f"✅ Battle type selected: {battle_type.title()}\n\n{Messages.CHOOSE_BOOK}",
        reply_markup=get_back_to_main_keyboard()
    )
    await callback.answer("📚 Book selection will be available in Part 3!")

@router.callback_query(F.data == "back_to_battle_type")
async def back_to_battle_type_handler(callback: CallbackQuery, state: FSMContext):
    """Handle back to battle type selection"""
    await state.set_state(BattleStates.waiting_for_battle_type)
    
    await callback.message.edit_text(
        Messages.CHOOSE_BATTLE_TYPE,
        reply_markup=get_battle_type_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "my_stats")
async def my_stats_handler(callback: CallbackQuery):
    """Handle stats viewing - placeholder"""
    await callback.message.edit_text(
        "📊 Statistics feature will be available in Part 3!",
        reply_markup=get_back_to_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "view_books")
async def view_books_handler(callback: CallbackQuery):
    """Handle books viewing - placeholder"""
    await callback.message.edit_text(
        "📚 Books viewing will be available in Part 3!",
        reply_markup=get_back_to_main_keyboard()
    )
    await callback.answer()

def register_callback_handlers(dp):
    """Register callback handlers"""
    dp.include_router(router)