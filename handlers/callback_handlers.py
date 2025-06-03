from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
import asyncio
import time
import json
import random

from json_maker import create_pretty_json

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

# Storage for active battles
active_battles = {}
waiting_battles = {}

def shuffle_answer_options(correct_answer, distractors):
    """Shuffle answer options and return options with correct index"""
    options = distractors + [correct_answer]
    random.shuffle(options)
    correct_index = options.index(correct_answer)
    return options, correct_index

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
            f"{Messages.BATTLE_TYPE_SELECTED.format(battle_type=battle_type.title())}\n\n{Messages.CHOOSE_BOOK}",
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
            f"{Messages.BOOK_SELECTED.format(book_title=book['title'])}\n\n{Messages.CHOOSE_SCOPE}",
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
async def scope_selection_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle scope selection"""
    scope = callback.data.split("_")[1]
    
    session = get_user_session(callback.from_user.id)
    session.battle_scope = scope
    
    if scope == "book":
        # Battle with entire book - start battle creation
        await create_battle_session(callback, state, session, bot)
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
                f"{Messages.SCOPE_SELECTED.format(scope_display='Specific Topic')}\n\n{Messages.CHOOSE_TOPIC}",
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
async def topic_selection_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle topic selection"""
    topic_id = int(callback.data.split("_")[-1])
    
    session = get_user_session(callback.from_user.id)
    session.selected_topic_id = topic_id
    
    # Now create battle session
    await create_battle_session(callback, state, session, bot)

async def create_battle_session(callback: CallbackQuery, state: FSMContext, session, bot: Bot):
    """Create battle session based on user choices"""
    try:
        # Get battle session from database
        if session.battle_scope == "book":
            # Get random battle session for the book
            battle_session = await db.get_random_battle_session_book(session.selected_book_id)
            book = await db.get_book_by_id(session.selected_book_id)
            scope_display = Messages.SCOPE_ALL_VOCABULARIES.format(book_title=book['title']) if book else Messages.BOOK_BATTLE_DEFAULT
            battle_config = f"book_{session.selected_book_id}"
        else:
            # Get random battle session for the topic
            battle_session = await db.get_random_battle_session_topic(session.selected_topic_id)
            topic = await db.get_topic_by_id(session.selected_topic_id)
            scope_display = Messages.SCOPE_SPECIFIC_TOPIC.format(topic_title=topic['title']) if topic else Messages.TOPIC_BATTLE_DEFAULT
            battle_config = f"topic_{session.selected_topic_id}"
        

        if not battle_session:
            await callback.message.edit_text(
                Messages.BATTLE_SESSION_ERROR,
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()
            return
        
        if session.battle_type == "random":
            # Try to find waiting opponent with same configuration
            check_if_opponent_av = await db.get_random_opponent(requesting_player_id=callback.from_user.id, battle_config=battle_config)
            if check_if_opponent_av:
                await callback.message.delete()
                # Found opponent! Start battle immediately
                opponent_data = check_if_opponent_av
                opponent_id = opponent_data[1]
                opponent_message_id = opponent_data[2]
                await db.remove_pending_request(player1_id=callback.from_user.id, player2_id=opponent_id)
                
                battle_id = await db.create_battle(
                    session_id = battle_session["id"], 
                    session_type = battle_config, 
                    player1_id = callback.from_user.id, 
                    player2_id = opponent_id
                )
                
                # Start battle for both players
                msg_user_data={
                    'player1': {
                        'user_id': callback.from_user.id,
                        'msg_id': callback.message.message_id
                    },
                    'player2': {
                        'user_id': opponent_id,
                        'msg_id': opponent_message_id
                    }
                }
                await start_battle_for_players(msg_user_data, battle_session, battle_id, battle_config, scope_display, bot)
                
            else:
                await db.add_pending_request(player_id=callback.from_user.id, message_id=callback.message.message_id, battle_config=battle_config)

                await state.set_state(BattleStates.waiting_for_opponent)
                await callback.message.edit_text(
                    Messages.SEARCHING_OPPONENT,
                    reply_markup=get_back_to_main_keyboard()
                )
                await callback.answer()
        
        else:
            # Battle with friend - create shareable link
            battle_link = f"https://t.me/namu\_robot?start=battle\_{battle_session['id']}\_{session.battle_scope}"
            battle_link_btn = f"https://t.me/namu_robot?start=battle_{battle_session['id']}_{session.battle_scope}"
            
            await state.set_state(BattleStates.sharing_battle_link)
            await callback.message.edit_text(
                Messages.BATTLE_LINK_CREATED.format(battle_link=battle_link),
                reply_markup=get_share_battle_keyboard(battle_link_btn)
            )
            await callback.answer()
    
    except Exception as e:
        logger.error(f"Error creating battle session: {e}")
        await callback.message.edit_text(
            Messages.BATTLE_SESSION_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

async def start_battle_for_players(msg_data: dict, 
                                 battle_session: dict, battle_id: int, battle_config: str, scope_display: str, bot: Bot):
    """Start battle for both players"""
    try:
        # Get words with distractors for battle
        word_ids = battle_session["word_ids"]
        battle_words = await db.get_words_with_distractors(word_ids)
        
        if len(battle_words) < 10:
            logger.error(f"Not enough words with distractors for battle: {len(battle_words)}")
            return
        
        # Create questions from words with distractors
        questions = []
        for word in battle_words:
            if len(word["distractors"]) >= 3:  # Ensure we have enough distractors
                questions.append({
                    "id": word["id"],
                    "uzbek": word["uzbek"],
                    "correct_answer": word["translation"],
                    "distractors": word["distractors"][:3]  # Take first 3 distractors
                })
        
        if len(questions) < 10:
            logger.error(f"Not enough questions with distractors: {len(questions)}")
            return
        
        player1 = msg_data['player1']['user_id']
        player2 = msg_data['player2']['user_id']

        # Send battle start message to both players
        start_message = Messages.BATTLE_STARTING.format(
            book_title=scope_display,
            scope=scope_display,
            countdown_message=Messages.GET_READY_MESSAGE
        )
        
        message_1 = await bot.send_message(chat_id=player1, text=start_message)
        message_2 = await bot.send_message(chat_id=player2, text=start_message)
        
        # Store battle data
        battle_data = {
            "questions": questions[:10],  # Take exactly 10 questions
            "players": {
                player1: {
                    "message": message_1,
                    "answers": [],
                    "start_time": None,  # Will be set when countdown finishes
                    "current_question": 0,
                    "completed": False
                },
                player2: {
                    "message": message_2,
                    "answers": [],
                    "start_time": None,  # Will be set when countdown finishes
                    "current_question": 0,
                    "completed": False
                }
            },
            "battle_id": battle_id,
            "scope_display": scope_display,
            "session_id": battle_session['id'],
            "battle_config": battle_config
        }
        
        active_battles[battle_id] = battle_data
        
        # Update user sessions
        session1 = get_user_session(message_1.chat.id)
        session1.current_battle_id = battle_id
        
        session2 = get_user_session(message_2.chat.id)
        session2.current_battle_id = battle_id
        
        # Countdown sequence with simultaneous updates
        countdown_messages = [Messages.COUNTDOWN_3, Messages.COUNTDOWN_2, Messages.COUNTDOWN_1, Messages.COUNTDOWN_GO]
        await asyncio.sleep(1.5)
        for countdown_text in countdown_messages:
            await asyncio.sleep(1)  # 1 second between each countdown
            
            start_message = Messages.BATTLE_STARTING.format(
                book_title=scope_display,
                scope=scope_display,
                countdown_message=countdown_text
            )

            # Update both messages simultaneously
            await asyncio.gather(
                bot.edit_message_text(
                    text=start_message,
                    chat_id=message_1.chat.id,
                    message_id=message_1.message_id
                ),
                bot.edit_message_text(
                    text=start_message,
                    chat_id=message_2.chat.id,
                    message_id=message_2.message_id
                )
            )        
        
        # Small delay after "GO!" then send first question immediately
        await asyncio.sleep(0.5)
        
        # Set the actual start time after countdown
        current_time = time.time()
        battle_data["players"][player1]["start_time"] = current_time
        battle_data["players"][player2]["start_time"] = current_time
        # Update sessions with start time
        session1.start_time = current_time
        session2.start_time = current_time

        await asyncio.gather(
            send_question_to_player(message_1.chat.id, battle_id, 0),
            send_question_to_player(message_2.chat.id, battle_id, 0)
        )
        
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
        
        # Use the stored message object instead of callback
        message = player_data["message"]

        await message.edit_text(
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
            await callback.answer(Messages.BATTLE_NOT_FOUND)
            return
        
        battle_data = active_battles[battle_id]
        player_data = battle_data["players"][user_id]
        
        if player_data["completed"]:
            await callback.answer(Messages.BATTLE_ALREADY_COMPLETED)
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
        
        # Show answer feedback
        if is_correct:
            feedback = Messages.CORRECT_ANSWER
        else:
            feedback = Messages.WRONG_ANSWER.format(
                correct_answer=battle_data["questions"][current_q]["correct_answer"]
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
        await callback.answer(Messages.ERROR_PROCESSING_ANSWER)

async def show_battle_results(battle_data: dict):
    """Show battle results to both players"""
    try:
        players = list(battle_data["players"].items())
        player1_id, player1_data = players[0]
        player2_id, player2_data = players[1]
        battle_id = battle_data["battle_id"]

        # Calculate scores
        player1_score = sum(1 for ans in player1_data["answers"] if ans["is_correct"])
        player2_score = sum(1 for ans in player2_data["answers"] if ans["is_correct"])

        # Get completion times
        player1_completion_time = player1_data["completion_time"]  # Should be time.time() - start_time
        player2_completion_time = player2_data["completion_time"]  # Should be time.time() - start_time

        # Determine winner
        if player1_score > player2_score:
            # Player 1 has higher score
            winner_id = player1_id
            winner_name = player1_data["message"].chat.first_name
        elif player2_score > player1_score:
            # Player 2 has higher score
            winner_id = player2_id
            winner_name = player2_data["message"].chat.first_name
        elif player1_score == player2_score:
            # Same score - determine by completion time (faster wins)
            if player1_completion_time < player2_completion_time:
                # Player 1 completed faster
                winner_id = player1_id
                winner_name = player1_data["message"].chat.first_name
            elif player2_completion_time < player1_completion_time:
                # Player 2 completed faster
                winner_id = player2_id
                winner_name = player2_data["message"].chat.first_name
            else:
                # Exact same score and completion time (very rare)
                winner_id = None
                winner_name = "Draw!"
        else:
            # This shouldn't happen, but handle as draw
            winner_id = None
            winner_name = "Draw!"
        # Update battle result in database (you'll need to implement this)
        await db.update_battle_result(
            battle_code = battle_id, 
            winner_id = winner_id, 
            player1_score = player1_score, 
            player2_score = player2_score
            )
        
        # Create results message
        results_message = Messages.BATTLE_COMPLETED.format(
            player1_name=player1_data["message"].chat.first_name,
            player1_score=player1_score,
            player1_time=f"{player1_data['completion_time']:.1f}",
            player2_name=player2_data["message"].chat.first_name,
            player2_score=player2_score,
            player2_time=f"{player2_data['completion_time']:.1f}",
            winner_name=winner_name
        )
        
        # Send results to both players
        await player1_data["message"].edit_text(
            results_message,
            reply_markup=get_battle_results_keyboard(player1_id, player2_id, battle_data["battle_config"])
        )
        await player2_data["message"].edit_text(
            results_message,
            reply_markup=get_battle_results_keyboard(player2_id, player1_id, battle_data["battle_config"])
        )
        
        # Clean up battle data
        del active_battles[battle_id]
        
    except Exception as e:
        logger.error(f"Error showing results: {e}")

@router.callback_query(F.data == "my_stats")
async def my_stats_handler(callback: CallbackQuery):
    """Handle stats viewing"""
    try:
        # You'll need to implement get_user_battle_stats in your database
        stats = await db.get_player_stats(callback.from_user.id)
        # example = {
        #     'player_id': player_id,
        #     'total_battles': total_battles,
        #     'wins': wins,
        #     'losses': total_battles - wins,
        #     'win_rate': round(win_rate, 2),
        #     'average_score': round(scores[0] or 0, 2),
        #     'average_opponent_score': round(scores[1] or 0, 2)
        # }
        # Temporary mock stats

        if stats["total_battles"] == 0:
            stats_message = Messages.NO_BATTLES_COMPLETED
        else:
            stats_message = Messages.STATS_DISPLAY.format(
                total_battles=stats['total_battles'],
                wins=stats['wins'],
                losses=stats['losses'],
                win_rate=stats['win_rate'],
                average_score=stats['average_score']
            )
        
        await callback.message.edit_text(
            stats_message,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await callback.message.edit_text(
            Messages.ERROR_FETCHING_STATS,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()

@router.callback_query(F.data == "view_books")
async def view_books_handler(callback: CallbackQuery):
    """Handle books viewing"""
    try:
        books = await db.get_all_books()
        
        if not books:
            books_message = Messages.NO_BOOKS_MESSAGE
        else:
            books_list = []
            for book in books:
                topics = await db.get_topics_by_book(book["id"])
                books_list.append(Messages.BOOK_DISPLAY_FORMAT.format(
                    book_title=book['title'],
                    topic_count=len(topics),
                    word_count=book['total_words']
                ))
            
            books_message = Messages.BOOKS_TITLE + "\n\n".join(books_list)
        
        await callback.message.edit_text(
            books_message,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        await callback.message.edit_text(
            Messages.ERROR_FETCHING_BOOKS,
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
            Messages.BATTLE_TYPE_SELECTED.format(battle_type=session.battle_type.title())+"\n\n"+Messages.CHOOSE_BOOK,
            reply_markup=get_book_selection_keyboard(book_options)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in back to book selection: {e}")
        await callback.answer(Messages.ERROR_OCCURRED)

@router.callback_query(F.data == "back_to_scope_selection")
async def back_to_scope_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Handle back to scope selection"""
    session = get_user_session(callback.from_user.id)
    await state.set_state(BattleStates.waiting_for_scope_selection)
    
    try:
        book = await db.get_book_by_id(session.selected_book_id)
        await callback.message.edit_text(
            Messages.BOOK_SELECTED.format(book_title=book['title'])+"\n\n"+Messages.CHOOSE_SCOPE,
            reply_markup=get_scope_selection_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in back to scope selection: {e}")
        await callback.answer(Messages.ERROR_OCCURRED)

def register_callback_handlers(dp, bot):
    """Register callback handlers"""
    dp.include_router(router)

