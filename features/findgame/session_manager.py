from typing import Dict, Optional
from .session import GameSession

_sessions: Dict[int, GameSession] = {}


def get_session(chat_id: int) -> Optional[GameSession]:
    return _sessions.get(chat_id)


def set_session(chat_id: int, session: GameSession) -> None:
    _sessions[chat_id] = session


def del_session(chat_id: int) -> None:
    _sessions.pop(chat_id, None)


def has_session(chat_id: int) -> bool:
    return chat_id in _sessions