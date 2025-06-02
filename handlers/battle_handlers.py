
from aiogram import Router
from aiogram.fsm.context import FSMContext

# Placeholder router for battle logic handlers
router = Router()

# Battle handlers will be implemented in Part 3
# This includes:
# - Battle creation logic
# - Question handling
# - Answer processing
# - Battle completion

def register_battle_handlers(dp, bot):
    """Register battle handlers"""
    dp.include_router(router)