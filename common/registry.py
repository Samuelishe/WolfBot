from typing import Dict, Optional
from features.findgame.session import GameSession

# Хранилище сессий по chat_id
_sessions: Dict[int, GameSession] = {}


def create_session(chat_id: int, field_size: int, win_condition: int) -> GameSession:
    session = GameSession(chat_id, field_size, win_condition)
    _sessions[chat_id] = session
    return session


def get_session(chat_id: int) -> Optional[GameSession]:
    return _sessions.get(chat_id)


def remove_session(chat_id: int) -> None:
    _sessions.pop(chat_id, None)


def has_session(chat_id: int) -> bool:
    return chat_id in _sessions