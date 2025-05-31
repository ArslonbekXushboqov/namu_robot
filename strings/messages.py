class Messages:
    # Welcome and main menu
    WELCOME = """
🎯 Welcome to Vocabulary Battle Bot!

Test your Uzbek vocabulary knowledge by battling with other users!

Choose an option below to get started:
"""
    
    MAIN_MENU = """
🏠 Main Menu

What would you like to do?
"""
    
    # Battle setup messages
    CHOOSE_BATTLE_TYPE = """
⚔️ Battle Setup

How would you like to battle?

🎲 **Random Opponent** - Get matched with another player
👥 **Battle with Friend** - Create a link to share with a friend
"""
    
    CHOOSE_BOOK = """
📚 Select Book

Choose which book you want to battle with:
"""
    
    CHOOSE_SCOPE = """
🎯 Battle Scope

Do you want to battle with:

📚 **All Vocabularies** - Words from the entire book
📝 **Specific Topic** - Words from one topic only
"""
    
    CHOOSE_TOPIC = """
📝 Select Topic

Choose which topic you want to battle with:
"""
    
    # Battle states
    SEARCHING_OPPONENT = """
🔍 Searching for opponent...

Looking for another player with the same battle configuration.
This may take a moment.

⏰ You can cancel anytime by pressing /cancel
"""
    
    BATTLE_LINK_CREATED = """
🔗 Battle Link Created!

Share this link with your friend to start the battle:

{battle_link}

⏰ Link expires in 24 hours
"""
    
    BATTLE_STARTING = """
⚔️ Battle Starting!

🎯 **Battle Configuration:**
📖 Book: {book_title}
📝 Scope: {scope}
❓ Questions: 10

👥 **Opponents:**
• {player1_name}
• {player2_name}

Get ready! First question coming up...
"""
    
    BATTLE_QUESTION = """
❓ **Question {current}/{total}**

**Uzbek word:** `{uzbek_word}`

Choose the correct translation:
"""
    
    CORRECT_ANSWER = "✅ Correct! (+1 point)"
    WRONG_ANSWER = "❌ Wrong! The correct answer was: {correct_answer}"
    
    BATTLE_COMPLETED = """
🏁 **Battle Completed!**

📊 **Final Results:**

👤 **{player1_name}**
• Score: {player1_score}/10
• Time: {player1_time}s

👤 **{player2_name}**
• Score: {player2_score}/10  
• Time: {player2_time}s

🏆 **Winner: {winner_name}**

Great battle! 🎉
"""
    
    WAITING_FOR_OPPONENT = """
⏳ **Battle Completed!**

You finished the battle! Now waiting for your opponent to complete their questions.

📊 **Your Results:**
• Score: {your_score}/10
• Time: {your_time}s

You'll get the final results when your opponent finishes.
"""
    
    # Error messages
    NO_BOOKS_AVAILABLE = "❌ No books available at the moment."
    NO_TOPICS_AVAILABLE = "❌ No topics available for this book."
    BATTLE_SESSION_ERROR = "❌ Error creating battle session. Please try again."
    DATABASE_ERROR = "❌ Database error occurred. Please try again later."
    
    # Commands
    HELP_MESSAGE = """
🤖 **Battle Bot Commands:**

/start - Start the bot and go to main menu
/cancel - Cancel current operation
/stats - View your battle statistics
/help - Show this help message

**How to Battle:**
1. Press ⚔️ Battle button
2. Choose random opponent or battle with friend
3. Select book and topic
4. Answer 10 questions as fast as possible
5. See results and earn points!
"""