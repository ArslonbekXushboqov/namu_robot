from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
import asyncio
import time
import json
import random

from keyboards.inline import (
    get_main_menu_keyboard, get_battle_type_keyboard, 
    get_book_selection_keyboard, get_scope_selection_keyboard,
    get_topic_selection_keyboard, get_back_to_main_keyboard,
    get_battle_question_keyboard, get_share_battle_keyboard,
    get_battle_results_keyboard, dec_rebattle_btn,
    acc_rebattle_btn
)
from strings.messages import Messages
from utils.states import BattleStates, get_user_session, clear_user_session
from database.queries import VocabularyBattleDB
from config.settings import settings

logger = logging.getLogger(__name__)
router = Router()

# Initialize database manager
db = VocabularyBattleDB(settings.DATABASE_PATH)

# Global storage for re-battle requests
pending_rebattle_requests = {}

# Re-battle callback handlers for aiogram 3
@router.callback_query(F.data.startswith('rebattle_request_'))
async def handle_rebattle_request(callback: CallbackQuery):
    """Handle re-battle request initiation"""
    try:
        # Parse: rebattle_request_requester_opponent_scope
        data_parts = callback.data.split("_", 3)
        if len(data_parts) < 4:
            await callback.answer("❌ Invalid request format")
            return
        
        requester_id = int(data_parts[2])
        opponent_id = int(data_parts[3])
        scope_display = data_parts[4] if len(data_parts) > 4 else "Unknown"
        
        # Validate requester
        if callback.from_user.id != requester_id:
            await callback.answer("❌ Unauthorized request")
            return
        
        # Generate unique request ID
        request_id = f"{requester_id}_{opponent_id}_{int(time.time())}"
        
        # Store the request
        pending_rebattle_requests[request_id] = {
            "requester_id": requester_id,
            "opponent_id": opponent_id,
            "scope_display": scope_display,
            "requester_name": callback.from_user.first_name,
            "timestamp": time.time()
        }
        
        # Update requester's message
        await callback.message.edit_text(
            text="🔄 Re-battle request sent to your opponent!\nWaiting for response...",
            reply_markup=get_rebattle_cancel_keyboard(request_id)
        )
        
        # Send request to opponent
        await send_rebattle_request_to_opponent(request_id)
        await callback.answer("✅ Re-battle request sent!")
        
    except Exception as e:
        logger.error(f"Error in rebattle request: {e}")
        await callback.answer("❌ Error processing request")

@router.callback_query(F.data.startswith('rebattle_accept_'))
async def handle_rebattle_accept(callback: CallbackQuery):
    """Handle re-battle acceptance"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in pending_rebattle_requests:
            await callback.answer("❌ Request expired or invalid")
            return
        
        request_data = pending_rebattle_requests[request_id]
        requester_id = request_data["requester_id"]
        opponent_id = request_data["opponent_id"]
        scope_display = request_data["scope_display"]
        
        # Validate opponent
        if callback.from_user.id != opponent_id:
            await callback.answer("❌ Unauthorized action")
            return
        
        # Clean up the request
        del pending_rebattle_requests[request_id]
        
        # Create new battle session
        new_battle_session = await create_new_battle_session(scope_display)
        
        if not new_battle_session:
            await callback.message.edit_text(
                text="❌ Unable to create new battle session. Please try again later.",
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer("❌ Failed to create battle session")
            return
        
        # Generate new battle ID
        new_battle_id = generate_battle_id()
        
        # Update opponent's message
        await callback.message.edit_text(
            text="✅ Re-battle accepted! Preparing new battle...",
            reply_markup=None
        )
        
        # Notify requester and start battle
        await notify_rebattle_accepted(requester_id, opponent_id, new_battle_session, new_battle_id, scope_display)
        await callback.answer("✅ Re-battle accepted!")
        
    except Exception as e:
        logger.error(f"Error accepting rebattle: {e}")
        await callback.answer("❌ Error processing acceptance")

@router.callback_query(F.data.startswith('rebattle_decline_'))
async def handle_rebattle_decline(callback: CallbackQuery):
    """Handle re-battle decline"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in pending_rebattle_requests:
            await callback.answer("❌ Request expired or invalid")
            return
        
        request_data = pending_rebattle_requests[request_id]
        requester_id = request_data["requester_id"]
        opponent_id = request_data["opponent_id"]
        
        # Validate opponent
        if callback.from_user.id != opponent_id:
            await callback.answer("❌ Unauthorized action")
            return
        
        # Clean up the request
        del pending_rebattle_requests[request_id]
        
        # Update opponent's message
        await callback.message.edit_text(
            text="❌ Re-battle request declined.",
            reply_markup=get_back_to_main_keyboard()
        )
        
        # Notify requester about decline
        await notify_rebattle_declined(requester_id)
        await callback.answer("✅ Request declined")
        
    except Exception as e:
        logger.error(f"Error declining rebattle: {e}")
        await callback.answer("❌ Error processing decline")

@router.callback_query(F.data.startswith('rebattle_cancel_'))
async def handle_rebattle_cancel(callback: CallbackQuery):
    """Handle re-battle request cancellation"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in pending_rebattle_requests:
            await callback.answer("❌ Request not found")
            return
        
        request_data = pending_rebattle_requests[request_id]
        requester_id = request_data["requester_id"]
        
        # Validate requester
        if callback.from_user.id != requester_id:
            await callback.answer("❌ Unauthorized action")
            return
        
        # Clean up the request
        del pending_rebattle_requests[request_id]
        
        # Update requester's message
        await callback.message.edit_text(
            text="❌ Re-battle request cancelled.",
            reply_markup=get_back_to_main_keyboard()
        )
        
        await callback.answer("✅ Request cancelled")
        
    except Exception as e:
        logger.error(f"Error cancelling rebattle: {e}")
        await callback.answer("❌ Error processing cancellation")

# Helper functions
async def send_rebattle_request_to_opponent(request_id: str):
    """Send re-battle request notification to opponent"""
    try:
        request_data = pending_rebattle_requests[request_id]
        opponent_id = request_data["opponent_id"]
        requester_name = request_data["requester_name"]
        scope_display = request_data["scope_display"]
        
        request_message = (
            f"🔄 <b>Re-battle Request!</b>\n\n"
            f"{requester_name} wants to battle you again!\n\n"
            f"📚 Topic: {scope_display}\n\n"
            f"Do you accept this challenge?"
        )
        
        await bot.send_message(
            chat_id=opponent_id,
            text=request_message,
            reply_markup=get_rebattle_response_keyboard(request_id)
        )
        
    except Exception as e:
        logger.error(f"Error sending rebattle request: {e}")

async def notify_rebattle_accepted(requester_id: int, opponent_id: int, battle_session: dict, battle_id: int, scope_display: str):
    """Notify requester that re-battle was accepted and start battle"""
    try:
        # Send acceptance notification to requester
        await bot.send_message(
            chat_id=requester_id,
            text="✅ Your re-battle request was accepted! Starting new battle..."
        )
        
        # Send battle start message to both players
        battle_start_msg = f"🥊 <b>New Battle Starting!</b>\n\n📚 Topic: {scope_display}\n\nGet ready!"
        
        await bot.send_message(chat_id=requester_id, text=battle_start_msg)
        await bot.send_message(chat_id=opponent_id, text=battle_start_msg)
        
        # TODO: Implement actual battle start logic here
        # You might need to modify start_battle_for_players to work with user IDs
        # Or create mock callback objects from user IDs
        
    except Exception as e:
        logger.error(f"Error notifying rebattle acceptance: {e}")

async def notify_rebattle_declined(user_id: int):
    """Notify user that their re-battle request was declined"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Your re-battle request was declined by your opponent.",
            reply_markup=get_back_to_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error notifying rebattle decline: {e}")

async def create_new_battle_session(scope_display: str):
    """Create a new battle session with different words from the same scope"""
    try:
        # Get different word IDs from the same scope/book
        new_word_ids = await db.get_random_words_for_scope(scope_display, limit=15)
        
        if len(new_word_ids) < 10:
            logger.warning(f"Not enough words for rebattle in scope: {scope_display}")
            return None
        
        return {
            "word_ids": new_word_ids,
            "scope_display": scope_display
        }
        
    except Exception as e:
        logger.error(f"Error creating new battle session: {e}")
        return None

def generate_battle_id():
    """Generate unique battle ID"""
    return int(time.time() * 1000)

# Cleanup function (call this periodically)
async def cleanup_expired_rebattle_requests():
    """Remove expired re-battle requests (older than 5 minutes)"""
    current_time = time.time()
    expired_requests = [
        request_id for request_id, request_data in pending_rebattle_requests.items()
        if current_time - request_data["timestamp"] > 300  # 5 minutes
    ]
    
    for request_id in expired_requests:
        logger.info(f"Cleaning up expired rebattle request: {request_id}")
        del pending_rebattle_requests[request_id]
    
    return len(expired_requests)


def register_basic_handlers(dp):
    """Register basic handlers"""
    dp.include_router(router)