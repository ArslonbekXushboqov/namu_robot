# 1. UPDATED handlers/callback_handlers.py
"""
Enhanced callback handlers with full database integration
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
import asyncio
import time
import json

from keyboards.inline import (
    get_main_menu_keyboard, get_battle_type_keyboard, 
    get_book_selection_keyboard, get_scope_selection_keyboard,
    get_topic_selection_keyboard, get_back_to_main_keyboard,
    get_battle_question_keyboard, get_share_battle_keyboard
)
from strings.messages import Messages
from utils.states import BattleStates, get_user_session, clear_user_session
from database.queries import DatabaseManager
from config.settings import settings

logger = logging.getLogger(__name__)
router = Router()

# Initialize database manager
db = DatabaseManager(settings.DATABASE_PATH)

# Storage for active battles
active_battles = {}
waiting_battles = {}

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
    
    try:
        # Fetch books from database
        books = await db.get_all_books()
        if not books:
            await callback.message.edit_text(
                Messages.NO_BOOKS_AVAILABLE,
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()
            return
        
        book_options = [(book["id"], book["title"]) for book in books]
        
        await callback.message.edit_text(
            f"✅ Battle type: {battle_type.title()}\n\n{Messages.CHOOSE_BOOK}",
            reply_markup=get_book_selection_keyboard(book_options)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        await callback.message.edit_text(
            Messages.DATABASE_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

@router.callback_query(F.data.startswith("select_book_"))
async def book_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Handle book selection"""
    book_id = int(callback.data.split("_")[-1])
    
    session = get_user_session(callback.from_user.id)
    session.selected_book_id = book_id
    
    await state.set_state(BattleStates.waiting_for_scope_selection)
    
    try:
        book = await db.get_book_by_id(book_id)
        if not book:
            await callback.message.edit_text(
                Messages.DATABASE_ERROR,
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            f"✅ Selected book: {book['title']}\n\n{Messages.CHOOSE_SCOPE}",
            reply_markup=get_scope_selection_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error fetching book: {e}")
        await callback.message.edit_text(
            Messages.DATABASE_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

@router.callback_query(F.data.in_(["scope_book", "scope_topic"]))
async def scope_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Handle scope selection"""
    scope = callback.data.split("_")[1]
    
    session = get_user_session(callback.from_user.id)
    session.battle_scope = scope
    
    if scope == "book":
        # Battle with entire book - start battle creation
        await create_battle_session(callback, state, session)
    else:
        # Battle with specific topic - show topic selection
        await state.set_state(BattleStates.waiting_for_topic_selection)
        
        try:
            topics = await db.get_topics_by_book(session.selected_book_id)
            if not topics:
                await callback.message.edit_text(
                    Messages.NO_TOPICS_AVAILABLE,
                    reply_markup=get_back_to_main_keyboard()
                )
                await callback.answer()
                return
            
            topic_options = [(topic["id"], topic["title"], topic["word_count"]) for topic in topics]
            
            await callback.message.edit_text(
                f"✅ Scope: Specific Topic\n\n{Messages.CHOOSE_TOPIC}",
                reply_markup=get_topic_selection_keyboard(topic_options)
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error fetching topics: {e}")
            await callback.message.edit_text(
                Messages.DATABASE_ERROR,
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()

@router.callback_query(F.data.startswith("select_topic_"))
async def topic_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Handle topic selection"""
    topic_id = int(callback.data.split("_")[-1])
    
    session = get_user_session(callback.from_user.id)
    session.selected_topic_id = topic_id
    
    # Now create battle session
    await create_battle_session(callback, state, session)

async def create_battle_session(callback: CallbackQuery, state: FSMContext, session):
    """Create battle session based on user choices"""
    try:
        # Get battle session from database
        if session.battle_scope == "book":
            battle_session = await db.get_random_book_battle_session(session.selected_book_id)
            book = await db.get_book_by_id(session.selected_book_id)
            scope_display = f"📚 All vocabularies from {book['title']}"
        else:
            battle_session = await db.get_random_topic_battle_session(session.selected_topic_id)
            topic = await db.get_topic_by_id(session.selected_topic_id)
            scope_display = f"📝 Topic: {topic['title']}"
        
        if not battle_session:
            await callback.message.edit_text(
                Messages.BATTLE_SESSION_ERROR,
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()
            return
        
        # Create battle configuration key for matching
        battle_config = f"{battle_session['type']}_{battle_session.get('book_id', battle_session.get('topic_id'))}"
        
        if session.battle_type == "random":
            # Try to find waiting opponent with same configuration
            if battle_config in waiting_battles:
                # Found opponent! Start battle immediately
                opponent_id = waiting_battles[battle_config]["user_id"]
                opponent_callback = waiting_battles[battle_config]["callback"]
                del waiting_battles[battle_config]
                
                # Create battle record in database
                battle_id = await db.create_battle_record(
                    battle_session["session_id"],
                    battle_session["type"],
                    callback.from_user.id,
                    opponent_id
                )
                
                # Start battle for both players
                await start_battle_for_players(callback, opponent_callback, battle_session, battle_id, scope_display)
                
            else:
                # No opponent found, add to waiting list
                waiting_battles[battle_config] = {
                    "user_id": callback.from_user.id,
                    "callback": callback,
                    "battle_session": battle_session,
                    "scope_display": scope_display
                }
                
                await state.set_state(BattleStates.waiting_for_opponent)
                await callback.message.edit_text(
                    Messages.SEARCHING_OPPONENT,
                    reply_markup=get_back_to_main_keyboard()
                )
                await callback.answer()
        
        else:
            # Battle with friend - create shareable link
            battle_link = f"https://t.me/{callback.bot.username}?start=battle_{battle_session['session_id']}_{session.battle_scope}"
            
            await state.set_state(BattleStates.sharing_battle_link)
            await callback.message.edit_text(
                Messages.BATTLE_LINK_CREATED.format(battle_link=battle_link),
                reply_markup=get_share_battle_keyboard(battle_link)
            )
            await callback.answer()
    
    except Exception as e:
        logger.error(f"Error creating battle session: {e}")
        await callback.message.edit_text(
            Messages.BATTLE_SESSION_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

async def start_battle_for_players(callback1: CallbackQuery, callback2: CallbackQuery, 
                                 battle_session: dict, battle_id: int, scope_display: str):
    """Start battle for both players"""
    try:
        # Get questions for battle
        questions = await db.get_battle_questions(battle_session["word_ids"])
        
        if len(questions) < 10:
            logger.error(f"Not enough questions for battle: {len(questions)}")
            return
        
        # Store battle data
        battle_data = {
            "questions": questions,
            "players": {
                callback1.from_user.id: {
                    "callback": callback1,
                    "answers": [],
                    "start_time": time.time(),
                    "current_question": 0,
                    "completed": False
                },
                callback2.from_user.id: {
                    "callback": callback2,
                    "answers": [],
                    "start_time": time.time(),
                    "current_question": 0,
                    "completed": False
                }
            },
            "battle_id": battle_id,
            "scope_display": scope_display
        }
        
        active_battles[battle_id] = battle_data
        
        # Update user sessions
        session1 = get_user_session(callback1.from_user.id)
        session1.current_battle_id = battle_id
        session1.start_time = time.time()
        
        session2 = get_user_session(callback2.from_user.id)
        session2.current_battle_id = battle_id
        session2.start_time = time.time()
        
        # Send battle start message to both players
        start_message = Messages.BATTLE_STARTING.format(
            book_title=scope_display,
            scope=scope_display,
            player1_name=callback1.from_user.first_name,
            player2_name=callback2.from_user.first_name
        )
        
        await callback1.message.edit_text(start_message)
        await callback2.message.edit_text(start_message)
        
        # Wait a moment then send first question
        await asyncio.sleep(2)
        await send_question_to_player(callback1.from_user.id, battle_id, 0)
        await send_question_to_player(callback2.from_user.id, battle_id, 0)
        
    except Exception as e:
        logger.error(f"Error starting battle: {e}")

async def send_question_to_player(user_id: int, battle_id: int, question_index: int):
    """Send question to specific player"""
    try:
        if battle_id not in active_battles:
            return
        
        battle_data = active_battles[battle_id]
        if user_id not in battle_data["players"]:
            return
        
        player_data = battle_data["players"][user_id]
        if question_index >= len(battle_data["questions"]) or player_data["completed"]:
            return
        
        question = battle_data["questions"][question_index]
        
        # Shuffle answer options
        from database.queries import shuffle_answer_options
        options, correct_index = shuffle_answer_options(
            question["correct_answer"], 
            question["distractors"]
        )
        
        # Store correct answer index for this question
        player_data[f"correct_index_{question_index}"] = correct_index
        
        question_text = Messages.BATTLE_QUESTION.format(
            current=question_index + 1,
            total=len(battle_data["questions"]),
            uzbek_word=question["uzbek"]
        )
        
        callback = player_data["callback"]
        await callback.message.edit_text(
            question_text,
            reply_markup=get_battle_question_keyboard(options)
        )
        
    except Exception as e:
        logger.error(f"Error sending question: {e}")

@router.callback_query(F.data.startswith("answer_"))
async def answer_handler(callback: CallbackQuery, state: FSMContext):
    """Handle battle answer"""
    try:
        answer_index = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        session = get_user_session(user_id)
        battle_id = session.current_battle_id
        
        if not battle_id or battle_id not in active_battles:
            await callback.answer("Battle not found!")
            return
        
        battle_data = active_battles[battle_id]
        player_data = battle_data["players"][user_id]
        
        if player_data["completed"]:
            await callback.answer("You've already completed this battle!")
            return
        
        current_q = player_data["current_question"]
        correct_index = player_data[f"correct_index_{current_q}"]
        
        # Record answer
        is_correct = answer_index == correct_index
        player_data["answers"].append({
            "question_index": current_q,
            "answer_index": answer_index,
            "is_correct": is_correct,
            "timestamp": time.time()
        })
        
        # Update user progress in database
        question = battle_data["questions"][current_q]
        await db.update_user_progress(user_id, question["id"], is_correct)
        
        # Show answer feedback
        if is_correct:
            feedback = Messages.CORRECT_ANSWER
        else:
            feedback = Messages.WRONG_ANSWER.format(
                correct_answer=question["correct_answer"]
            )
        
        await callback.answer(feedback)
        
        # Move to next question
        player_data["current_question"] += 1
        
        if player_data["current_question"] >= len(battle_data["questions"]):
            # Player completed all questions
            player_data["completed"] = True
            player_data["completion_time"] = time.time() - player_data["start_time"]
            
            # Check if both players completed
            other_player_id = [pid for pid in battle_data["players"].keys() if pid != user_id][0]
            other_player = battle_data["players"][other_player_id]
            
            if other_player["completed"]:
                # Both completed - show results
                await show_battle_results(battle_data)
            else:
                # Wait for other player
                score = sum(1 for ans in player_data["answers"] if ans["is_correct"])
                await callback.message.edit_text(
                    Messages.WAITING_FOR_OPPONENT.format(
                        your_score=score,
                        your_time=f"{player_data['completion_time']:.1f}"
                    ),
                    reply_markup=get_back_to_main_keyboard()
                )
        else:
            # Send next question
            await send_question_to_player(user_id, battle_id, player_data["current_question"])
        
    except Exception as e:
        logger.error(f"Error handling answer: {e}")
        await callback.answer("Error processing answer!")

async def show_battle_results(battle_data: dict):
    """Show battle results to both players"""
    try:
        players = list(battle_data["players"].items())
        player1_id, player1_data = players[0]
        player2_id, player2_data = players[1]
        
        # Calculate scores
        player1_score = sum(1 for ans in player1_data["answers"] if ans["is_correct"])
        player2_score = sum(1 for ans in player2_data["answers"] if ans["is_correct"])
        
        # Update battle result in database
        await db.update_battle_result(
            battle_data["battle_id"],
            player1_score,
            player2_score
        )
        
        # Determine winner
        if player1_score > player2_score:
            winner_name = player1_data["callback"].from_user.first_name
        elif player2_score > player1_score:
            winner_name = player2_data["callback"].from_user.first_name
        else:
            winner_name = "Draw!"
        
        # Create results message
        results_message = Messages.BATTLE_COMPLETED.format(
            player1_name=player1_data["callback"].from_user.first_name,
            player1_score=player1_score,
            player1_time=f"{player1_data['completion_time']:.1f}",
            player2_name=player2_data["callback"].from_user.first_name,
            player2_score=player2_score,
            player2_time=f"{player2_data['completion_time']:.1f}",
            winner_name=winner_name
        )
        
        # Send results to both players
        await player1_data["callback"].message.edit_text(
            results_message,
            reply_markup=get_back_to_main_keyboard()
        )
        await player2_data["callback"].message.edit_text(
            results_message,
            reply_markup=get_back_to_main_keyboard()
        )
        
        # Clean up battle data
        del active_battles[battle_data["battle_id"]]
        
    except Exception as e:
        logger.error(f"Error showing results: {e}")

@router.callback_query(F.data == "my_stats")
async def my_stats_handler(callback: CallbackQuery):
    """Handle stats viewing"""
    try:
        stats = await db.get_user_battle_stats(callback.from_user.id)
        
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
        
        await callback.message.edit_text(
            stats_message,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await callback.message.edit_text(
            "❌ Error fetching statistics.",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

@router.callback_query(F.data == "view_books")
async def view_books_handler(callback: CallbackQuery):
    """Handle books viewing"""
    try:
        books = await db.get_all_books()
        
        if not books:
            books_message = "📚 No books available."
        else:
            books_list = []
            for book in books:
                topics = await db.get_topics_by_book(book["id"])
                books_list.append(f"📖 **{book['title']}**\n   • {len(topics)} topics, {book['total_words']} words")
            
            books_message = "📚 **Available Books:**\n\n" + "\n\n".join(books_list)
        
        await callback.message.edit_text(
            books_message,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        await callback.message.edit_text(
            "❌ Error fetching books.",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

# Back navigation handlers
@router.callback_query(F.data == "back_to_battle_type")
async def back_to_battle_type_handler(callback: CallbackQuery, state: FSMContext):
    """Handle back to battle type selection"""
    await state.set_state(BattleStates.waiting_for_battle_type)
    
    await callback.message.edit_text(
        Messages.CHOOSE_BATTLE_TYPE,
        reply_markup=get_battle_type_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_book_selection")
async def back_to_book_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Handle back to book selection"""
    session = get_user_session(callback.from_user.id)
    await state.set_state(BattleStates.waiting_for_book_selection)
    
    try:
        books = await db.get_all_books()
        book_options = [(book["id"], book["title"]) for book in books]
        
        await callback.message.edit_text(
            f"✅ Battle type: {session.battle_type.title()}\n\n{Messages.CHOOSE_BOOK}",
            reply_markup=get_book_selection_keyboard(book_options)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in back to book selection: {e}")
        await callback.answer("Error occurred!")

@router.callback_query(F.data == "back_to_scope_selection")
async def back_to_scope_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Handle back to scope selection"""
    session = get_user_session(callback.from_user.id)
    await state.set_state(BattleStates.waiting_for_scope_selection)
    
    try:
        book = await db.get_book_by_id(session.selected_book_id)
        await callback.message.edit_text(
            f"✅ Selected book: {book['title']}\n\n{Messages.CHOOSE_SCOPE}",
            reply_markup=get_scope_selection_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in back to scope selection: {e}")
        await callback.answer("Error occurred!")

def register_callback_handlers(dp):
    """Register callback handlers"""
    dp.include_router(router)