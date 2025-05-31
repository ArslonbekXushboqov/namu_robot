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