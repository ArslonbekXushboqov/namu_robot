

    # # ==================== CLEANUP & OPTIMIZATION ====================
    
    # async def cleanup_expired_battles(self) -> int:
    #     """
    #     Remove expired friend battles (older than 24 hours)
        
    #     Parameters: None
        
    #     Returns:
    #     - Success: int - Number of expired battles removed
    #     - Failure: 0
        
    #     Usage: removed_count = await db.cleanup_expired_battles()
    #     """
    #     try:
    #         async with aiosqlite.connect(self.db_path) as db:
    #             cursor = await db.execute("""
    #                 DELETE FROM friend_battles 
    #                 WHERE expires_at < datetime('now')
    #             """)
    #             await db.commit()
                
    #             removed_count = cursor.rowcount
    #             if removed_count > 0:
    #                 logger.info(f"Cleaned up {removed_count} expired friend battles")
    #             return removed_count
                
    #     except Exception as e:
    #         logger.error(f"Error in cleanup_expired_battles: {e}")
    #         return 0

    # async def regenerate_all_optimizations(self, book_id: int = None) -> bool:
    #     """
    #     Regenerate all optimization data (learning parts, battle sessions, distractors)
        
    #     Parameters:
    #     - book_id: int - Specific book ID (optional, None for all books)
        
    #     Returns:
    #     - Success: True
    #     - Failure: False
        
    #     Usage: success = await db.regenerate_all_optimizations()  # All books
    #     Usage: success = await db.regenerate_all_optimizations(1)  # Specific book
    #     """
    #     try:
    #         async with aiosqlite.connect(self.db_path) as db:
    #             if book_id:
    #                 # Get topics for specific book
    #                 cursor = await db.execute("SELECT id FROM topics WHERE book_id = ?", (book_id,))
    #                 topic_ids = [row[0] for row in await cursor.fetchall()]
    #                 book_ids = [book_id]
    #             else:
    #                 # Get all topics and books
    #                 cursor = await db.execute("SELECT id FROM topics")
    #                 topic_ids = [row[0] for row in await cursor.fetchall()]
    #                 cursor = await db.execute("SELECT id FROM books")
    #                 book_ids = [row[0] for row in await cursor.fetchall()]
                
    #             success_count = 0
                
    #             # Regenerate for each topic
    #             for topic_id in topic_ids:
    #                 # Create learning parts
    #                 if await self.create_learning_parts(topic_id):
    #                     success_count += 1
                    
    #                 # Create battle sessions for topic
    #                 if await self.create_battle_sessions_topic(topic_id):
    #                     success_count += 1
                    
    #                 # Generate distractors for all words in topic
    #                 cursor = await db.execute("SELECT id FROM words WHERE topic_id = ?", (topic_id,))
    #                 word_ids = [row[0] for row in await cursor.fetchall()]
                    
    #                 for word_id in word_ids:
    #                     await self.generate_random_distractors(word_id, topic_id)
                
    #             # Regenerate battle sessions for books
    #             for book_id_item in book_ids:
    #                 if await self.create_battle_sessions_book(book_id_item):
    #                     success_count += 1
                
    #             logger.info(f"Regenerated optimizations: {success_count} operations completed")
    #             return True
                
    #     except Exception as e:
    #         logger.error(f"Error in regenerate_all_optimizations: {e}")
    #         return False