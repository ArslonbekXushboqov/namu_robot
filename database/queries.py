"""
Telegram Vocabulary Battle Bot - Part 1: Database Layer
Author: Assistant
Date: 2025-05-31

This is Part 1 of the vocabulary battle bot implementation.
Focus: Database connection and query functions.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations for the vocabulary battle bot"""
    
    def __init__(self, db_path: str = "vocabulary.db"):
        self.db_path = db_path
        
    async def get_connection(self):
        """Get async database connection"""
        return await aiosqlite.connect(self.db_path)
    
    # ==================== BOOK & TOPIC QUERIES ====================
    
    async def get_all_books(self) -> List[Dict]:
        """Get all available books"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT id, title, description, total_words 
                FROM books 
                ORDER BY id
            """)
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1], 
                    "description": row[2],
                    "total_words": row[3]
                } 
                for row in rows
            ]
    
    async def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """Get specific book by ID"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT id, title, description, total_words 
                FROM books 
                WHERE id = ?
            """, (book_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2], 
                    "total_words": row[3]
                }
            return None
    
    async def get_topics_by_book(self, book_id: int) -> List[Dict]:
        """Get all topics for a specific book"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT id, title, topic_order, word_count 
                FROM topics 
                WHERE book_id = ? 
                ORDER BY topic_order
            """, (book_id,))
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "topic_order": row[2],
                    "word_count": row[3]
                }
                for row in rows
            ]
    
    async def get_topic_by_id(self, topic_id: int) -> Optional[Dict]:
        """Get specific topic by ID"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT id, book_id, title, topic_order, word_count 
                FROM topics 
                WHERE id = ?
            """, (topic_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "book_id": row[1],
                    "title": row[2],
                    "topic_order": row[3],
                    "word_count": row[4]
                }
            return None
    
    # ==================== BATTLE SESSION QUERIES ====================
    
    async def get_random_book_battle_session(self, book_id: int) -> Optional[Dict]:
        """Get a random battle session for entire book"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT id, session_number, word_ids 
                FROM battle_sessions_book 
                WHERE book_id = ? 
                ORDER BY RANDOM() 
                LIMIT 1
            """, (book_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "session_number": row[1],
                    "word_ids": json.loads(row[2]),
                    "type": "book",
                    "book_id": book_id
                }
            return None
    
    async def get_random_topic_battle_session(self, topic_id: int) -> Optional[Dict]:
        """Get a random battle session for specific topic"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT id, session_number, word_ids 
                FROM battle_sessions_topic 
                WHERE topic_id = ? 
                ORDER BY RANDOM() 
                LIMIT 1
            """, (topic_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "session_number": row[1], 
                    "word_ids": json.loads(row[2]),
                    "type": "topic",
                    "topic_id": topic_id
                }
            return None
    
    # ==================== WORD & QUESTION QUERIES ====================
    
    async def get_word_with_distractors(self, word_id: int) -> Optional[Dict]:
        """Get word with its distractors for battle question"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT w.id, w.uzbek, w.translation, w.word_photo, w.note,
                       wd.distractor_1, wd.distractor_2, wd.distractor_3
                FROM words w
                LEFT JOIN word_distractors wd ON w.id = wd.word_id
                WHERE w.id = ?
            """, (word_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "uzbek": row[1],
                    "translation": row[2],
                    "word_photo": row[3],
                    "note": row[4],
                    "correct_answer": row[2],
                    "distractors": [row[5], row[6], row[7]] if row[5] else []
                }
            return None
    
    async def get_battle_questions(self, word_ids: List[int]) -> List[Dict]:
        """Get all questions for a battle session"""
        questions = []
        for word_id in word_ids:
            question = await self.get_word_with_distractors(word_id)
            if question:
                questions.append(question)
        return questions
    
    # ==================== USER PROGRESS QUERIES ====================
    
    async def get_user_progress(self, user_id: int, word_id: int) -> Optional[Dict]:
        """Get user's progress for specific word"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT correct_count, total_attempts, mastery_level, last_seen
                FROM user_learning_progress 
                WHERE user_id = ? AND word_id = ?
            """, (user_id, word_id))
            row = await cursor.fetchone()
            if row:
                return {
                    "correct_count": row[0],
                    "total_attempts": row[1],
                    "mastery_level": row[2],
                    "last_seen": row[3]
                }
            return None
    
    async def update_user_progress(self, user_id: int, word_id: int, is_correct: bool):
        """Update user's progress after answering a question"""
        async with await self.get_connection() as db:
            # Check if progress exists
            existing = await self.get_user_progress(user_id, word_id)
            
            if existing:
                # Update existing progress
                new_correct = existing["correct_count"] + (1 if is_correct else 0)
                new_total = existing["total_attempts"] + 1
                new_mastery = min(5, new_correct // 2)  # Simple mastery calculation
                
                await db.execute("""
                    UPDATE user_learning_progress 
                    SET correct_count = ?, total_attempts = ?, 
                        mastery_level = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND word_id = ?
                """, (new_correct, new_total, new_mastery, user_id, word_id))
            else:
                # Create new progress record
                correct_count = 1 if is_correct else 0
                mastery_level = 1 if is_correct else 0
                
                await db.execute("""
                    INSERT INTO user_learning_progress 
                    (user_id, word_id, correct_count, total_attempts, mastery_level, last_seen)
                    VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                """, (user_id, word_id, correct_count, mastery_level))
            
            await db.commit()
    
    # ==================== BATTLE HISTORY QUERIES ====================
    
    async def create_battle_record(self, session_id: int, session_type: str, 
                                 player1_id: int, player2_id: int) -> int:
        """Create new battle record and return battle_id"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                INSERT INTO battle_history 
                (session_id, session_type, player1_id, player2_id)
                VALUES (?, ?, ?, ?)
            """, (session_id, session_type, player1_id, player2_id))
            await db.commit()
            return cursor.lastrowid
    
    async def update_battle_result(self, battle_id: int, player1_score: int, 
                                 player2_score: int):
        """Update battle with final scores and determine winner"""
        winner_id = None
        if player1_score > player2_score:
            winner_id = await self.get_battle_player1_id(battle_id)
        elif player2_score > player1_score:
            winner_id = await self.get_battle_player2_id(battle_id)
        
        async with await self.get_connection() as db:
            await db.execute("""
                UPDATE battle_history 
                SET player1_score = ?, player2_score = ?, winner_id = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (player1_score, player2_score, winner_id, battle_id))
            await db.commit()
    
    async def get_battle_player1_id(self, battle_id: int) -> Optional[int]:
        """Get player1_id from battle"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT player1_id FROM battle_history WHERE id = ?
            """, (battle_id,))
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def get_battle_player2_id(self, battle_id: int) -> Optional[int]:
        """Get player2_id from battle"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT player2_id FROM battle_history WHERE id = ?
            """, (battle_id,))
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def get_user_battle_stats(self, user_id: int) -> Dict:
        """Get user's battle statistics"""
        async with await self.get_connection() as db:
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_battles,
                    SUM(CASE WHEN winner_id = ? THEN 1 ELSE 0 END) as wins,
                    AVG(CASE 
                        WHEN player1_id = ? THEN player1_score 
                        WHEN player2_id = ? THEN player2_score 
                    END) as avg_score
                FROM battle_history 
                WHERE (player1_id = ? OR player2_id = ?) 
                AND completed_at IS NOT NULL
            """, (user_id, user_id, user_id, user_id, user_id))
            row = await cursor.fetchone()
            
            if row and row[0] > 0:
                return {
                    "total_battles": row[0],
                    "wins": row[1] or 0,
                    "losses": row[0] - (row[1] or 0),
                    "win_rate": (row[1] or 0) / row[0] * 100,
                    "avg_score": round(row[2] or 0, 1)
                }
            return {
                "total_battles": 0,
                "wins": 0, 
                "losses": 0,
                "win_rate": 0,
                "avg_score": 0
            }

# ==================== HELPER FUNCTIONS ====================

def shuffle_answer_options(correct_answer: str, distractors: List[str]) -> Tuple[List[str], int]:
    """Shuffle answer options and return options with correct answer index"""
    import random
    
    options = [correct_answer] + distractors
    random.shuffle(options)
    correct_index = options.index(correct_answer)
    
    return options, correct_index

# ==================== TESTING FUNCTIONS ====================

class DatabaseTester:
    """Test database functions - use this in your main bot file"""
    
    @staticmethod
    async def test_basic_queries(db: DatabaseManager):
        """Test basic database queries"""
        try:
            # Test getting books
            books = await db.get_all_books()
            logger.info(f"Found {len(books)} books")
            
            if books:
                book_id = books[0]["id"]
                topics = await db.get_topics_by_book(book_id)
                logger.info(f"Book {book_id} has {len(topics)} topics")
                
                # Test battle session
                battle_session = await db.get_random_book_battle_session(book_id)
                if battle_session:
                    logger.info(f"Battle session has {len(battle_session['word_ids'])} words")
                    
                    # Test getting questions (first 3 words only)
                    questions = await db.get_battle_questions(battle_session['word_ids'][:3])
                    logger.info(f"Got {len(questions)} questions")
                    
            return True
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False



"""
=== COMPLETED IN PART 1 ===
✅ Database connection management with aiosqlite
✅ Book and topic query functions
✅ Battle session retrieval (both book and topic level)
✅ Word and question retrieval with distractors
✅ User progress tracking functions
✅ Battle history management
✅ User statistics calculation
✅ Helper functions for answer shuffling
✅ Comprehensive error handling and logging

=== TODO FOR NEXT PARTS ===
Part 2: Telegram Bot Setup & States
- aiogram3 bot initialization
- FSM (Finite State Machine) for user states
- Basic message handlers for /start and Battle button
- State management for battle configuration choices

Part 3: Battle Configuration Flow
- Book selection handlers
- Topic vs All vocabulary choice handlers
- Random vs Friend battle choice handlers
- Battle link generation for friend battles

Part 4: Battle Matching & Queue System
- User matching system for random battles
- Battle queue management
- Friend battle link sharing and joining

Part 5: Battle Game Logic
- Question presentation with inline keyboards
- Answer validation and scoring
- Timer implementation for questions
- Real-time battle progress tracking

Part 6: Battle Results & Completion
- Score calculation with time bonuses
- Battle completion detection
- Results presentation
- Winner determination and statistics update

Part 7: Additional Features & Polish
- User profile and statistics display
- Battle history viewing
- Error handling and edge cases
- Performance optimizations
"""