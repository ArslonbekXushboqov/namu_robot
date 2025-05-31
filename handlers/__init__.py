from aiogram import Dispatcher
from . import basic_handlers, battle_handlers, callback_handlers

def setup_handlers(dp: Dispatcher):
    """Setup all handlers"""
    # Register handlers in order of priority
    callback_handlers.register_callback_handlers(dp)
    battle_handlers.register_battle_handlers(dp)  
    basic_handlers.register_basic_handlers(dp)