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

# Add these imports to your existing imports
import uuid

# Add this storage for rebattle requests (similar to active_battles)
rebattle_requests = {}

@router.callback_query(F.data.startswith("rebattle_"))
async def rebattle_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle rebattle request"""
    try:
        await callback.answer("This feature is coming soon...", show_alert=True)
        # # Parse callback data: rebattle_{current_user_id}_{opponent_id}_{battle_id}
        # parts = callback.data.split("_")
        # current_user_id = int(parts[1])
        # opponent_id = int(parts[2])
        # battle_id = int(parts[3])
        
        # # Verify the current user is the one making the request
        # if callback.from_user.id != current_user_id:
        #     await callback.answer("❌ Invalid request!")
        #     return
        
        # # Get previous battle data from database
        # battle_data = await db.get_battle_by_code(battle_id)
        # if not battle_data:
        #     await callback.answer("❌ Battle data not found!")
        #     return
        
        # # Generate unique request ID
        # request_id = str(uuid.uuid4())[:8]
        
        # # Store rebattle request
        # rebattle_requests[request_id] = {
        #     "requester_id": current_user_id,
        #     "opponent_id": opponent_id,
        #     "session_type": battle_data["session_type"],
        #     "original_battle_id": battle_id,
        #     "requester_message_id": callback.message.message_id
        # }
        
        # # Get requester name
        # requester_name = callback.from_user.first_name or "Unknown"
        
        # # Send rebattle request to opponent
        # request_message = f"🔄 **Rebattle Request!**\n\n" \
        #                  f"👤 **{requester_name}** wants to battle you again!\n" \
        #                  f"📊 Previous battle scope: {battle_data['session_type'].title()}\n\n" \
        #                  f"Do you accept the challenge?"
        
        # try:
        #     opponent_message = await bot.send_message(
        #         chat_id=opponent_id,
        #         text=request_message,
        #         reply_markup=acc_rebattle_btn(request_id)
        #     )
            
        #     # Store opponent message ID for later cleanup
        #     rebattle_requests[request_id]["opponent_message_id"] = opponent_message.message_id
            
        #     # Update requester's message
        #     await callback.message.edit_text(
        #         f"🔄 **Rebattle request sent!**\n\n" \
        #         f"⏳ Waiting for opponent's response...",
        #         reply_markup=dec_rebattle_btn(request_id)
        #     )
            
        #     await callback.answer("✅ Rebattle request sent!")
            
        # except Exception as e:
        #     logger.error(f"Error sending rebattle request to opponent: {e}")
        #     # Clean up the request
        #     if request_id in rebattle_requests:
        #         del rebattle_requests[request_id]
        #     await callback.answer("❌ Could not send request to opponent!")
            
    except Exception as e:
        logger.error(f"Error handling rebattle request: {e}")
        await callback.answer("❌ Error processing rebattle request!")

@router.callback_query(F.data.startswith("accept_rebattle_"))
async def accept_rebattle_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle rebattle acceptance"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in rebattle_requests:
            await callback.answer("❌ Request expired or not found!")
            return
        
        request_data = rebattle_requests[request_id]
        
        # Verify the current user is the opponent
        if callback.from_user.id != request_data["opponent_id"]:
            await callback.answer("❌ Invalid request!")
            return
        
        # Get session type and create new battle session
        session_type = request_data["session_type"]
        
        try:
            # Get a new random battle session based on session type
            if session_type == "book":
                # Get the original battle to find which book was used
                original_battle = await db.get_battle_by_code(request_data["original_battle_id"])
                original_session = await db.get_battle_session_by_id(original_battle["session_id"])
                
                # Get a new random session for the same book
                # You'll need to extract book_id from the original session or store it in battle_history
                # For now, I'll assume you can get it from the session
                battle_session = await db.get_random_battle_session_book(original_session["book_id"])
                book = await db.get_book_by_id(original_session["book_id"])
                scope_display = f"📚 All vocabularies from {book['title']}"
                
            else:  # topic
                # Get the original battle to find which topic was used
                original_battle = await db.get_battle_by_code(request_data["original_battle_id"])
                original_session = await db.get_battle_session_by_id(original_battle["session_id"])
                
                # Get a new random session for the same topic
                battle_session = await db.get_random_battle_session_topic(original_session["topic_id"])
                topic = await db.get_topic_by_id(original_session["topic_id"])
                scope_display = f"📝 Topic: {topic['title']}"
            
            if not battle_session:
                await callback.answer("❌ No battle session available!")
                # Clean up
                await cleanup_rebattle_request(request_id, bot)
                return
            
            # Create new battle record
            battle_id = await db.create_battle(
                session_id=battle_session["id"],
                session_type=session_type,
                player1_id=request_data["requester_id"],
                player2_id=request_data["opponent_id"]
            )
            
            # Prepare message data for battle start
            msg_user_data = {
                'player1': {
                    'user_id': request_data["requester_id"],
                    'msg_id': request_data["requester_message_id"]
                },
                'player2': {
                    'user_id': request_data["opponent_id"],
                    'msg_id': callback.message.message_id
                }
            }
            
            # Clean up rebattle request
            await cleanup_rebattle_request(request_id, bot, delete_messages=False)
            
            # Start the battle
            await start_battle_for_players(msg_user_data, battle_session, battle_id, scope_display, bot)
            
            await callback.answer("✅ Rebattle accepted! Starting battle...")
            
        except Exception as e:
            logger.error(f"Error creating rebattle session: {e}")
            await callback.answer("❌ Error starting rebattle!")
            await cleanup_rebattle_request(request_id, bot)
            
    except Exception as e:
        logger.error(f"Error accepting rebattle: {e}")
        await callback.answer("❌ Error accepting rebattle!")

@router.callback_query(F.data.startswith("decline_rebattle_"))
async def decline_rebattle_handler(callback: CallbackQuery, bot: Bot):
    """Handle rebattle decline"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in rebattle_requests:
            await callback.answer("❌ Request expired or not found!")
            return
        
        request_data = rebattle_requests[request_id]
        
        # Verify the current user is the opponent
        if callback.from_user.id != request_data["opponent_id"]:
            await callback.answer("❌ Invalid request!")
            return
        
        # Notify requester about decline
        try:
            await bot.edit_message_text(
                chat_id=request_data["requester_id"],
                message_id=request_data["requester_message_id"],
                text="❌ **Rebattle Declined**\n\nYour opponent declined the rebattle request.",
                reply_markup=get_back_to_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Error notifying requester about decline: {e}")
        
        # Update opponent's message
        await callback.message.edit_text(
            "❌ **Rebattle Declined**\n\nYou declined the rebattle request.",
            reply_markup=get_back_to_main_keyboard()
        )
        
        # Clean up request
        if request_id in rebattle_requests:
            del rebattle_requests[request_id]
        
        await callback.answer("✅ Rebattle declined!")
        
    except Exception as e:
        logger.error(f"Error declining rebattle: {e}")
        await callback.answer("❌ Error declining rebattle!")

@router.callback_query(F.data.startswith("cancel_rebattle_"))
async def cancel_rebattle_handler(callback: CallbackQuery, bot: Bot):
    """Handle rebattle cancellation by requester"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in rebattle_requests:
            await callback.answer("❌ Request expired or not found!")
            return
        
        request_data = rebattle_requests[request_id]
        
        # Verify the current user is the requester
        if callback.from_user.id != request_data["requester_id"]:
            await callback.answer("❌ Invalid request!")
            return
        
        # Update requester's message
        await callback.message.edit_text(
            "❌ **Rebattle Cancelled**\n\nYou cancelled the rebattle request.",
            reply_markup=get_back_to_main_keyboard()
        )
        
        # Clean up (this will also delete opponent's message)
        await cleanup_rebattle_request(request_id, bot)
        
        await callback.answer("✅ Rebattle request cancelled!")
        
    except Exception as e:
        logger.error(f"Error cancelling rebattle: {e}")
        await callback.answer("❌ Error cancelling rebattle!")

async def cleanup_rebattle_request(request_id: str, bot: Bot, delete_messages: bool = True):
    """Clean up rebattle request and optionally delete messages"""
    try:
        if request_id not in rebattle_requests:
            return
        
        request_data = rebattle_requests[request_id]
        
        if delete_messages:
            # Try to delete opponent's message
            try:
                await bot.delete_message(
                    chat_id=request_data["opponent_id"],
                    message_id=request_data["opponent_message_id"]
                )
            except Exception as e:
                logger.error(f"Error deleting opponent message: {e}")
        
        # Remove from storage
        del rebattle_requests[request_id]
        
    except Exception as e:
        logger.error(f"Error cleaning up rebattle request: {e}")

# Add cleanup for expired requests (optional - call this periodically)
async def cleanup_expired_rebattle_requests(bot: Bot, max_age_minutes: int = 10):
    """Clean up rebattle requests older than max_age_minutes"""
    try:
        current_time = time.time()
        expired_requests = []
        
        for request_id, request_data in rebattle_requests.items():
            # Assuming you add timestamp when creating request
            if hasattr(request_data, 'timestamp'):
                if current_time - request_data['timestamp'] > (max_age_minutes * 60):
                    expired_requests.append(request_id)
        
        for request_id in expired_requests:
            await cleanup_rebattle_request(request_id, bot)
            
    except Exception as e:
        logger.error(f"Error cleaning up expired requests: {e}")

def register_basic_handlers(dp, bot):
    """Register basic handlers"""
    dp.include_router(router)