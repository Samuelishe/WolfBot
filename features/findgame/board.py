from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .session import GameSession
from .config import EMOJI_CLOSED, EMOJI_EMPTY, EMOJI_ITEM, EMOJI_SPECIAL

def build_field_keyboard(session: GameSession) -> InlineKeyboardMarkup:
    keyboard = []

    for y in range(session.field_size):
        row = []
        for x in range(session.field_size):
            coord = (x, y)

            if coord in session.opened_cells:
                if coord == session.special_position:
                    emoji = EMOJI_SPECIAL
                elif coord in session.item_positions:
                    emoji = EMOJI_ITEM
                else:
                    emoji = EMOJI_EMPTY
                callback_data = "fg:noop"  # нельзя нажимать
            else:
                emoji = EMOJI_CLOSED
                callback_data = f"fg:{x}:{y}"

            row.append(InlineKeyboardButton(
                text=emoji,
                callback_data=callback_data
            ))
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)