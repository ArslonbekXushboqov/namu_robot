from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Tuple

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with Battle button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Battle", callback_data="start_battle")],
        [InlineKeyboardButton(text="📊 My Stats", callback_data="my_stats")],
        [InlineKeyboardButton(text="📚 Books", callback_data="view_books")]
    ])
    return keyboard

def get_battle_type_keyboard() -> InlineKeyboardMarkup:
    """Choose battle type: random or friend"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Random Opponent", callback_data="battle_random")],
        [InlineKeyboardButton(text="👥 Battle with Friend", callback_data="battle_friend")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])
    return keyboard

def get_book_selection_keyboard(books: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
    """Select book for battle"""
    buttons = []
    for book_id, title in books:
        buttons.append([InlineKeyboardButton(
            text=f"📖 {title}", 
            callback_data=f"select_book_{book_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_battle_type")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_scope_selection_keyboard() -> InlineKeyboardMarkup:
    """Choose battle scope: all book or specific topic"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 All Vocabularies", callback_data="scope_book")],
        [InlineKeyboardButton(text="📝 Specific Topic", callback_data="scope_topic")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_book_selection")]
    ])
    return keyboard

def get_topic_selection_keyboard(topics: List[Tuple[int, str, int]]) -> InlineKeyboardMarkup:
    """Select topic for battle"""
    buttons = []
    for topic_id, title, word_count in topics:
        buttons.append([InlineKeyboardButton(
            text=f"📝 {title} ({word_count} words)", 
            callback_data=f"select_topic_{topic_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_scope_selection")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_battle_question_keyboard(options: List[str]) -> InlineKeyboardMarkup:
    """Question options for battle"""
    buttons = []
    for i, option in enumerate(options):
        buttons.append([InlineKeyboardButton(
            text=f"{chr(65+i)}. {option}", 
            callback_data=f"answer_{i}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_share_battle_keyboard(battle_link: str) -> InlineKeyboardMarkup:
    """Share battle link with friend"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Share Battle Link", url=battle_link)],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="back_to_main")]
    ])
    return keyboard

def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Simple back to main button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="back_to_main")]
    ])
    return keyboard