import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

class BattleHistoryDB:
    def __init__(self, db_path: str):  # Removed logger parameter
        self.db_path = db_path
    
    async def _create_battle_history(self, db):
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battle_history (
                id INTEGER PRIMARY KEY,
                battle_code TEXT UNIQUE NOT NULL,
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

        self.logger.info("Battle history database initialized with indexes")
    
    def generate_battle_code(self) -> str:
        """Generate a unique battle code"""
        return int(time.time() * 1000)  # battle ID

    
    async def create_battle(self, session_id: int, session_type: str, 
                          player1_id: int, player2_id: int) -> str:
        """Create a new battle entry"""
        battle_code = self.generate_battle_code()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO battle_history 
                    (battle_code, session_id, session_type, player1_id, player2_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (battle_code, session_id, session_type, player1_id, player2_id))
                
                await db.commit()
                self.logger.info(f"Battle created: {battle_code}")
                return battle_code
                
        except Exception as e:
            self.logger.error(f"Error creating battle: {e}")
            raise
    
    async def update_battle_result(self, battle_code: str, winner_id: Optional[int],
                                 player1_score: int, player2_score: int) -> bool:
        """Update battle with final results"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    UPDATE battle_history 
                    SET winner_id = ?, player1_score = ?, player2_score = ?,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE battle_code = ?
                """, (winner_id, player1_score, player2_score, battle_code))
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Battle {battle_code} updated with results")
                    return True
                else:
                    self.logger.warning(f"Battle {battle_code} not found for update")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error updating battle {battle_code}: {e}")
            raise
    
    async def get_battle_by_code(self, battle_code: str) -> Optional[Dict[str, Any]]:
        """Get battle details by battle code"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM battle_history WHERE battle_code = ?
                """, (battle_code,))
                
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting battle {battle_code}: {e}")
            raise
    
    async def get_player_battles(self, player_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all battles for a specific player"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM battle_history 
                    WHERE player1_id = ? OR player2_id = ?
                    ORDER BY completed_at DESC
                    LIMIT ?
                """, (player_id, player_id, limit))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting battles for player {player_id}: {e}")
            raise
    
    async def get_session_battles(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all battles for a specific session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM battle_history 
                    WHERE session_id = ?
                    ORDER BY completed_at DESC
                """, (session_id,))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting battles for session {session_id}: {e}")
            raise
    
    async def get_player_stats(self, player_id: int) -> Dict[str, Any]:
        """Get comprehensive stats for a player"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Total battles
                cursor = await db.execute("""
                    SELECT COUNT(*) as total_battles
                    FROM battle_history 
                    WHERE (player1_id = ? OR player2_id = ?) AND winner_id IS NOT NULL
                """, (player_id, player_id))
                total_battles = (await cursor.fetchone())[0]
                
                # Wins
                cursor = await db.execute("""
                    SELECT COUNT(*) as wins
                    FROM battle_history 
                    WHERE winner_id = ?
                """, (player_id,))
                wins = (await cursor.fetchone())[0]
                
                # Average scores
                cursor = await db.execute("""
                    SELECT 
                        AVG(CASE WHEN player1_id = ? THEN player1_score ELSE player2_score END) as avg_score,
                        AVG(CASE WHEN player1_id = ? THEN player2_score ELSE player1_score END) as avg_opponent_score
                    FROM battle_history 
                    WHERE (player1_id = ? OR player2_id = ?) AND winner_id IS NOT NULL
                """, (player_id, player_id, player_id, player_id))
                scores = await cursor.fetchone()
                
                win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
                
                return {
                    'player_id': player_id,
                    'total_battles': total_battles,
                    'wins': wins,
                    'losses': total_battles - wins,
                    'win_rate': round(win_rate, 2),
                    'average_score': round(scores[0] or 0, 2),
                    'average_opponent_score': round(scores[1] or 0, 2)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting stats for player {player_id}: {e}")
            raise
    
    async def get_recent_battles(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent battles across all sessions"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM battle_history 
                    ORDER BY completed_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting recent battles: {e}")
            raise
    
    async def delete_battle(self, battle_code: str) -> bool:
        """Delete a battle by battle code"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    DELETE FROM battle_history WHERE battle_code = ?
                """, (battle_code,))
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Battle {battle_code} deleted")
                    return True
                else:
                    self.logger.warning(f"Battle {battle_code} not found for deletion")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting battle {battle_code}: {e}")
            raise
    
    async def get_head_to_head(self, player1_id: int, player2_id: int) -> Dict[str, Any]:
        """Get head-to-head statistics between two players"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM battle_history 
                    WHERE ((player1_id = ? AND player2_id = ?) 
                           OR (player1_id = ? AND player2_id = ?))
                    AND winner_id IS NOT NULL
                    ORDER BY completed_at DESC
                """, (player1_id, player2_id, player2_id, player1_id))
                
                battles = [dict(row) for row in await cursor.fetchall()]
                
                player1_wins = sum(1 for b in battles if b['winner_id'] == player1_id)
                player2_wins = sum(1 for b in battles if b['winner_id'] == player2_id)
                
                return {
                    'player1_id': player1_id,
                    'player2_id': player2_id,
                    'total_battles': len(battles),
                    'player1_wins': player1_wins,
                    'player2_wins': player2_wins,
                    'battles': battles
                }
                
        except Exception as e:
            self.logger.error(f"Error getting head-to-head for players {player1_id} vs {player2_id}: {e}")
            raise