import aiosqlite
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PendingRequestsDB:
    def __init__(self, db_path: str):  # Removed logger parameter
        self.db_path = db_path
    
    async def _create_pending_requests_tables(self, db):
        """Create pending requests table - to be called from main init_database"""
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pending_random_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL UNIQUE,
                message_id INTEGER NOT NULL,
                battle_config TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Pending requests table created")

    async def add_pending_request(self, player_id: int, message_id: int, battle_config: str) -> bool:
        """
        Add a new pending request. If player already has a request, delete the old one first.
        Returns True if successfully added, False otherwise.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # First, delete any existing request from this player
                await db.execute(
                    "DELETE FROM pending_random_requests WHERE player_id = ?",
                    (player_id,)
                )
                
                # Insert the new request
                await db.execute('''
                    INSERT INTO pending_random_requests (player_id, message_id, battle_config, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (player_id, message_id, battle_config, datetime.now().isoformat()))
                
                await db.commit()
                logger.info(f"Added pending request for player {player_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding pending request for player {player_id}: {e}")
            return False
    
    async def get_random_opponent(self, requesting_player_id: int, battle_config: str) -> Optional[Tuple[int, int, int, str]]:
        """
        Get a random opponent with matching battle_config (excluding the requesting player).
        Returns tuple (id, player_id, message_id, battle_config) or None if no opponents found.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT id, player_id, message_id, battle_config 
                    FROM pending_random_requests 
                    WHERE battle_config = ? AND player_id != ? 
                    ORDER BY RANDOM() 
                    LIMIT 1
                ''', (battle_config, requesting_player_id))
                
                result = await cursor.fetchone()
                if result:
                    logger.info(f"Found opponent {result[1]} for player {requesting_player_id} with config {battle_config}")
                    return result
                else:
                    logger.info(f"No opponents found for player {requesting_player_id} with config {battle_config}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error getting random opponent for player {requesting_player_id}: {e}")
            return False
    
    async def remove_pending_request(self, player1_id: int, player2_id: int = None) -> bool:
        """
        Remove pending request(s). 
        If player2_id is provided, removes both players (when matched).
        If only player1_id provided, removes single player.
        Returns True if successfully removed, False otherwise.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if player2_id is not None:
                    # Remove both players (when matched)
                    cursor = await db.execute(
                        "DELETE FROM pending_random_requests WHERE player_id IN (?, ?)",
                        (player1_id, player2_id)
                    )
                    await db.commit()
                    
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info(f"Removed pending requests for matched players {player1_id} and {player2_id} (deleted {deleted_count} records)")
                        return True
                    else:
                        logger.info(f"No pending requests found for players {player1_id} and {player2_id}")
                        return False
                else:
                    # Remove single player
                    cursor = await db.execute(
                        "DELETE FROM pending_random_requests WHERE player_id = ?",
                        (player1_id,)
                    )
                    await db.commit()
                    
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info(f"Removed pending request for player {player1_id}")
                        return True
                    else:
                        logger.info(f"No pending request found for player {player1_id}")
                        return False
                    
        except Exception as e:
            logger.error(f"Error removing pending request(s): {e}")
            return False
            
    async def remove_pending_request_by_id(self, request_id: int) -> bool:
        """
        Remove a pending request by its ID.
        Returns True if successfully removed, False otherwise.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM pending_random_requests WHERE id = ?",
                    (request_id,)
                )
                await db.commit()
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    logger.info(f"Removed pending request with ID {request_id}")
                    return True
                else:
                    logger.info(f"No pending request found with ID {request_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing pending request with ID {request_id}: {e}")
            return False
    
    async def get_pending_request_by_player(self, player_id: int) -> Optional[Tuple[int, int, int, str, str]]:
        """
        Get a specific player's pending request.
        Returns tuple (id, player_id, message_id, battle_config, timestamp) or None.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT id, player_id, message_id, battle_config, timestamp 
                    FROM pending_random_requests 
                    WHERE player_id = ?
                ''', (player_id,))
                
                result = await cursor.fetchone()
                if result:
                    logger.info(f"Found pending request for player {player_id}")
                    return result
                else:
                    logger.info(f"No pending request found for player {player_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting pending request for player {player_id}: {e}")
            return None
    
    async def get_all_pending_requests(self) -> List[Tuple[int, int, int, str, str]]:
        """
        Get all pending requests.
        Returns list of tuples (id, player_id, message_id, battle_config, timestamp).
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT id, player_id, message_id, battle_config, timestamp 
                    FROM pending_random_requests 
                    ORDER BY timestamp DESC
                ''')
                
                results = await cursor.fetchall()
                logger.info(f"Retrieved {len(results)} pending requests")
                return results
                
        except Exception as e:
            logger.error(f"Error getting all pending requests: {e}")
            return []
    
    async def clear_all_pending_requests(self) -> bool:
        """
        Clear all pending requests (useful for maintenance).
        Returns True if successful, False otherwise.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM pending_random_requests")
                await db.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleared {deleted_count} pending requests")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing all pending requests: {e}")
            return False
