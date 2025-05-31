# VOCABULARY BATTLE BOT - PART 2 DEVELOPER GUIDE
## Complete Function Reference for Vocabulary Data Management

---

## 📚 BOOK MANAGEMENT FUNCTIONS

### `create_book(title, description=None)`
**Purpose:** Create a new vocabulary book in the database

**Parameters:**
- `title` (str, required) - The book title
- `description` (str, optional) - Book description, can be None

**Returns:**
- **Success:** `dict` with keys: `{'id': int, 'title': str, 'description': str, 'total_words': int, 'created_at': str}`
- **Failure:** `None`

**Usage Example:**
```python
# Create book with description
book = await db.create_book("English Basics", "Beginner level vocabulary")
# Returns: {'id': 1, 'title': 'English Basics', 'description': 'Beginner level vocabulary', 'total_words': 0, 'created_at': '2025-01-15 10:30:00'}

# Create book without description
book = await db.create_book("Advanced English")
# Returns: {'id': 2, 'title': 'Advanced English', 'description': None, 'total_words': 0, 'created_at': '2025-01-15 10:31:00'}
```

---

### `get_all_books()`
**Purpose:** Retrieve all books with their statistics

**Parameters:** None

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'title': str, 'description': str, 'total_words': int, 'topic_count': int, 'created_at': str}`
- **Empty database:** `[]` (empty list)

**Usage Example:**
```python
books = await db.get_all_books()
# Returns: [
#   {'id': 1, 'title': 'English Basics', 'description': 'Beginner level', 'total_words': 150, 'topic_count': 5, 'created_at': '2025-01-15 10:30:00'},
#   {'id': 2, 'title': 'Advanced English', 'description': None, 'total_words': 200, 'topic_count': 3, 'created_at': '2025-01-15 10:31:00'}
# ]
```

---

### `get_book_by_id(book_id)`
**Purpose:** Get specific book details by ID

**Parameters:**
- `book_id` (int, required) - The book ID to retrieve

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'title': str, 'description': str, 'total_words': int, 'topic_count': int, 'created_at': str}`
- **Not found:** `None`

**Usage Example:**
```python
book = await db.get_book_by_id(1)
# Returns: {'id': 1, 'title': 'English Basics', 'description': 'Beginner level', 'total_words': 150, 'topic_count': 5, 'created_at': '2025-01-15 10:30:00'}

invalid_book = await db.get_book_by_id(999)
# Returns: None
```

---

### `update_book_word_count(book_id)`
**Purpose:** Recalculate and update the total word count for a book

**Parameters:**
- `book_id` (int, required) - The book ID to update

**Returns:**
- **Success:** `True`
- **Failure:** `False`

**Usage Example:**
```python
success = await db.update_book_word_count(1)
# Returns: True (if book exists and update succeeds)
# Returns: False (if book doesn't exist or database error)
```

---

## 📖 TOPIC MANAGEMENT FUNCTIONS

### `create_topic(book_id, title, topic_order)`
**Purpose:** Create a new topic within a book

**Parameters:**
- `book_id` (int, required) - Parent book ID (must exist)
- `title` (str, required) - Topic title
- `topic_order` (int, required) - Order within book (1-10)

**Returns:**
- **Success:** `dict` with keys: `{'id': int, 'book_id': int, 'title': str, 'topic_order': int, 'word_count': int}`
- **Failure:** `None` (if book doesn't exist or topic_order conflicts)

**Usage Example:**
```python
topic = await db.create_topic(1, "Daily Activities", 1)
# Returns: {'id': 1, 'book_id': 1, 'title': 'Daily Activities', 'topic_order': 1, 'word_count': 0}

# This will fail if topic_order 1 already exists for book_id 1
duplicate = await db.create_topic(1, "Another Topic", 1)
# Returns: None
```

---

### `get_topics_by_book(book_id)`
**Purpose:** Get all topics for a specific book, ordered by topic_order

**Parameters:**
- `book_id` (int, required) - The book ID

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'book_id': int, 'title': str, 'topic_order': int, 'word_count': int}`
- **Empty/Not found:** `[]` (empty list)

**Usage Example:**
```python
topics = await db.get_topics_by_book(1)
# Returns: [
#   {'id': 1, 'book_id': 1, 'title': 'Daily Activities', 'topic_order': 1, 'word_count': 25},
#   {'id': 2, 'book_id': 1, 'title': 'Food & Cooking', 'topic_order': 2, 'word_count': 30}
# ]
```

---

### `get_topic_by_id(topic_id)`
**Purpose:** Get specific topic details by ID

**Parameters:**
- `topic_id` (int, required) - The topic ID to retrieve

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'book_id': int, 'title': str, 'topic_order': int, 'word_count': int}`
- **Not found:** `None`

**Usage Example:**
```python
topic = await db.get_topic_by_id(1)
# Returns: {'id': 1, 'book_id': 1, 'title': 'Daily Activities', 'topic_order': 1, 'word_count': 25}

invalid_topic = await db.get_topic_by_id(999)
# Returns: None
```

---

### `update_topic_word_count(topic_id)`
**Purpose:** Recalculate and update the word count for a topic

**Parameters:**
- `topic_id` (int, required) - The topic ID to update

**Returns:**
- **Success:** `True`
- **Failure:** `False`

**Usage Example:**
```python
success = await db.update_topic_word_count(1)
# Returns: True (if topic exists and update succeeds)
# Returns: False (if topic doesn't exist or database error)
```

---

## 📝 WORD MANAGEMENT FUNCTIONS

### `create_word(topic_id, uzbek, translation, word_photo=None, note=None, word_order=None, difficulty_level=1)`
**Purpose:** Create a new word in a topic

**Parameters:**
- `topic_id` (int, required) - Parent topic ID (must exist)
- `uzbek` (str, required) - Uzbek word
- `translation` (str, required) - English translation
- `word_photo` (str, optional) - Photo URL/path, can be None
- `note` (str, optional) - Additional notes, can be None
- `word_order` (int, optional) - Order within topic, auto-assigned if None
- `difficulty_level` (int, optional) - Difficulty 1-5, defaults to 1

**Returns:**
- **Success:** `dict` with keys: `{'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}`
- **Failure:** `None`

**Usage Example:**
```python
# Full word creation
word = await db.create_word(1, "kitob", "book", "photos/book.jpg", "Used for reading", 1, 2)
# Returns: {'id': 1, 'topic_id': 1, 'uzbek': 'kitob', 'translation': 'book', 'word_photo': 'photos/book.jpg', 'note': 'Used for reading', 'word_order': 1, 'difficulty_level': 2}

# Minimal word creation (auto word_order, default difficulty)
word = await db.create_word(1, "qalam", "pen")
# Returns: {'id': 2, 'topic_id': 1, 'uzbek': 'qalam', 'translation': 'pen', 'word_photo': None, 'note': None, 'word_order': 2, 'difficulty_level': 1}
```

---

### `get_words_by_topic(topic_id, limit=None)`
**Purpose:** Get all words for a specific topic, ordered by word_order

**Parameters:**
- `topic_id` (int, required) - The topic ID
- `limit` (int, optional) - Maximum number of words to return, None for all

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}`
- **Empty/Not found:** `[]` (empty list)

**Usage Example:**
```python
# Get all words
words = await db.get_words_by_topic(1)
# Returns: [
#   {'id': 1, 'topic_id': 1, 'uzbek': 'kitob', 'translation': 'book', 'word_photo': 'photos/book.jpg', 'note': 'Used for reading', 'word_order': 1, 'difficulty_level': 2},
#   {'id': 2, 'topic_id': 1, 'uzbek': 'qalam', 'translation': 'pen', 'word_photo': None, 'note': None, 'word_order': 2, 'difficulty_level': 1}
# ]

# Get limited words
words = await db.get_words_by_topic(1, limit=5)
# Returns: First 5 words only
```

---

### `get_word_by_id(word_id)`
**Purpose:** Get specific word details by ID

**Parameters:**
- `word_id` (int, required) - The word ID to retrieve

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}`
- **Not found:** `None`

**Usage Example:**
```python
word = await db.get_word_by_id(1)
# Returns: {'id': 1, 'topic_id': 1, 'uzbek': 'kitob', 'translation': 'book', 'word_photo': 'photos/book.jpg', 'note': 'Used for reading', 'word_order': 1, 'difficulty_level': 2}

invalid_word = await db.get_word_by_id(999)
# Returns: None
```

---

### `get_words_by_ids(word_ids)`
**Purpose:** Get multiple words by their IDs (batch operation, useful for battle sessions)

**Parameters:**
- `word_ids` (list, required) - List of word IDs to retrieve

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'topic_id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str, 'word_order': int, 'difficulty_level': int}`
- **Empty input/Not found:** `[]` (empty list)

**Usage Example:**
```python
words = await db.get_words_by_ids([1, 2, 5, 10])
# Returns: [
#   {'id': 1, 'topic_id': 1, 'uzbek': 'kitob', 'translation': 'book', ...},
#   {'id': 2, 'topic_id': 1, 'uzbek': 'qalam', 'translation': 'pen', ...},
#   {'id': 5, 'topic_id': 2, 'uzbek': 'non', 'translation': 'bread', ...},
#   {'id': 10, 'topic_id': 2, 'uzbek': 'suv', 'translation': 'water', ...}
# ]

empty_result = await db.get_words_by_ids([])
# Returns: []
```

---

### `update_word(word_id, **kwargs)`
**Purpose:** Update any word fields

**Parameters:**
- `word_id` (int, required) - The word ID to update
- `**kwargs` (optional) - Any combination of: `uzbek`, `translation`, `word_photo`, `note`, `word_order`, `difficulty_level`

**Returns:**
- **Success:** `True`
- **Failure:** `False` (if word doesn't exist or invalid fields)

**Usage Example:**
```python
# Update multiple fields
success = await db.update_word(1, translation="new translation", difficulty_level=3, note="updated note")
# Returns: True

# Update single field
success = await db.update_word(1, uzbek="yangi so'z")
# Returns: True

# No changes
success = await db.update_word(1)
# Returns: True (no-op)

# Invalid field ignored
success = await db.update_word(1, invalid_field="value", translation="valid")
# Returns: True (only valid fields updated)
```

---

### `delete_word(word_id)`
**Purpose:** Delete a word and clean up all related data

**Parameters:**
- `word_id` (int, required) - The word ID to delete

**Returns:**
- **Success:** `True`
- **Failure:** `False` (if word doesn't exist)

**Usage Example:**
```python
success = await db.delete_word(1)
# Returns: True (word deleted, distractors removed, progress data cleaned, topic count updated)

invalid_delete = await db.delete_word(999)
# Returns: False
```

---

## 🔄 AUTOMATIC OPERATIONS

**Note:** These functions automatically trigger when needed:
- `update_topic_word_count()` is called automatically when creating/deleting words
- `update_book_word_count()` should be called after bulk operations
- Word ordering is auto-assigned if not specified in `create_word()`

## ⚠️ IMPORTANT CONSIDERATIONS

1. **Foreign Key Constraints:** Make sure parent records exist before creating child records
2. **Unique Constraints:** `topic_order` must be unique within each book
3. **Batch Operations:** Use `get_words_by_ids()` for better performance when fetching multiple words
4. **Error Handling:** All functions return `None` or `False` on failure, check return values
5. **Data Integrity:** Deleting words cleans up related data automatically


# VOCABULARY BATTLE BOT - PART 3 DEVELOPER GUIDE
## Complete Function Reference for Battle System & Optimization

---

## 🎯 DISTRACTOR MANAGEMENT FUNCTIONS

### `create_word_distractors(word_id, distractor_1, distractor_2, distractor_3)`
**Purpose:** Store 3 wrong answers for a word (for quiz multiple choice)

**Parameters:**
- `word_id` (int, required) - Word ID (must exist in database)
- `distractor_1` (str, required) - First wrong answer
- `distractor_2` (str, required) - Second wrong answer  
- `distractor_3` (str, required) - Third wrong answer

**Returns:**
- **Success:** `True`
- **Failure:** `False` (if word doesn't exist or database error)

**Usage Example:**
```python
# Create distractors for word ID 1
success = await db.create_word_distractors(1, "cat", "dog", "bird")
# Returns: True (if word exists and distractors are created)

# This will fail if word_id doesn't exist
failed = await db.create_word_distractors(999, "wrong1", "wrong2", "wrong3")
# Returns: False
```

---

### `get_word_distractors(word_id)`
**Purpose:** Get distractors for a specific word

**Parameters:**
- `word_id` (int, required) - Word ID to get distractors for

**Returns:**
- **Found:** `dict` with keys: `{'word_id': int, 'distractor_1': str, 'distractor_2': str, 'distractor_3': str}`
- **Not found:** `None`

**Usage Example:**
```python
distractors = await db.get_word_distractors(1)
# Returns: {'word_id': 1, 'distractor_1': 'cat', 'distractor_2': 'dog', 'distractor_3': 'bird'}

no_distractors = await db.get_word_distractors(999)
# Returns: None
```

---

### `get_words_with_distractors(word_ids)`
**Purpose:** Batch get words with their distractors (optimized for battle sessions)

**Parameters:**
- `word_ids` (list, required) - List of word IDs

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'distractors': ['dist1', 'dist2', 'dist3']}`
- **Empty input/Not found:** `[]` (empty list)

**Usage Example:**
```python
battle_words = await db.get_words_with_distractors([1, 2, 3, 4, 5])
# Returns: [
#   {'id': 1, 'uzbek': 'kitob', 'translation': 'book', 'word_photo': 'book.jpg', 'distractors': ['cat', 'dog', 'bird']},
#   {'id': 2, 'uzbek': 'qalam', 'translation': 'pen', 'word_photo': None, 'distractors': ['house', 'tree', 'car']},
#   {'id': 3, 'uzbek': 'stol', 'translation': 'table', 'word_photo': 'table.jpg', 'distractors': []}  # No distractors yet
# ]

empty_result = await db.get_words_with_distractors([])
# Returns: []
```

---

### `update_word_distractors(word_id, distractor_1=None, distractor_2=None, distractor_3=None)`
**Purpose:** Update specific distractors for a word

**Parameters:**
- `word_id` (int, required) - Word ID (must exist)
- `distractor_1` (str, optional) - New first distractor
- `distractor_2` (str, optional) - New second distractor
- `distractor_3` (str, optional) - New third distractor

**Returns:**
- **Success:** `True`
- **Failure:** `False`

**Usage Example:**
```python
# Update only first distractor
success = await db.update_word_distractors(1, distractor_1="new_wrong_answer")
# Returns: True

# Update multiple distractors
success = await db.update_word_distractors(1, distractor_1="cat", distractor_3="fish")
# Returns: True (distractor_2 remains unchanged)

# No changes (all parameters None)
success = await db.update_word_distractors(1)
# Returns: True (no-op)
```

---

### `generate_random_distractors(word_id, topic_id)`
**Purpose:** Auto-generate 3 random distractors from other words in the same topic

**Parameters:**
- `word_id` (int, required) - Target word ID
- `topic_id` (int, required) - Topic ID to select distractors from

**Returns:**
- **Success:** `True`
- **Failure:** `False` (if not enough words in topic)

**Usage Example:**
```python
success = await db.generate_random_distractors(1, 1)
# Returns: True (if topic has at least 3 other words)

# This will fail if topic doesn't have enough words
failed = await db.generate_random_distractors(1, 2)  # Topic 2 has only 2 words
# Returns: False
```

---

## 📚 LEARNING PARTS MANAGEMENT FUNCTIONS

### `create_learning_parts(topic_id, part_size=15)`
**Purpose:** Generate learning parts for a topic (pre-calculated word groups for optimization)

**Parameters:**
- `topic_id` (int, required) - Topic ID (must exist)
- `part_size` (int, optional) - Words per part (default: 15, range: 15-20)

**Returns:**
- **Success:** `True`
- **Failure:** `False`

**Usage Example:**
```python
# Create parts with default size (15 words)
success = await db.create_learning_parts(1)
# Returns: True (creates parts of 15 words each)

# Create parts with custom size
success = await db.create_learning_parts(1, 20)
# Returns: True (creates parts of 20 words each)

# Invalid part_size gets corrected to 15
success = await db.create_learning_parts(1, 25)  # Too large
# Returns: True (uses 15 instead of 25)
```

---

### `get_learning_parts(topic_id)`
**Purpose:** Get all learning parts for a topic

**Parameters:**
- `topic_id` (int, required) - Topic ID

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'part_number': int, 'part_size': int, 'word_ids': [int]}`
- **Empty/Not found:** `[]` (empty list)

**Usage Example:**
```python
parts = await db.get_learning_parts(1)
# Returns: [
#   {'id': 1, 'part_number': 1, 'part_size': 15, 'word_ids': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]},
#   {'id': 2, 'part_number': 2, 'part_size': 15, 'word_ids': [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]},
#   {'id': 3, 'part_number': 3, 'part_size': 10, 'word_ids': [31, 32, 33, 34, 35, 36, 37, 38, 39, 40]}  # Last part smaller
# ]
```

---

### `get_learning_part(topic_id, part_number)`
**Purpose:** Get specific learning part

**Parameters:**
- `topic_id` (int, required) - Topic ID
- `part_number` (int, required) - Part number (1, 2, 3, etc.)

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'part_number': int, 'part_size': int, 'word_ids': [int]}`
- **Not found:** `None`

**Usage Example:**
```python
part = await db.get_learning_part(1, 2)
# Returns: {'id': 2, 'part_number': 2, 'part_size': 15, 'word_ids': [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]}

invalid_part = await db.get_learning_part(1, 999)
# Returns: None
```

---

### `get_words_in_learning_part(topic_id, part_number)`
**Purpose:** Get all words in a specific learning part with their data

**Parameters:**
- `topic_id` (int, required) - Topic ID
- `part_number` (int, required) - Part number

**Returns:**
- **Success:** `list` of dicts, each with keys: `{'id': int, 'uzbek': str, 'translation': str, 'word_photo': str, 'note': str}`
- **Not found:** `[]` (empty list)

**Usage Example:**
```python
words = await db.get_words_in_learning_part(1, 2)
# Returns: [
#   {'id': 16, 'uzbek': 'uy', 'translation': 'house', 'word_photo': 'house.jpg', 'note': 'Building where people live'},
#   {'id': 17, 'uzbek': 'daraxt', 'translation': 'tree', 'word_photo': None, 'note': None},
#   ... (13 more words)
# ]

no_words = await db.get_words_in_learning_part(1, 999)
# Returns: []
```

---

## ⚔️ BATTLE SESSION MANAGEMENT FUNCTIONS

### `create_battle_sessions_topic(topic_id, session_count=10)`
**Purpose:** Generate pre-calculated battle sessions for a topic (10 words each)

**Parameters:**
- `topic_id` (int, required) - Topic ID (must exist)
- `session_count` (int, optional) - Number of sessions to create (default: 10)

**Returns:**
- **Success:** `True`
- **Failure:** `False` (if topic has less than 10 words)

**Usage Example:**
```python
# Create default 10 sessions
success = await db.create_battle_sessions_topic(1)
# Returns: True (creates 10 sessions with 10 random words each)

# Create custom number of sessions
success = await db.create_battle_sessions_topic(1, 15)
# Returns: True (creates 15 sessions)

# This will fail if topic has less than 10 words
failed = await db.create_battle_sessions_topic(2)  # Topic 2 has only 5 words
# Returns: False
```

---

### `create_battle_sessions_book(book_id, session_count=10)`
**Purpose:** Generate pre-calculated battle sessions for a book (10 words each from all topics)

**Parameters:**
- `book_id` (int, required) - Book ID (must exist)
- `session_count` (int, optional) - Number of sessions to create (default: 10)

**Returns:**
- **Success:** `True`
- **Failure:** `False` (if book has less than 10 total words)

**Usage Example:**
```python
# Create default 10 sessions for entire book
success = await db.create_battle_sessions_book(1)
# Returns: True (creates 10 sessions with 10 random words from all topics in book)

# Create custom number of sessions
success = await db.create_battle_sessions_book(1, 20)
# Returns: True (creates 20 sessions)

# This will fail if book has less than 10 total words
failed = await db.create_battle_sessions_book(2)
# Returns: False
```

---

### `get_battle_session_topic(topic_id, session_number)`
**Purpose:** Get specific topic battle session

**Parameters:**
- `topic_id` (int, required) - Topic ID
- `session_number` (int, required) - Session number

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'session_number': int, 'word_ids': [int]}`
- **Not found:** `None`

**Usage Example:**
```python
session = await db.get_battle_session_topic(1, 3)
# Returns: {'id': 3, 'session_number': 3, 'word_ids': [5, 12, 18, 23, 31, 7, 14, 26, 33, 9]}

invalid_session = await db.get_battle_session_topic(1, 999)
# Returns: None
```

---

### `get_battle_session_book(book_id, session_number)`
**Purpose:** Get specific book battle session

**Parameters:**
- `book_id` (int, required) - Book ID
- `session_number` (int, required) - Session number

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'session_number': int, 'word_ids': [int]}`
- **Not found:** `None`

**Usage Example:**
```python
session = await db.get_battle_session_book(1, 5)
# Returns: {'id': 5, 'session_number': 5, 'word_ids': [3, 17, 22, 8, 29, 11, 35, 19, 6, 24]}

invalid_session = await db.get_battle_session_book(1, 999)
# Returns: None
```

---

### `get_random_battle_session_topic(topic_id)`
**Purpose:** Get random battle session from topic

**Parameters:**
- `topic_id` (int, required) - Topic ID

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'session_number': int, 'word_ids': [int]}`
- **Not found:** `None`

**Usage Example:**
```python
session = await db.get_random_battle_session_topic(1)
# Returns: {'id': 7, 'session_number': 7, 'word_ids': [15, 3, 28, 11, 33, 8, 21, 36, 14, 25]}
# Note: Different session each time due to randomness

no_sessions = await db.get_random_battle_session_topic(999)
# Returns: None
```

---

### `get_random_battle_session_book(book_id)`
**Purpose:** Get random battle session from book

**Parameters:**
- `book_id` (int, required) - Book ID

**Returns:**
- **Found:** `dict` with keys: `{'id': int, 'session_number': int, 'word_ids': [int]}`
- **Not found:** `None`

**Usage Example:**
```python
session = await db.get_random_battle_session_book(1)
# Returns: {'id': 2, 'session_number': 2, 'word_ids': [9, 31, 16, 4, 27, 12, 38, 21, 5, 33]}
# Note: Different session each time due to randomness

no_sessions = await db.get_random_battle_session_book(999)
# Returns: None
```

---

## 🧹 CLEANUP & OPTIMIZATION FUNCTIONS

### `cleanup_expired_battles()`
**Purpose:** Remove expired friend battles (older than 24 hours)

**Parameters:** None

**Returns:**
- **Success:** `int` - Number of expired battles removed
- **Failure:** `0`

**Usage Example:**
```python
removed_count = await db.cleanup_expired_battles()
# Returns: 5 (if 5 expired battles were removed)
# Returns: 0 (if no expired battles or error occurred)
```

---

### `regenerate_all_optimizations(book_id=None)`
**Purpose:** Regenerate all optimization data (learning parts, battle sessions, distractors)

**Parameters:**
- `book_id` (int, optional) - Specific book ID (None for all books)

**Returns:**
- **Success:** `True`
- **Failure:** `False`

**Usage Example:**
```python
# Regenerate optimizations for all books
success = await db.regenerate_all_optimizations()
# Returns: True (regenerates learning parts, battle sessions, and distractors for all books)

# Regenerate optimizations for specific book
success = await db.regenerate_all_optimizations(1)
# Returns: True (regenerates only for book ID 1)

# Database error
failed = await db.regenerate_all_optimizations()
# Returns: False
```

---

## 🔄 AUTOMATIC OPERATIONS & WORKFLOW

### **Typical Battle Setup Workflow:**
```python
# 1. Create distractors for all words in a topic
topic_words = await db.get_words_by_topic(1)
for word in topic_words:
    await db.generate_random_distractors(word['id'], 1)

# 2. Create learning parts for structured learning
await db.create_learning_parts(1, 15)

# 3. Create battle sessions for quick battles
await db.create_battle_sessions_topic(1, 10)
await db.create_battle_sessions_book(1, 10)

# 4. Get battle-ready data
session = await db.get_random_battle_session_topic(1)
battle_words = await db.get_words_with_distractors(session['word_ids'])
```

### **Optimization Maintenance:**
```python
# Regular cleanup (run daily)
removed = await db.cleanup_expired_battles()

# Full regeneration (run when content changes significantly)
success = await db.regenerate_all_optimizations()
```

---

## ⚠️ IMPORTANT CONSIDERATIONS

1. **Pre-calculation Strategy:** Battle sessions and learning parts are pre-calculated for performance. Regenerate when content changes significantly.

2. **Distractor Requirements:** Each word needs exactly 3 distractors for proper quiz functionality. Use `generate_random_distractors()` for automatic generation.

3. **Minimum Data Requirements:**
   - Topics need ≥4 words for distractor generation (1 target + 3 distractors)
   - Topics need ≥10 words for battle session creation
   - Books need ≥10 total words for book-level battle sessions

4. **Performance Optimization:**
   - Use `get_words_with_distractors()` for batch word retrieval in battles
   - Battle sessions are pre-calculated to avoid real-time random selection
   - Learning parts group words for efficient study sessions

5. **Data Consistency:**
   - `regenerate_all_optimizations()` clears and rebuilds all optimization data
   - Distractor generation uses random selection from the same topic
   - Battle sessions contain exactly 10 words each

6. **Error Handling:** All functions return `False`/`None`/`0` on failure. Always check return values and have fallback strategies.

7. **Memory Considerations:** JSON arrays are stored as strings in the database and parsed when retrieved. Handle JSON parsing errors appropriately.