from aiogram.fsm.state import State, StatesGroup

class BattleStates(StatesGroup):
    # Initial battle setup
    waiting_for_battle_type = State()  # random or friend
    waiting_for_book_selection = State()
    waiting_for_scope_selection = State()  # all vocabs or specific topic
    waiting_for_topic_selection = State()
    
    # Battle states
    waiting_for_opponent = State()
    sharing_battle_link = State()
    in_battle = State()
    battle_completed = State()
    waiting_for_opponent_completion = State()

class UserSession:
    """Store user's battle configuration during setup"""
    def __init__(self):
        self.battle_type: Optional[str] = None  # 'random' or 'friend'
        self.selected_book_id: Optional[int] = None
        self.selected_topic_id: Optional[int] = None
        self.battle_scope: Optional[str] = None  # 'book' or 'topic'
        self.current_battle_id: Optional[str] = None
        self.current_question_index: int = 0
        self.answers: list = []
        self.start_time: Optional[float] = None

# Global storage for user sessions (in production, consider Redis)
user_sessions: dict[int, UserSession] = {}

def get_user_session(user_id: int) -> UserSession:
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    return user_sessions[user_id]

def clear_user_session(user_id: int):
    """Clear user session"""
    if user_id in user_sessions:
        del user_sessions[user_id]