from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
import asyncio
import time
import json
import random

from .callback_handlers import start_battle_for_players
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

# Add these imports if not already present
import uuid
from datetime import datetime, timedelta

# Dictionary to store pending rebattle requests
pending_rebattles = {}

@router.callback_query(F.data.startswith("rebattle_"))
async def rebattle_request_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle rebattle request"""
    try:
        # Parse callback data: rebattle_{current_user_id}_{opponent_id}_{battle_config}
        data_parts = callback.data.split("_", 3)  # Split into max 4 parts
        current_user_id = int(data_parts[1])
        opponent_id = int(data_parts[2])
        battle_config = data_parts[3]  # This could be "book_123" or "topic_456"
        
        # Verify the current user is actually the one making the request
        if callback.from_user.id != current_user_id:
            await callback.answer(Messages.INVALID_REQUEST)
            return
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]  # Short unique ID
        
        # Store rebattle request
        pending_rebattles[request_id] = {
            "requester_id": current_user_id,
            "opponent_id": opponent_id,
            "battle_config": battle_config,
            "timestamp": datetime.now(),
            "requester_message_id": callback.message.message_id,
            "requester_chat_id": callback.message.chat.id
        }
        
        # Parse battle config to get readable info
        config_parts = battle_config.split("_")
        config_type = config_parts[0]  # "book" or "topic"
        config_id = int(config_parts[1])
        
        # Get battle info for display
        if config_type == "book":
            book = await db.get_book_by_id(config_id)
            battle_info = Messages.BOOK_BATTLE_INFO.format(book_title=book['title']) if book else Messages.BOOK_BATTLE_DEFAULT
        else:  # topic
            topic = await db.get_topic_by_id(config_id)
            battle_info = Messages.TOPIC_BATTLE_INFO.format(topic_title=topic['title']) if topic else Messages.TOPIC_BATTLE_DEFAULT
        
        # Send rebattle request to opponent
        request_message = Messages.REBATTLE_REQUEST_MESSAGE.format(
            requester_name=callback.from_user.first_name,
            battle_info=battle_info
        )
        
        try:
            await bot.send_message(
                chat_id=opponent_id,
                text=request_message,
                reply_markup=acc_rebattle_btn(request_id),
                parse_mode="HTML"
            )
            
            # Update requester's message
            await callback.message.edit_text(
                Messages.REBATTLE_REQUEST_SENT.format(
                    opponent_name=await get_user_name(opponent_id, bot),
                    battle_info=battle_info
                ),
                reply_markup=dec_rebattle_btn(request_id),
                parse_mode="HTML"
            )
            
            await callback.answer(Messages.REBATTLE_REQUEST_SENT_SHORT)
            
        except Exception as e:
            if "chat not found" in str(e).lower() or "user is deactivated" in str(e).lower():
                await callback.answer(Messages.UNABLE_TO_SEND_REQUEST)
                # Clean up the pending request
                if request_id in pending_rebattles:
                    del pending_rebattles[request_id]
            else:
                logger.error(f"Error sending rebattle request: {e}")
                await callback.answer(Messages.ERROR_SENDING_REQUEST)
        
    except Exception as e:
        logger.error(f"Error in rebattle request: {e}")
        await callback.answer(Messages.ERROR_PROCESSING_REQUEST)

@router.callback_query(F.data.startswith("accept_rebattle_"))
async def accept_rebattle_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle rebattle acceptance"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in pending_rebattles:
            await callback.answer(Messages.REQUEST_EXPIRED_SHORT)
            await callback.message.edit_text(Messages.REQUEST_EXPIRED)
            return
        
        request_data = pending_rebattles[request_id]
        
        # Verify the current user is the opponent
        if callback.from_user.id != request_data["opponent_id"]:
            await callback.answer(Messages.INVALID_REQUEST)
            return
        
        requester_id = request_data["requester_id"]
        battle_config = request_data["battle_config"]
        
        # Parse battle config
        config_parts = battle_config.split("_")
        config_type = config_parts[0]  # "book" or "topic"
        config_id = int(config_parts[1])
        
        # Create battle session (reuse existing logic)
        try:
            if config_type == "book":
                battle_session = await db.get_random_battle_session_book(config_id)
                book = await db.get_book_by_id(config_id)
                scope_display = Messages.SCOPE_ALL_VOCABULARIES.format(book_title=book['title']) if book else Messages.BOOK_BATTLE_DEFAULT
            else:  # topic
                battle_session = await db.get_random_battle_session_topic(config_id)
                topic = await db.get_topic_by_id(config_id)
                scope_display = Messages.SCOPE_SPECIFIC_TOPIC.format(topic_title=topic['title']) if topic else Messages.TOPIC_BATTLE_DEFAULT
            
            if not battle_session:
                await callback.answer(Messages.BATTLE_SESSION_NOT_AVAILABLE)
                await callback.message.edit_text(Messages.BATTLE_NOT_AVAILABLE)
                # Clean up
                del pending_rebattles[request_id]
                return
            
            # Create battle in database
            battle_id = await db.create_battle(
                session_id=battle_session["id"],
                session_type=battle_config,
                player1_id=requester_id,
                player2_id=callback.from_user.id
            )
            
            # Update both messages to show acceptance
            await callback.message.delete()
            
            # Update requester's message
            try:
                await bot.delete_message(
                    chat_id=request_data["requester_chat_id"],
                    message_id=request_data["requester_message_id"]
                )
            except Exception as e:
                logger.error(f"Error updating requester message: {e}")
            
            # Start the battle using existing logic
            msg_user_data = {
                'player1': {
                    'user_id': requester_id,
                    'msg_id': request_data["requester_message_id"]
                },
                'player2': {
                    'user_id': callback.from_user.id,
                    'msg_id': callback.message.message_id
                },
                'battle_type': "re"
            }
            
            await start_battle_for_players(msg_user_data, battle_session, battle_id, battle_config, scope_display, bot)
            
            # Clean up pending request
            del pending_rebattles[request_id]
            
        except Exception as e:
            logger.error(f"Error creating rebattle: {e}")
            # Clean up
            if request_id in pending_rebattles:
                del pending_rebattles[request_id]
        
    except Exception as e:
        logger.error(f"Error accepting rebattle: {e}")
        await callback.answer(Messages.ERROR_PROCESSING_ACCEPTANCE)

@router.callback_query(F.data.startswith("decline_rebattle_"))
async def decline_rebattle_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle rebattle decline"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in pending_rebattles:
            await callback.answer(Messages.REQUEST_EXPIRED_SHORT)
            await callback.message.edit_text(Messages.REQUEST_EXPIRED)
            return
        
        request_data = pending_rebattles[request_id]
        
        # Verify the current user is the opponent
        if callback.from_user.id != request_data["opponent_id"]:
            await callback.answer(Messages.INVALID_REQUEST)
            return
        
        requester_id = request_data["requester_id"]
        
        # Update opponent's message
        await callback.message.edit_text(
            Messages.REBATTLE_DECLINED_OPPONENT.format(
                requester_name=await get_user_name(requester_id, bot)
            ),
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        
        # Notify requester
        try:
            await bot.edit_message_text(
                chat_id=request_data["requester_chat_id"],
                message_id=request_data["requester_message_id"],
                text=Messages.REBATTLE_DECLINED_REQUESTER.format(
                    opponent_name=callback.from_user.first_name
                ),
                reply_markup=get_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error notifying requester: {e}")
        
        # Clean up
        del pending_rebattles[request_id]
        await callback.answer(Messages.REBATTLE_DECLINED_SHORT)
        
    except Exception as e:
        logger.error(f"Error declining rebattle: {e}")
        await callback.answer(Messages.ERROR_PROCESSING_DECLINE)

@router.callback_query(F.data.startswith("cancel_rebattle_"))
async def cancel_rebattle_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle rebattle cancellation by requester"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        if request_id not in pending_rebattles:
            await callback.answer(Messages.REQUEST_EXPIRED_SHORT)
            await callback.message.edit_text(
                Messages.REQUEST_EXPIRED,
                reply_markup=get_back_to_main_keyboard()
            )
            return
        
        request_data = pending_rebattles[request_id]
        
        # Verify the current user is the requester
        if callback.from_user.id != request_data["requester_id"]:
            await callback.answer(Messages.INVALID_REQUEST)
            return
        
        # Update requester's message
        await callback.message.edit_text(
            Messages.REBATTLE_REQUEST_CANCELLED,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        
        # Try to notify opponent that request was cancelled
        try:
            opponent_id = request_data["opponent_id"]
            await bot.send_message(
                chat_id=opponent_id,
                text=Messages.REBATTLE_REQUEST_CANCELLED_NOTIFICATION.format(
                    requester_name=callback.from_user.first_name
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error notifying opponent about cancellation: {e}")
        
        # Clean up
        del pending_rebattles[request_id]
        await callback.answer(Messages.REQUEST_CANCELLED_SHORT)
        
    except Exception as e:
        logger.error(f"Error cancelling rebattle: {e}")
        await callback.answer(Messages.ERROR_CANCELLING_REQUEST)

# Helper function to get user name
async def get_user_name(user_id: int, bot: Bot) -> str:
    """Get user's first name from Telegram"""
    try:
        chat = await bot.get_chat(user_id)
        return chat.first_name or Messages.DEFAULT_USER_NAME
    except Exception:
        return Messages.DEFAULT_USER_NAME

# Clean up expired rebattle requests (call this periodically)
async def cleanup_expired_rebattles():
    """Remove expired rebattle requests (older than 5 minutes)"""
    current_time = datetime.now()
    expired_requests = []
    
    for request_id, request_data in pending_rebattles.items():
        if current_time - request_data["timestamp"] > timedelta(minutes=5):
            expired_requests.append(request_id)
    
    for request_id in expired_requests:
        del pending_rebattles[request_id]
    
    logger.info(f"Cleaned up {len(expired_requests)} expired rebattle requests")

def register_basic_handlers(dp, bot):
    """Register basic handlers"""
    dp.include_router(router)