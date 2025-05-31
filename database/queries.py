"""
VOCABULARY BATTLE BOT - DATABASE QUERIES PART 1
=============================================

This file contains database initialization and user management queries.
Each query includes complete documentation with parameters and return values.

Author: Vocabulary Battle Bot Team
Version: 3.0
Last Updated: 2025
"""

import aiosqlite
import json
import random
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VocabularyBattleDB:
    """Complete database manager for vocabulary battle bot"""
    
    def __init__(self, db_path: str = "vocabulary.db"):
        self.db_path = db_path

    # ==================== DATABASE INITIALIZATION ====================
    
    async def init_database(self) -> bool:
        """
        Initialize database with all required tables
        
        Parameters: None
        Returns: bool - Success status
        Usage: success = await db.init_database()
        
        Creates tables: books, topics, words, word_distractors, learning_parts,
        battle_sessions_topic, battle_sessions_book, users, user_learning_progress,
        battle_history, user_statistics, friend_battles
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Core vocabulary tables
                await self._create_vocabulary_tables(db)
                # User management tables
                await self._create_user_tables(db)
                # Battle and progress tables
                await self._create_battle_tables(db)
                # Performance indexes
                await self._create_indexes(db)
                
                await db.commit()
                logger.info("Database initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    async def _create_vocabulary_tables(self, db):
        """Create core vocabulary structure tables"""
        
        # Books table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                total_words INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Topics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY,
                book_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                topic_order INTEGER NOT NULL,
                word_count INTEGER DEFAULT 0,
                FOREIGN KEY (book_id) REFERENCES books(id),
                UNIQUE(book_id, topic_order)
            )
        """)
        
        # Words table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                uzbek TEXT NOT NULL,
                translation TEXT NOT NULL,
                word_photo TEXT,
                note TEXT,
                word_order INTEGER,
                difficulty_level INTEGER DEFAULT 1,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        """)
        
        # Pre-generated distractors for optimization
        await db.execute("""
            CREATE TABLE IF NOT EXISTS word_distractors (
                id INTEGER PRIMARY KEY,
                word_id INTEGER NOT NULL,
                distractor_1 TEXT NOT NULL,
                distractor_2 TEXT NOT NULL,
                distractor_3 TEXT NOT NULL,
                FOREIGN KEY (word_id) REFERENCES words(id),
                UNIQUE(word_id)
            )
        """)
        
        # Learning parts - pre-calculated for optimization
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learning_parts (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                part_number INTEGER NOT NULL,
                part_size INTEGER NOT NULL,
                word_ids TEXT NOT NULL,
                FOREIGN KEY (topic_id) REFERENCES topics(id),
                UNIQUE(topic_id, part_number)
            )
        """)

    async def _create_user_tables(self, db):
        """Create user management tables"""
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'en',
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User learning progress
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_learning_progress (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                correct_count INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                last_seen TIMESTAMP,
                mastery_level INTEGER DEFAULT 0,
                FOREIGN KEY (word_id) REFERENCES words(id),
                UNIQUE(user_id, word_id)
            )
        """)
        
        # User statistics for quick access
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_statistics (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                total_battles INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                total_draws INTEGER DEFAULT 0,
                best_score INTEGER DEFAULT 0,
                average_score REAL DEFAULT 0.0,
                words_learned INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_battle TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    async def _create_battle_tables(self, db):
        """Create battle-related tables"""
        
        # Battle sessions for topics
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battle_sessions_topic (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                word_ids TEXT NOT NULL,
                FOREIGN KEY (topic_id) REFERENCES topics(id),
                UNIQUE(topic_id, session_number)
            )
        """)
        
        # Battle sessions for books
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battle_sessions_book (
                id INTEGER PRIMARY KEY,
                book_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                word_ids TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id),
                UNIQUE(book_id, session_number)
            )
        """)
        
        # Battle history
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battle_history (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                winner_id INTEGER,
                player1_score INTEGER DEFAULT 0,
                player2_score INTEGER DEFAULT 0,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Friend battles for sharing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS friend_battles (
                id INTEGER PRIMARY KEY,
                battle_code TEXT UNIQUE NOT NULL,
                creator_id INTEGER NOT NULL,
                session_id INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

    async def _create_indexes(self, db):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_words_topic ON words(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_topics_book ON topics(book_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_parts_topic ON learning_parts(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_battle_sessions_topic ON battle_sessions_topic(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_battle_sessions_book ON battle_sessions_book(book_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_learning_progress(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_progress_word ON user_learning_progress(word_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_battle_history_players ON battle_history(player1_id, player2_id)",
            "CREATE INDEX IF NOT EXISTS idx_friend_battles_code ON friend_battles(battle_code)"
        ]
        
        for index in indexes:
            await db.execute(index)

    # ==================== USER MANAGEMENT QUERIES ====================
    
    async def create_or_update_user(self, telegram_id: int, username: str = None, 
                                  first_name: str = None, last_name: str = None) -> Optional[Dict]:
        """
        Create new user or update existing user information
        
        Parameters:
        - telegram_id: int - Telegram user ID (required)
        - username: str - Telegram username (optional)
        - first_name: str - User's first name (optional)
        - last_name: str - User's last name (optional)
        
        Returns: dict or None
        - Success: {'id': int, 'telegram_id': int, 'username': str, 'first_name': str, 
                   'last_name': str, 'created_at': str}
        - Failure: None
        
        Usage: user = await db.create_or_update_user(12345, "john_doe", "John", "Doe")
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Check if user exists
                cursor = await db.execute(
                    "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
                )
                existing_user = await cursor.fetchone()
                
                if existing_user:
                    # Update existing user
                    await db.execute("""
                        UPDATE users SET 
                        username = ?, first_name = ?, last_name = ?, last_active = CURRENT_TIMESTAMP
                        WHERE telegram_id = ?
                    """, (username, first_name, last_name, telegram_id))
                else:
                    # Create new user
                    await db.execute("""
                        INSERT INTO users (telegram_id, username, first_name, last_name)
                        VALUES (?, ?, ?, ?)
                    """, (telegram_id, username, first_name, last_name))
                    
                    # Create user statistics record
                    await db.execute("""
                        INSERT INTO user_statistics (user_id) VALUES (?)
                    """, (telegram_id,))
                
                await db.commit()
                
                # Return user data
                cursor = await db.execute(
                    "SELECT id, telegram_id, username, first_name, last_name, created_at FROM users WHERE telegram_id = ?", 
                    (telegram_id,)
                )
                user_data = await cursor.fetchone()
                
                if user_data:
                    return {
                        'id': user_data[0],
                        'telegram_id': user_data[1],
                        'username': user_data[2],
                        'first_name': user_data[3],
                        'last_name': user_data[4],
                        'created_at': user_data[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in create_or_update_user: {e}")
            return None

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """
        Get user information by Telegram ID
        
        Parameters:
        - telegram_id: int - Telegram user ID
        
        Returns: dict or None
        - Success: {'id': int, 'telegram_id': int, 'username': str, 'first_name': str, 
                   'last_name': str, 'language_code': str, 'is_premium': bool, 
                   'created_at': str, 'last_active': str}
        - Not found: None
        
        Usage: user = await db.get_user_by_telegram_id(12345)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
                )
                user = await cursor.fetchone()
                
                if user:
                    return {
                        'id': user[0],
                        'telegram_id': user[1],
                        'username': user[2],
                        'first_name': user[3],
                        'last_name': user[4],
                        'language_code': user[5],
                        'is_premium': user[6],
                        'created_at': user[7],
                        'last_active': user[8]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_user_by_telegram_id: {e}")
            return None

    async def update_user_language(self, telegram_id: int, language_code: str) -> bool:
        """
        Update user's language preference
        
        Parameters:
        - telegram_id: int - Telegram user ID
        - language_code: str - Language code (e.g., 'en', 'uz', 'ru')
        
        Returns: bool - Success status
        
        Usage: success = await db.update_user_language(12345, 'uz')
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET language_code = ? WHERE telegram_id = ?",
                    (language_code, telegram_id)
                )
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error in update_user_language: {e}")
            return False

    async def get_user_statistics(self, telegram_id: int) -> Optional[Dict]:
        """
        Get user's battle statistics
        
        Parameters:
        - telegram_id: int - Telegram user ID
        
        Returns: dict or None
        - Success: {'total_battles': int, 'total_wins': int, 'total_losses': int, 
                   'total_draws': int, 'best_score': int, 'average_score': float, 
                   'words_learned': int, 'current_streak': int, 'longest_streak': int, 
                   'last_battle': str}
        - Not found: None
        
        Usage: stats = await db.get_user_statistics(12345)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT total_battles, total_wins, total_losses, total_draws,
                           best_score, average_score, words_learned, current_streak,
                           longest_streak, last_battle
                    FROM user_statistics WHERE user_id = ?
                """, (telegram_id,))
                
                stats = await cursor.fetchone()
                
                if stats:
                    return {
                        'total_battles': stats[0],
                        'total_wins': stats[1],
                        'total_losses': stats[2],
                        'total_draws': stats[3],
                        'best_score': stats[4],
                        'average_score': stats[5],
                        'words_learned': stats[6],
                        'current_streak': stats[7],
                        'longest_streak': stats[8],
                        'last_battle': stats[9]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_user_statistics: {e}")
            return None

"""
VOCABULARY BATTLE BOT - DATABASE QUERIES PART 2
=============================================

This file contains vocabulary data management queries (books, topics, words).
Each query includes complete documentation with parameters and return values.

Author: Vocabulary Battle Bot Team
Version: 3.0
Last Updated: 2025
"""

    # ==================== BOOK MANAGEMENT QUERIES ====================
    
    async def create_book(self, title: str, description: str = None) -> Optional[Dict]:
        """
        Create a new vocabulary book
        
        Parameters:
        - title: str - Book title (required)
        - description: str - Book description (optional)
        
        Returns: dict or None
        - Success: {'id': int, 'title': str, 'description': str, 'total_words': int, 'created_at': str}
        - Failure: None
        
        Usage: book = await db.create_book("English Basics", "Beginner level vocabulary")
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "INSERT INTO books (title, description) VALUES (?, ?)",
                    (title, description)
                )
                book_id = cursor.lastrowid
                await db.commit()
                
                # Return created book data
                cursor = await db.execute(
                    "SELECT id, title, description, total_words, created_at FROM books WHERE id = ?",
                    (book_id,)
                )
                book_data = await cursor.fetchone()
                
                if book_data:
                    return {
                        'id': book_data[0],
                        'title': book_data[1],
                        'description': book_data[2],
                        'total_words': book_data[3],
                        'created_at': book_data[4]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in create_book: {e}")
            return None

    async def get_all_books(self) -> List[Dict]:
        """
        Get all vocabulary books with their statistics
        
        Parameters: None
        
        Returns: list
        - Success: [{'id': int, 'title': str, 'description': str, 'total_words': int, 
                    'topic_count': int, 'created_at': str}]
        - Empty: []
        
        Usage: books = await db.get_all_books()
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT b.id, b.title, b.description, b.total_words, b.created_at,
                           COUNT(t.id) as topic_count
                    FROM books b
                    LEFT JOIN topics t ON b.id = t.book_id
                    GROUP BY b.id, b.title, b.description, b.total_words, b.created_at
                    ORDER BY b.created_at DESC
                """)
                books = await cursor.fetchall()
                
                return [
                    {
                        'id': book[0],
                        'title': book[1],
                        'description': book[2],
                        'total_words': book[3],
                        'created_at': book[4],
                        'topic_count': book[5]
                    }
                    for book in books
                ]
                
        except Exception as e:
            logger.error(f"Error in get_all_books: {e}")
            return []

    async def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """
        Get book details by ID
        
        Parameters:
        - book_id: int - Book ID
        
        Returns: dict or None
        - Success: {'id': int, 'title': str, 'description': str, 'total_words': int, 
                   'topic_count': int, 'created_at': str}
        - Not found: None
        
        Usage: book = await db.get_book_by_id(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT b.id, b.title, b.description, b.total_words, b.created_at,
                           COUNT(t.id) as topic_count
                    FROM books b
                    LEFT JOIN topics t ON b.id = t.book_id
                    WHERE b.id = ?
                    GROUP BY b.id, b.title, b.description, b.total_words, b.created_at
                """, (book_id,))
                book = await cursor.fetchone()
                
                if book:
                    return {
                        'id': book[0],
                        'title': book[1],
                        'description': book[2],
                        'total_words': book[3],
                        'created_at': book[4],
                        'topic_count': book[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_book_by_id: {e}")
            return None

    async def update_book_word_count(self, book_id: int) -> bool:
        """
        Update total word count for a book (call after adding/removing words)
        
        Parameters:
        - book_id: int - Book ID
        
        Returns: bool - Success status
        
        Usage: success = await db.update_book_word_count(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE books SET total_words = (
                        SELECT COUNT(w.id)
                        FROM words w
                        JOIN topics t ON w.topic_id = t.id
                        WHERE t.book_id = ?
                    )
                    WHERE id = ?
                """, (book_id, book_id))
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error in update_book_word_count: {e}")
            return False

    # ==================== TOPIC MANAGEMENT QUERIES ====================
    
    async def create_topic(self, book_id: int, title: str, topic_order: int) -> Optional[Dict]:
        """
        Create a new topic within a book
        
        Parameters:
        - book_id: int - Parent book ID (required)
        - title: str - Topic title (required)
        - topic_order: int - Order within book (1-10) (required)
        
        Returns: dict or None
        - Success: {'id': int, 'book_id': int, 'title': str, 'topic_order': int, 'word_count': int}
        - Failure: None
        
        Usage: topic = await db.create_topic(1, "Daily Activities", 1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "INSERT INTO topics (book_id, title, topic_order) VALUES (?, ?, ?)",
                    (book_id, title, topic_order)
                )
                topic_id = cursor.lastrowid
                await db.commit()
                
                # Return created topic data
                cursor = await db.execute(
                    "SELECT id, book_id, title, topic_order, word_count FROM topics WHERE id = ?",
                    (topic_id,)
                )
                topic_data = await cursor.fetchone()
                
                if topic_data:
                    return {
                        'id': topic_data[0],
                        'book_id': topic_data[1],
                        'title': topic_data[2],
                        'topic_order': topic_data[3],
                        'word_count': topic_data[4]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in create_topic: {e}")
            return None

    async def get_topics_by_book(self, book_id: int) -> List[Dict]:
        """
        Get all topics for a specific book, ordered by topic_order
        
        Parameters:
        - book_id: int - Book ID
        
        Returns: list
        - Success: [{'id': int, 'book_id': int, 'title': str, 'topic_order': int, 'word_count': int}]
        - Empty: []
        
        Usage: topics = await db.get_topics_by_book(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, book_id, title, topic_order, word_count FROM topics WHERE book_id = ? ORDER BY topic_order",
                    (book_id,)
                )
                topics = await cursor.fetchall()
                
                return [
                    {
                        'id': topic[0],
                        'book_id': topic[1],
                        'title': topic[2],
                        'topic_order': topic[3],
                        'word_count': topic[4]
                    }
                    for topic in topics
                ]
                
        except Exception as e:
            logger.error(f"Error in get_topics_by_book: {e}")
            return []

    async def get_topic_by_id(self, topic_id: int) -> Optional[Dict]:
        """
        Get topic details by ID
        
        Parameters:
        - topic_id: int - Topic ID
        
        Returns: dict or None
        - Success: {'id': int, 'book_id': int, 'title': str, 'topic_order': int, 'word_count': int}
        - Not found: None
        
        Usage: topic = await db.get_topic_by_id(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, book_id, title, topic_order, word_count FROM topics WHERE id = ?",
                    (topic_id,)
                )
                topic = await cursor.fetchone()
                
                if topic:
                    return {
                        'id': topic[0],
                        'book_id': topic[1],
                        'title': topic[2],
                        'topic_order': topic[3],
                        'word_count': topic[4]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_topic_by_id: {e}")
            return None

    async def update_topic_word_count(self, topic_id: int) -> bool:
        """
        Update word count for a topic (call after adding/removing words)
        
        Parameters:
        - topic_id: int - Topic ID
        
        Returns: bool - Success status
        
        Usage: success = await db.update_topic_word_count(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE topics SET word_count = (
                        SELECT COUNT(*) FROM words WHERE topic_id = ?
                    )
                    WHERE id = ?
                """, (topic_id, topic_id))
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error in update_topic_word_count: {e}")
            return False

    # ==================== WORD MANAGEMENT QUERIES ====================
    
    async def create_word(self, topic_id: int, uzbek: str, translation: str, 
                         word_photo: str = None, note: str = None, 
                         word_order: int = None, difficulty_level: int = 1) -> Optional[Dict]:
        """
        Create a new word in a topic
        
        Parameters:
        - topic_id: int - Parent topic ID (required)
        - uzbek: str - Uzbek word (required)
        - translation: str - English translation (required)
        - word_photo: str - Photo URL/path (optional)
        - note: str - Additional notes (optional)
        - word_order: int - Order within topic (optional, auto-assigned if None)
        - difficulty_level: int - Difficulty 1-5 (default: 1)
        
        Returns: dict or None
        - Success: {'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 
                   'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}
        - Failure: None
        
        Usage: word = await db.create_word(1, "kitob", "book", None, "Used for reading")
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Auto-assign word_order if not provided
                if word_order is None:
                    cursor = await db.execute(
                        "SELECT COALESCE(MAX(word_order), 0) + 1 FROM words WHERE topic_id = ?",
                        (topic_id,)
                    )
                    word_order = (await cursor.fetchone())[0]
                
                cursor = await db.execute("""
                    INSERT INTO words (topic_id, uzbek, translation, word_photo, note, word_order, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (topic_id, uzbek, translation, word_photo, note, word_order, difficulty_level))
                
                word_id = cursor.lastrowid
                await db.commit()
                
                # Update topic word count
                await self.update_topic_word_count(topic_id)
                
                # Return created word data
                cursor = await db.execute(
                    "SELECT * FROM words WHERE id = ?", (word_id,)
                )
                word_data = await cursor.fetchone()
                
                if word_data:
                    return {
                        'id': word_data[0],
                        'topic_id': word_data[1],
                        'uzbek': word_data[2],
                        'translation': word_data[3],
                        'word_photo': word_data[4],
                        'note': word_data[5],
                        'word_order': word_data[6],
                        'difficulty_level': word_data[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in create_word: {e}")
            return None

    async def get_words_by_topic(self, topic_id: int, limit: int = None) -> List[Dict]:
        """
        Get all words for a specific topic, ordered by word_order
        
        Parameters:
        - topic_id: int - Topic ID
        - limit: int - Maximum number of words to return (optional)
        
        Returns: list
        - Success: [{'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 
                    'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}]
        - Empty: []
        
        Usage: words = await db.get_words_by_topic(1, limit=20)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT * FROM words WHERE topic_id = ? ORDER BY word_order"
                params = [topic_id]
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor = await db.execute(query, params)
                words = await cursor.fetchall()
                
                return [
                    {
                        'id': word[0],
                        'topic_id': word[1],
                        'uzbek': word[2],
                        'translation': word[3],
                        'word_photo': word[4],
                        'note': word[5],
                        'word_order': word[6],
                        'difficulty_level': word[7]
                    }
                    for word in words
                ]
                
        except Exception as e:
            logger.error(f"Error in get_words_by_topic: {e}")
            return []

    async def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """
        Get word details by ID
        
        Parameters:
        - word_id: int - Word ID
        
        Returns: dict or None
        - Success: {'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 
                   'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}
        - Not found: None
        
        Usage: word = await db.get_word_by_id(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT * FROM words WHERE id = ?", (word_id,))
                word = await cursor.fetchone()
                
                if word:
                    return {
                        'id': word[0],
                        'topic_id': word[1],
                        'uzbek': word[2],
                        'translation': word[3],
                        'word_photo': word[4],
                        'note': word[5],
                        'word_order': word[6],
                        'difficulty_level': word[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_word_by_id: {e}")
            return None

    async def get_words_by_ids(self, word_ids: List[int]) -> List[Dict]:
        """
        Get multiple words by their IDs (useful for battle sessions)
        
        Parameters:
        - word_ids: list - List of word IDs
        
        Returns: list
        - Success: [{'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 
                    'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}]
        - Empty: []
        
        Usage: words = await db.get_words_by_ids([1, 2, 3, 4, 5])
        """
        try:
            if not word_ids:
                return []
                
            async with aiosqlite.connect(self.db_path) as db:
                placeholders = ','.join('?' * len(word_ids))
                cursor = await db.execute(
                    f"SELECT * FROM words WHERE id IN ({placeholders})",
                    word_ids
                )
                words = await cursor.fetchall()
                
                return [
                    {
                        'id': word[0],
                        'topic_id': word[1],
                        'uzbek': word[2],
                        'translation': word[3],
                        'word_photo': word[4],
                        'note': word[5],
                        'word_order': word[6],
                        'difficulty_level': word[7]
                    }
                    for word in words
                ]
                
        except Exception as e:
            logger.error(f"Error in get_words_by_ids: {e}")
            return []

    async def update_word(self, word_id: int, **kwargs) -> bool:
        """
        Update word fields
        
        Parameters:
        - word_id: int - Word ID (required)
        - **kwargs: Any word field to update (uzbek, translation, word_photo, note, 
                   word_order, difficulty_level)
        
        Returns: bool - Success status
        
        Usage: success = await db.update_word(1, translation="new translation", note="updated note")
        """
        try:
            if not kwargs:
                return True
                
            async with aiosqlite.connect(self.db_path) as db:
                # Build update query dynamically
                set_clauses = []
                params = []
                
                for field, value in kwargs.items():
                    if field in ['uzbek', 'translation', 'word_photo', 'note', 'word_order', 'difficulty_level']:
                        set_clauses.append(f"{field} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return False
                
                params.append(word_id)
                query = f"UPDATE words SET {', '.join(set_clauses)} WHERE id = ?"
                
                await db.execute(query, params)
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error in update_word: {e}")
            return False

    async def delete_word(self, word_id: int) -> bool:
        """
        Delete a word and update related counts
        
        Parameters:
        - word_id: int - Word ID
        
        Returns: bool - Success status
        
        Usage: success = await db.delete_word(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get topic_idid before deletion
                cursor = await db.execute("SELECT topic_id FROM words WHERE id = ?", (word_id,))
                result = await cursor.fetchone()
                
                if not result:
                    return False
                    
                topic_id = result[0]
                
                # Delete word and related data
                await db.execute("DELETE FROM word_distractors WHERE word_id = ?", (word_id,))
                await db.execute("DELETE FROM user_learning_progress WHERE word_id = ?", (word_id,))
                await db.execute("DELETE FROM words WHERE id = ?", (word_id,))
                
                await db.commit()
                
                # Update topic word count
                await self.update_topic_word_count(topic_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Error in delete_word: {e}")
            return False

