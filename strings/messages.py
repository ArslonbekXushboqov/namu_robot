class Messages:
    # Welcome and main menu
    WELCOME = """
🎯 <b>Welcome to Vocabulary Battle Bot!</b>

Test your Uzbek-Korean vocabulary knowledge by battling with other users!

Choose an option below to get started:
"""

    MAIN_MENU = """
What would you like to do?
"""

    # Battle setup messages
    CHOOSE_BATTLE_TYPE = """
How would you like to battle?

🎲 <b>Random Opponent</b> - Get matched with another player
👥 <b>Battle with Friend</b> - Create a link to share with a friend
"""

    CHOOSE_BOOK = """
Choose which book you want to battle with:
"""

    CHOOSE_SCOPE = """
Do you want to battle with:

📚 <b>All Vocabularies</b> - Words from the entire book  
📝 <b>Specific Topic</b> - Words from one topic only
"""

    CHOOSE_TOPIC = """
Choose which topic you want to battle with:
"""

    # Battle states
    SEARCHING_OPPONENT = """
🔍 <b>Searching for opponent...</b>

Looking for another player with the same battle configuration.
This may take a moment.

⏰ You can cancel anytime by pressing /cancel
"""

    BATTLE_LINK_CREATED = """
🔗 <b>Battle Link Created!</b>

Share this link with your friend to start the battle:

{battle_link}

⏰ Link expires in 24 hours
"""

    BATTLE_STARTING = """
⚔️ <b>Battle Starting!</b>

🎯 <b>Battle Configuration:</b>

📖 Book: {book_title}  
📝 Scope: {scope}

❓ Questions: 10

{countdown_message}
"""

    BATTLE_QUESTION = """
❓ <i>Question {current}/{total}</i>

<b>{uzbek_word}</b>
"""

    CORRECT_ANSWER = "✅ Correct! (+1 point)"
    WRONG_ANSWER = "❌ Wrong! The correct answer was: {correct_answer}"

    BATTLE_COMPLETED = """
🏁 <b>Battle Completed!</b>

📊 <b>Final Results:</b>

👤 <b>{player1_name}</b>  
• Score: {player1_score}/10  
• Time: {player1_time}s

👤 <b>{player2_name}</b>  
• Score: {player2_score}/10  
• Time: {player2_time}s

🏆 <b>Winner: {winner_name}</b>

Great battle! 🎉
"""

    WAITING_FOR_OPPONENT = """
⏳ <b>Battle Completed!</b>

You finished the battle! Now waiting for your opponent to complete their questions.

📊 <b>Your Results:</b>  
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
🤖 <b>Battle Bot Commands:</b>

/start - Start the bot and go to main menu  
/cancel - Cancel current operation  
/stats - View your battle statistics  
/help - Show this help message

<b>How to Battle:</b>  
1. Press ⚔️ Battle button  
2. Choose random opponent or battle with friend  
3. Select book and topic  
4. Answer 10 questions as fast as possible  
5. See results and earn points!
"""

    # Battle type confirmation messages
    BATTLE_TYPE_SELECTED = "✅ Battle type: {battle_type}"
    BOOK_SELECTED = "✅ Selected book: {book_title}"
    SCOPE_SELECTED = "✅ Scope: {scope_display}"

    # Battle process messages
    COUNTDOWN_3 = "3"
    COUNTDOWN_2 = "2"
    COUNTDOWN_1 = "1"
    COUNTDOWN_GO = "GO! 🚀"
    GET_READY_MESSAGE = "Get ready! First question coming up..."

    # Scope display formats
    SCOPE_ALL_VOCABULARIES = "📚 All vocabularies from {book_title}"
    SCOPE_SPECIFIC_TOPIC = "📝 Topic: {topic_title}"

    # Generic error messages from callback handlers
    BATTLE_NOT_FOUND = "Battle not found!"
    BATTLE_ALREADY_COMPLETED = "You've already completed this battle!"
    ERROR_PROCESSING_ANSWER = "Error processing answer!"
    ERROR_OCCURRED = "Error occurred!"

    # Statistics messages
    STATS_TITLE = "📊 <b>Your Statistics</b>"
    NO_BATTLES_COMPLETED = """📊 <b>Your Statistics</b>

No battles completed yet.
Start your first battle to see stats!"""

    STATS_DISPLAY = """📊 <b>Your Statistics</b>

🎯 <b>Battles:</b> {total_battles}
🏆 <b>Wins:</b> {wins}
❌ <b>Losses:</b> {losses}
📈 <b>Win Rate:</b> {win_rate:.1f}%
⭐ <b>Average Score:</b> {average_score}/10
"""

    ERROR_FETCHING_STATS = "❌ Error fetching statistics."

    # Books viewing messages
    BOOKS_TITLE = "📚 <b>Available Books:</b> "
    NO_BOOKS_MESSAGE = "📚 No books available."
    BOOK_DISPLAY_FORMAT = "📖 <b>{book_title}</b>\n   • {topic_count} topics, {word_count} words"
    ERROR_FETCHING_BOOKS = "❌ Error fetching books."

    # Re-battle messages
    REBATTLE_REQUEST_TITLE = "🔄 <b>Re-battle Request!</b>"
    REBATTLE_REQUEST_MESSAGE = """🔄 <b>Re-battle Request!</b>

👤 <b>{requester_name}</b> wants a rematch!
🎯 <b>Battle:</b> {battle_info}

Do you accept the challenge?"""

    REBATTLE_REQUEST_SENT = """🔄 <b>Re-battle request sent!</b>

⏳ Waiting for <b>{opponent_name}</b> to respond...
🎯 <b>Battle:</b> {battle_info}"""

    REBATTLE_ACCEPTED = """✅ <b>Re-battle Accepted!</b>

🎯 <b>Battle:</b> {scope_display}
⚔️ <b>Opponent:</b> {opponent_name}

🚀 <b>Starting battle...</b>"""

    REBATTLE_DECLINED_OPPONENT = """❌ <b>Re-battle Declined</b>

You declined the re-battle request from <b>{requester_name}</b>."""

    REBATTLE_DECLINED_REQUESTER = """❌ <b>Re-battle Declined</b>

<b>{opponent_name}</b> declined your re-battle request."""

    REBATTLE_REQUEST_CANCELLED = """❌ <b>Re-battle Request Cancelled</b>

You cancelled your re-battle request."""

    REBATTLE_REQUEST_CANCELLED_NOTIFICATION = """❌ <b>Re-battle Request Cancelled</b>

<b>{requester_name}</b> cancelled their re-battle request."""

    REQUEST_EXPIRED = """❌ <b>Request Expired</b>

This re-battle request is no longer valid."""

    BATTLE_NOT_AVAILABLE = """❌ <b>Battle Not Available</b>

Unable to create battle session. Please try again later."""

    # Re-battle error messages
    INVALID_REQUEST = "❌ Invalid request!"
    REQUEST_EXPIRED_SHORT = "❌ Request expired or invalid!"
    UNABLE_TO_SEND_REQUEST = "❌ Unable to send request. User may have blocked the bot."
    ERROR_SENDING_REQUEST = "❌ Error sending request. Please try again."
    ERROR_PROCESSING_REQUEST = "❌ Error processing request!"
    ERROR_PROCESSING_ACCEPTANCE = "❌ Error processing acceptance!"
    ERROR_PROCESSING_DECLINE = "❌ Error processing decline!"
    ERROR_CANCELLING_REQUEST = "❌ Error cancelling request!"
    BATTLE_SESSION_NOT_AVAILABLE = "❌ Battle session not available!"

    # Re-battle success messages
    REBATTLE_REQUEST_SENT_SHORT = "✅ Re-battle request sent!"
    REBATTLE_STARTED = "✅ Re-battle started!"
    REBATTLE_DECLINED_SHORT = "❌ Re-battle declined"
    REQUEST_CANCELLED_SHORT = "✅ Request cancelled"

    # Battle info display formats
    BOOK_BATTLE_INFO = "📚 {book_title}"
    TOPIC_BATTLE_INFO = "📝 {topic_title}"
    BOOK_BATTLE_DEFAULT = "📚 Book Battle"
    TOPIC_BATTLE_DEFAULT = "📝 Topic Battle"

    # User fallback name
    DEFAULT_USER_NAME = "User"