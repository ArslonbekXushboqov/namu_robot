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

        # ==================== DISTRACTOR MANAGEMENT ====================
    
    async def create_word_distractors(self, word_id: int, distractor_1: str, 
                                    distractor_2: str, distractor_3: str) -> bool:
        """
        Store 3 wrong answers for a word (for quiz multiple choice)
        
        Parameters:
        - word_id: int - Word ID (required, must exist)
        - distractor_1: str - First wrong answer (required)
        - distractor_2: str - Second wrong answer (required)  
        - distractor_3: str - Third wrong answer (required)
        
        Returns:
        - Success: True
        - Failure: False (if word doesn't exist or distractors already exist)
        
        Usage: success = await db.create_word_distractors(1, "cat", "dog", "bird")
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO word_distractors 
                    (word_id, distractor_1, distractor_2, distractor_3)
                    VALUES (?, ?, ?, ?)
                """, (word_id, distractor_1, distractor_2, distractor_3))
                await db.commit()
                logger.info(f"Created distractors for word_id {word_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in create_word_distractors: {e}")
            return False

    async def get_word_distractors(self, word_id: int) -> Optional[Dict]:
        """
        Get distractors for a specific word
        
        Parameters:
        - word_id: int - Word ID
        
        Returns:
        - Success: {'word_id': int, 'distractor_1': str, 'distractor_2': str, 'distractor_3': str}
        - Not found: None
        
        Usage: distractors = await db.get_word_distractors(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT word_id, distractor_1, distractor_2, distractor_3
                    FROM word_distractors WHERE word_id = ?
                """, (word_id,))
                result = await cursor.fetchone()
                
                if result:
                    return {
                        'word_id': result[0],
                        'distractor_1': result[1],
                        'distractor_2': result[2],
                        'distractor_3': result[3]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_word_distractors: {e}")
            return None

    async def get_words_with_distractors(self, word_ids: List[int]) -> List[Dict]:
        """
        Batch get words with their distractors (optimized for battle sessions)
        
        Parameters:
        - word_ids: list - List of word IDs
        
        Returns:
        - Success: [{'id': int, 'uzbek': str, 'translation': str, 'word_photo': str,
                    'distractors': ['dist1', 'dist2', 'dist3']}]
        - Empty: []
        
        Usage: battle_words = await db.get_words_with_distractors([1, 2, 3, 4, 5])
        """
        try:
            if not word_ids:
                return []
                
            async with aiosqlite.connect(self.db_path) as db:
                placeholders = ','.join('?' * len(word_ids))
                cursor = await db.execute(f"""
                    SELECT w.id, w.uzbek, w.translation, w.word_photo,
                        wd.distractor_1, wd.distractor_2, wd.distractor_3
                    FROM words w
                    LEFT JOIN word_distractors wd ON w.id = wd.word_id
                    WHERE w.id IN ({placeholders})
                """, word_ids)
                
                results = await cursor.fetchall()
                
                words_with_distractors = []
                for row in results:
                    word_data = {
                        'id': row[0],
                        'uzbek': row[1],
                        'translation': row[2],
                        'word_photo': row[3],
                        'distractors': []
                    }
                    
                    # Add distractors if they exist
                    if row[4] and row[5] and row[6]:
                        word_data['distractors'] = [row[4], row[5], row[6]]
                    
                    words_with_distractors.append(word_data)
                
                return words_with_distractors
                
        except Exception as e:
            logger.error(f"Error in get_words_with_distractors: {e}")
            return []

    async def update_word_distractors(self, word_id: int, distractor_1: str = None,
                                    distractor_2: str = None, distractor_3: str = None) -> bool:
        """
        Update specific distractors for a word
        
        Parameters:
        - word_id: int - Word ID (required)
        - distractor_1: str - New first distractor (optional)
        - distractor_2: str - New second distractor (optional)
        - distractor_3: str - New third distractor (optional)
        
        Returns:
        - Success: True
        - Failure: False
        
        Usage: success = await db.update_word_distractors(1, distractor_1="new_wrong_answer")
        """
        try:
            updates = []
            params = []
            
            if distractor_1 is not None:
                updates.append("distractor_1 = ?")
                params.append(distractor_1)
            if distractor_2 is not None:
                updates.append("distractor_2 = ?")
                params.append(distractor_2)
            if distractor_3 is not None:
                updates.append("distractor_3 = ?")
                params.append(distractor_3)
            
            if not updates:
                return True
                
            params.append(word_id)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f"""
                    UPDATE word_distractors SET {', '.join(updates)} WHERE word_id = ?
                """, params)
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error in update_word_distractors: {e}")
            return False

    async def generate_random_distractors(self, word_id: int, topic_id: int) -> bool:
        """
        Auto-generate 3 random distractors from other words in the same topic
        
        Parameters:
        - word_id: int - Target word ID
        - topic_id: int - Topic ID to select distractors from
        
        Returns:
        - Success: True
        - Failure: False (if not enough words in topic)
        
        Usage: success = await db.generate_random_distractors(1, 1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get other words from the same topic
                cursor = await db.execute("""
                    SELECT translation FROM words 
                    WHERE topic_id = ? AND id != ? 
                    ORDER BY RANDOM() LIMIT 3
                """, (topic_id, word_id))
                
                potential_distractors = await cursor.fetchall()
                
                if len(potential_distractors) < 3:
                    logger.warning(f"Not enough words in topic {topic_id} to generate distractors")
                    return False
                
                distractors = [d[0] for d in potential_distractors]
                
                # Create distractors
                await db.execute("""
                    INSERT OR REPLACE INTO word_distractors 
                    (word_id, distractor_1, distractor_2, distractor_3)
                    VALUES (?, ?, ?, ?)
                """, (word_id, distractors[0], distractors[1], distractors[2]))
                
                await db.commit()
                logger.info(f"Generated random distractors for word_id {word_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in generate_random_distractors: {e}")
            return False

    # ==================== LEARNING PARTS MANAGEMENT ====================
    
    async def create_learning_parts(self, topic_id: int, part_size: int = 15) -> bool:
        """
        Generate learning parts for a topic (pre-calculated word groups for optimization)
        
        Parameters:
        - topic_id: int - Topic ID (required)
        - part_size: int - Words per part (default: 15, range: 15-20)
        
        Returns:
        - Success: True
        - Failure: False
        
        Usage: success = await db.create_learning_parts(1, 20)
        """
        try:
            # Validate part_size
            if not 15 <= part_size <= 20:
                part_size = 15
                
            async with aiosqlite.connect(self.db_path) as db:
                # Get all words for this topic
                cursor = await db.execute("""
                    SELECT id FROM words WHERE topic_id = ? ORDER BY word_order
                """, (topic_id,))
                word_ids = [row[0] for row in await cursor.fetchall()]
                
                if not word_ids:
                    logger.warning(f"No words found for topic {topic_id}")
                    return False
                
                # Clear existing learning parts for this topic
                await db.execute("DELETE FROM learning_parts WHERE topic_id = ?", (topic_id,))
                
                # Create parts
                part_number = 1
                for i in range(0, len(word_ids), part_size):
                    part_word_ids = word_ids[i:i + part_size]
                    
                    await db.execute("""
                        INSERT INTO learning_parts (topic_id, part_number, part_size, word_ids)
                        VALUES (?, ?, ?, ?)
                    """, (topic_id, part_number, len(part_word_ids), json.dumps(part_word_ids)))
                    
                    part_number += 1
                
                await db.commit()
                logger.info(f"Created {part_number - 1} learning parts for topic {topic_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in create_learning_parts: {e}")
            return False

    async def get_learning_parts(self, topic_id: int) -> List[Dict]:
        """
        Get all learning parts for a topic
        
        Parameters:
        - topic_id: int - Topic ID
        
        Returns:
        - Success: [{'id': int, 'part_number': int, 'part_size': int, 'word_ids': [int]}]
        - Empty: []
        
        Usage: parts = await db.get_learning_parts(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, part_number, part_size, word_ids
                    FROM learning_parts WHERE topic_id = ? ORDER BY part_number
                """, (topic_id,))
                
                parts = await cursor.fetchall()
                
                return [
                    {
                        'id': part[0],
                        'part_number': part[1],
                        'part_size': part[2],
                        'word_ids': json.loads(part[3])
                    }
                    for part in parts
                ]
                
        except Exception as e:
            logger.error(f"Error in get_learning_parts: {e}")
            return []

    async def get_learning_part(self, topic_id: int, part_number: int) -> Optional[Dict]:
        """
        Get specific learning part
        
        Parameters:
        - topic_id: int - Topic ID
        - part_number: int - Part number (1, 2, 3, etc.)
        
        Returns:
        - Success: {'id': int, 'part_number': int, 'part_size': int, 'word_ids': [int]}
        - Not found: None
        
        Usage: part = await db.get_learning_part(1, 2)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, part_number, part_size, word_ids
                    FROM learning_parts WHERE topic_id = ? AND part_number = ?
                """, (topic_id, part_number))
                
                part = await cursor.fetchone()
                
                if part:
                    return {
                        'id': part[0],
                        'part_number': part[1],
                        'part_size': part[2],
                        'word_ids': json.loads(part[3])
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_learning_part: {e}")
            return None

    async def get_words_in_learning_part(self, topic_id: int, part_number: int) -> List[Dict]:
        """
        Get all words in a specific learning part with their data
        
        Parameters:
        - topic_id: int - Topic ID
        - part_number: int - Part number
        
        Returns:
        - Success: [{'id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str}]
        - Not found: []
        
        Usage: words = await db.get_words_in_learning_part(1, 2)
        """
        try:
            # Get learning part first
            part = await self.get_learning_part(topic_id, part_number)
            if not part:
                return []
            
            # Get words by IDs
            word_ids = part['word_ids']
            if not word_ids:
                return []
                
            async with aiosqlite.connect(self.db_path) as db:
                placeholders = ','.join('?' * len(word_ids))
                cursor = await db.execute(f"""
                    SELECT id, uzbek, translation, word_photo, note
                    FROM words WHERE id IN ({placeholders})
                    ORDER BY word_order
                """, word_ids)
                
                words = await cursor.fetchall()
                
                return [
                    {
                        'id': word[0],
                        'uzbek': word[1],
                        'translation': word[2],
                        'word_photo': word[3],
                        'note': word[4]
                    }
                    for word in words
                ]
                
        except Exception as e:
            logger.error(f"Error in get_words_in_learning_part: {e}")
            return []

    # ==================== BATTLE SESSION MANAGEMENT ====================
    
    async def create_battle_sessions_topic(self, topic_id: int, session_count: int = 10) -> bool:
        """
        Generate pre-calculated battle sessions for a topic (10 words each)
        
        Parameters:
        - topic_id: int - Topic ID (required)
        - session_count: int - Number of sessions to create (default: 10)
        
        Returns:
        - Success: True
        - Failure: False
        
        Usage: success = await db.create_battle_sessions_topic(1, 15)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get all words for this topic
                cursor = await db.execute("""
                    SELECT id FROM words WHERE topic_id = ? ORDER BY word_order
                """, (topic_id,))
                word_ids = [row[0] for row in await cursor.fetchall()]
                
                if len(word_ids) < 10:
                    logger.warning(f"Topic {topic_id} has less than 10 words, cannot create battle sessions")
                    return False
                
                # Clear existing battle sessions
                await db.execute("DELETE FROM battle_sessions_topic WHERE topic_id = ?", (topic_id,))
                
                # Create battle sessions
                for session_num in range(1, session_count + 1):
                    # Randomly select 10 words
                    session_words = random.sample(word_ids, 10)
                    
                    await db.execute("""
                        INSERT INTO battle_sessions_topic (topic_id, session_number, word_ids)
                        VALUES (?, ?, ?)
                    """, (topic_id, session_num, json.dumps(session_words)))
                
                await db.commit()
                logger.info(f"Created {session_count} battle sessions for topic {topic_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in create_battle_sessions_topic: {e}")
            return False

    async def create_battle_sessions_book(self, book_id: int, session_count: int = 10) -> bool:
        """
        Generate pre-calculated battle sessions for a book (10 words each from all topics)
        
        Parameters:
        - book_id: int - Book ID (required)
        - session_count: int - Number of sessions to create (default: 10)
        
        Returns:
        - Success: True
        - Failure: False
        
        Usage: success = await db.create_battle_sessions_book(1, 20)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get all words from all topics in this book
                cursor = await db.execute("""
                    SELECT w.id FROM words w
                    JOIN topics t ON w.topic_id = t.id
                    WHERE t.book_id = ?
                    ORDER BY t.topic_order, w.word_order
                """, (book_id,))
                word_ids = [row[0] for row in await cursor.fetchall()]
                
                if len(word_ids) < 10:
                    logger.warning(f"Book {book_id} has less than 10 words, cannot create battle sessions")
                    return False
                
                # Clear existing battle sessions
                await db.execute("DELETE FROM battle_sessions_book WHERE book_id = ?", (book_id,))
                
                # Create battle sessions
                for session_num in range(1, session_count + 1):
                    # Randomly select 10 words from the entire book
                    session_words = random.sample(word_ids, 10)
                    
                    await db.execute("""
                        INSERT INTO battle_sessions_book (book_id, session_number, word_ids)
                        VALUES (?, ?, ?)
                    """, (book_id, session_num, json.dumps(session_words)))
                
                await db.commit()
                logger.info(f"Created {session_count} battle sessions for book {book_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in create_battle_sessions_book: {e}")
            return False

    async def get_battle_session_topic(self, topic_id: int, session_number: int) -> Optional[Dict]:
        """
        Get specific topic battle session
        
        Parameters:
        - topic_id: int - Topic ID
        - session_number: int - Session number
        
        Returns:
        - Success: {'id': int, 'session_number': int, 'word_ids': [int]}
        - Not found: None
        
        Usage: session = await db.get_battle_session_topic(1, 3)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, session_number, word_ids
                    FROM battle_sessions_topic 
                    WHERE topic_id = ? AND session_number = ?
                """, (topic_id, session_number))
                
                session = await cursor.fetchone()
                
                if session:
                    return {
                        'id': session[0],
                        'session_number': session[1],
                        'word_ids': json.loads(session[2])
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_battle_session_topic: {e}")
            return None

    async def get_battle_session_book(self, book_id: int, session_number: int) -> Optional[Dict]:
        """
        Get specific book battle session
        
        Parameters:
        - book_id: int - Book ID
        - session_number: int - Session number
        
        Returns:
        - Success: {'id': int, 'session_number': int, 'word_ids': [int]}
        - Not found: None
        
        Usage: session = await db.get_battle_session_book(1, 5)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, session_number, word_ids
                    FROM battle_sessions_book 
                    WHERE book_id = ? AND session_number = ?
                """, (book_id, session_number))
                
                session = await cursor.fetchone()
                
                if session:
                    return {
                        'id': session[0],
                        'session_number': session[1],
                        'word_ids': json.loads(session[2])
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_battle_session_book: {e}")
            return None

    async def get_random_battle_session_topic(self, topic_id: int) -> Optional[Dict]:
        """
        Get random battle session from topic
        
        Parameters:
        - topic_id: int - Topic ID
        
        Returns:
        - Success: {'id': int, 'session_number': int, 'word_ids': [int]}
        - Not found: None
        
        Usage: session = await db.get_random_battle_session_topic(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, session_number, word_ids
                    FROM battle_sessions_topic 
                    WHERE topic_id = ? 
                    ORDER BY RANDOM() LIMIT 1
                """, (topic_id,))
                
                session = await cursor.fetchone()
                
                if session:
                    return {
                        'id': session[0],
                        'session_number': session[1],
                        'word_ids': json.loads(session[2])
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_random_battle_session_topic: {e}")
            return None

    async def get_random_battle_session_book(self, book_id: int) -> Optional[Dict]:
        """
        Get random battle session from book
        
        Parameters:
        - book_id: int - Book ID
        
        Returns:
        - Success: {'id': int, 'session_number': int, 'word_ids': [int]}
        - Not found: None
        
        Usage: session = await db.get_random_battle_session_book(1)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, session_number, word_ids
                    FROM battle_sessions_book 
                    WHERE book_id = ? 
                    ORDER BY RANDOM() LIMIT 1
                """, (book_id,))
                
                session = await cursor.fetchone()
                
                if session:
                    return {
                        'id': session[0],
                        'session_number': session[1],
                        'word_ids': json.loads(session[2])
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error in get_random_battle_session_book: {e}")
            return None

    # ==================== CLEANUP & OPTIMIZATION ====================
    
    async def cleanup_expired_battles(self) -> int:
        """
        Remove expired friend battles (older than 24 hours)
        
        Parameters: None
        
        Returns:
        - Success: int - Number of expired battles removed
        - Failure: 0
        
        Usage: removed_count = await db.cleanup_expired_battles()
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    DELETE FROM friend_battles 
                    WHERE expires_at < datetime('now')
                """)
                await db.commit()
                
                removed_count = cursor.rowcount
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} expired friend battles")
                return removed_count
                
        except Exception as e:
            logger.error(f"Error in cleanup_expired_battles: {e}")
            return 0

    async def regenerate_all_optimizations(self, book_id: int = None) -> bool:
        """
        Regenerate all optimization data (learning parts, battle sessions, distractors)
        
        Parameters:
        - book_id: int - Specific book ID (optional, None for all books)
        
        Returns:
        - Success: True
        - Failure: False
        
        Usage: success = await db.regenerate_all_optimizations()  # All books
        Usage: success = await db.regenerate_all_optimizations(1)  # Specific book
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if book_id:
                    # Get topics for specific book
                    cursor = await db.execute("SELECT id FROM topics WHERE book_id = ?", (book_id,))
                    topic_ids = [row[0] for row in await cursor.fetchall()]
                    book_ids = [book_id]
                else:
                    # Get all topics and books
                    cursor = await db.execute("SELECT id FROM topics")
                    topic_ids = [row[0] for row in await cursor.fetchall()]
                    cursor = await db.execute("SELECT id FROM books")
                    book_ids = [row[0] for row in await cursor.fetchall()]
                
                success_count = 0
                
                # Regenerate for each topic
                for topic_id in topic_ids:
                    # Create learning parts
                    if await self.create_learning_parts(topic_id):
                        success_count += 1
                    
                    # Create battle sessions for topic
                    if await self.create_battle_sessions_topic(topic_id):
                        success_count += 1
                    
                    # Generate distractors for all words in topic
                    cursor = await db.execute("SELECT id FROM words WHERE topic_id = ?", (topic_id,))
                    word_ids = [row[0] for row in await cursor.fetchall()]
                    
                    for word_id in word_ids:
                        await self.generate_random_distractors(word_id, topic_id)
                
                # Regenerate battle sessions for books
                for book_id_item in book_ids:
                    if await self.create_battle_sessions_book(book_id_item):
                        success_count += 1
                
                logger.info(f"Regenerated optimizations: {success_count} operations completed")
                return True
                
        except Exception as e:
            logger.error(f"Error in regenerate_all_optimizations: {e}")
            return False