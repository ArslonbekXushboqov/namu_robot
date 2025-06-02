import aiosqlite
import json
import random
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta

from .pending_requests import PendingRequestsDB
from .battle_session import BattleSessionDB
from .battle_history import BattleHistoryDB

logger = logging.getLogger(__name__)

class VocabularyBattleDB(PendingRequestsDB, BattleHistoryDB, BattleSessionDB):
    """Complete database manager for vocabulary battle bot"""

    def __init__(self, db_path: str = "vocabulary.db"):
        # Initialize all parent classes with the same db_path
        BattleSessionDB.__init__(self, db_path)
        PendingRequestsDB.__init__(self, db_path)
        BattleHistoryDB.__init__(self, db_path)
        self.db_path = db_path

    # ==================== DATABASE INITIALIZATION ====================
    
    async def init_database(self) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                print("dsgsdgsdg")
                await db.execute("PRAGMA foreign_keys = ON")

                
                # Create all tables
                await self._create_pending_requests_tables(db)
                await self._create_battle_session_tables(db)
                await self._create_battle_history(db)

                await self._create_indexes(db)
                
                # CRITICAL: Add this commit
                await db.commit()
                logger.info("Database initialized successfully.")
                return True

        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False

        #     # User learning progress
            # await db.execute("""
        #         CREATE TABLE IF NOT EXISTS user_learning_progress (
        #             id INTEGER PRIMARY KEY,
        #             user_id INTEGER NOT NULL,
        #             word_id INTEGER NOT NULL,
        #             correct_count INTEGER DEFAULT 0,
        #             total_attempts INTEGER DEFAULT 0,
        #             last_seen TIMESTAMP,
        #             mastery_level INTEGER DEFAULT 0,
        #             FOREIGN KEY (word_id) REFERENCES words(id),
        #             UNIQUE(user_id, word_id)
        #         )
        #     """)
        #     # User learning progress
            
        #     # User statistics for quick access
        #     await db.execute("""
        #         CREATE TABLE IF NOT EXISTS user_statistics (
        #             id INTEGER PRIMARY KEY,
        #             user_id INTEGER UNIQUE NOT NULL,
        #             total_battles INTEGER DEFAULT 0,
        #             total_wins INTEGER DEFAULT 0,
        #             total_losses INTEGER DEFAULT 0,
        #             total_draws INTEGER DEFAULT 0,
        #             best_score INTEGER DEFAULT 0,
        #             average_score REAL DEFAULT 0.0,
        #             words_learned INTEGER DEFAULT 0,
        #             current_streak INTEGER DEFAULT 0,
        #             longest_streak INTEGER DEFAULT 0,
        #             last_battle TIMESTAMP,
        #             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #         )
        #     """)

    async def _create_indexes(self, db):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_words_topic ON words(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_topics_book ON topics(book_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_parts_topic ON learning_parts(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_battle_sessions_topic ON battle_sessions_topic(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_battle_sessions_book ON battle_sessions_book(book_id)",
            # "CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_learning_progress(user_id)",
            # "CREATE INDEX IF NOT EXISTS idx_user_progress_word ON user_learning_progress(word_id)",
            # "CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_battle_history_players ON battle_history(player1_id, player2_id)",
            "CREATE INDEX IF NOT EXISTS idx_friend_battles_code ON friend_battles(battle_code)",
            "CREATE INDEX IF NOT EXISTS idx_pending_random_battle_config ON pending_random_requests(battle_config)",
            "CREATE INDEX IF NOT EXISTS idx_pending_random_player_id ON pending_random_requests(player_id)"
        ]
        
        for index in indexes:
            await db.execute(index)
        
            
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