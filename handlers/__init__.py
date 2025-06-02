from aiogram import Dispatcher
from . import basic_handlers, battle_handlers, callback_handlers, rebate_handlers

def setup_handlers(dp: Dispatcher, bot):
    """Setup all handlers"""
    # Register handlers in order of priority
    callback_handlers.register_callback_handlers(dp, bot)
    battle_handlers.register_battle_handlers(dp, bot)  
    basic_handlers.register_basic_handlers(dp, bot)
    rebate_handlers.register_basic_handlers(dp, bot)

