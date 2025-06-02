    # # ==================== LEARNING PARTS MANAGEMENT ====================
    
    # async def create_learning_parts(self, topic_id: int, part_size: int = 15) -> bool:
    #     """
    #     Generate learning parts for a topic (pre-calculated word groups for optimization)
        
    #     Parameters:
    #     - topic_id: int - Topic ID (required)
    #     - part_size: int - Words per part (default: 15, range: 15-20)
        
    #     Returns:
    #     - Success: True
    #     - Failure: False
        
    #     Usage: success = await db.create_learning_parts(1, 20)
    #     """
    #     try:
    #         # Validate part_size
    #         if not 15 <= part_size <= 20:
    #             part_size = 15
                
    #         async with aiosqlite.connect(self.db_path) as db:
    #             # Get all words for this topic
    #             cursor = await db.execute("""
    #                 SELECT id FROM words WHERE topic_id = ? ORDER BY word_order
    #             """, (topic_id,))
    #             word_ids = [row[0] for row in await cursor.fetchall()]
                
    #             if not word_ids:
    #                 logger.warning(f"No words found for topic {topic_id}")
    #                 return False
                
    #             # Clear existing learning parts for this topic
    #             await db.execute("DELETE FROM learning_parts WHERE topic_id = ?", (topic_id,))
                
    #             # Create parts
    #             part_number = 1
    #             for i in range(0, len(word_ids), part_size):
    #                 part_word_ids = word_ids[i:i + part_size]
                    
    #                 await db.execute("""
    #                     INSERT INTO learning_parts (topic_id, part_number, part_size, word_ids)
    #                     VALUES (?, ?, ?, ?)
    #                 """, (topic_id, part_number, len(part_word_ids), json.dumps(part_word_ids)))
                    
    #                 part_number += 1
                
    #             await db.commit()
    #             logger.info(f"Created {part_number - 1} learning parts for topic {topic_id}")
    #             return True
                
    #     except Exception as e:
    #         logger.error(f"Error in create_learning_parts: {e}")
    #         return False

    # async def get_learning_parts(self, topic_id: int) -> List[Dict]:
    #     """
    #     Get all learning parts for a topic
        
    #     Parameters:
    #     - topic_id: int - Topic ID
        
    #     Returns:
    #     - Success: [{'id': int, 'part_number': int, 'part_size': int, 'word_ids': [int]}]
    #     - Empty: []
        
    #     Usage: parts = await db.get_learning_parts(1)
    #     """
    #     try:
    #         async with aiosqlite.connect(self.db_path) as db:
    #             cursor = await db.execute("""
    #                 SELECT id, part_number, part_size, word_ids
    #                 FROM learning_parts WHERE topic_id = ? ORDER BY part_number
    #             """, (topic_id,))
                
    #             parts = await cursor.fetchall()
                
    #             return [
    #                 {
    #                     'id': part[0],
    #                     'part_number': part[1],
    #                     'part_size': part[2],
    #                     'word_ids': json.loads(part[3])
    #                 }
    #                 for part in parts
    #             ]
                
    #     except Exception as e:
    #         logger.error(f"Error in get_learning_parts: {e}")
    #         return []

    # async def get_learning_part(self, topic_id: int, part_number: int) -> Optional[Dict]:
    #     """
    #     Get specific learning part
        
    #     Parameters:
    #     - topic_id: int - Topic ID
    #     - part_number: int - Part number (1, 2, 3, etc.)
        
    #     Returns:
    #     - Success: {'id': int, 'part_number': int, 'part_size': int, 'word_ids': [int]}
    #     - Not found: None
        
    #     Usage: part = await db.get_learning_part(1, 2)
    #     """
    #     try:
    #         async with aiosqlite.connect(self.db_path) as db:
    #             cursor = await db.execute("""
    #                 SELECT id, part_number, part_size, word_ids
    #                 FROM learning_parts WHERE topic_id = ? AND part_number = ?
    #             """, (topic_id, part_number))
                
    #             part = await cursor.fetchone()
                
    #             if part:
    #                 return {
    #                     'id': part[0],
    #                     'part_number': part[1],
    #                     'part_size': part[2],
    #                     'word_ids': json.loads(part[3])
    #                 }
    #             return None
                
    #     except Exception as e:
    #         logger.error(f"Error in get_learning_part: {e}")
    #         return None

    # async def get_words_in_learning_part(self, topic_id: int, part_number: int) -> List[Dict]:
    #     """
    #     Get all words in a specific learning part with their data
        
    #     Parameters:
    #     - topic_id: int - Topic ID
    #     - part_number: int - Part number
        
    #     Returns:
    #     - Success: [{'id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str}]
    #     - Not found: []
        
    #     Usage: words = await db.get_words_in_learning_part(1, 2)
    #     """
    #     try:
    #         # Get learning part first
    #         part = await self.get_learning_part(topic_id, part_number)
    #         if not part:
    #             return []
            
    #         # Get words by IDs
    #         word_ids = part['word_ids']
    #         if not word_ids:
    #             return []
                
    #         async with aiosqlite.connect(self.db_path) as db:
    #             placeholders = ','.join('?' * len(word_ids))
    #             cursor = await db.execute(f"""
    #                 SELECT id, uzbek, translation, word_photo, note
    #                 FROM words WHERE id IN ({placeholders})
    #                 ORDER BY word_order
    #             """, word_ids)
                
    #             words = await cursor.fetchall()
                
    #             return [
    #                 {
    #                     'id': word[0],
    #                     'uzbek': word[1],
    #                     'translation': word[2],
    #                     'word_photo': word[3],
    #                     'note': word[4]
    #                 }
    #                 for word in words
    #             ]
                
    #     except Exception as e:
    #         logger.error(f"Error in get_words_in_learning_part: {e}")
    #         return []
