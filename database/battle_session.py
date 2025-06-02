import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import random

logger = logging.getLogger(__name__)

class BattleSessionDB:
    def __init__(self, db_path: str):  # Removed logger parameter
        self.db_path = db_path
    
    async def _create_battle_session_tables(self, db):
        """Create battle session tables - to be called from main init_database"""
        # Battle sessions for topics
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battle_sessions_topic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                word_ids TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id),
                UNIQUE(topic_id, session_number)
            )
        """)
        
        # Battle sessions for books
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battle_sessions_book (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                word_ids TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id),
                UNIQUE(book_id, session_number)
            )
        """)
        
        logger.info("Battle session tables created")

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