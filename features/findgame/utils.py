from aiogram.types import InlineKeyboardMarkup


def are_markups_different(m1: InlineKeyboardMarkup, m2: InlineKeyboardMarkup) -> bool:
    if m1 is None or m2 is None:
        return True
    return m1.model_dump() != m2.model_dump()

def dice_emoji(value: int) -> str:
    return {
        1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
    }.get(value, "?")