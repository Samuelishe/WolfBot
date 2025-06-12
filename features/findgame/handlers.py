from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from .config import (DEFAULT_FIELD_SIZE,
                     MIN_FIELD_SIZE,
                     MAX_FIELD_SIZE,
                     DEFAULT_WIN_CONDITION,
                     MIN_ITEMS_PER_FIELD,
                     MAX_ITEMS_PER_FIELD)
from common.registry import create_session, get_session, has_session
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command(commands=["findgame", "fg", "findgame3", "findgame4", "findgame5", "findgame6"]))
async def handle_findgame(msg: Message, command: CommandObject):
    if command is None:
        await msg.answer("❌ Не удалось обработать команду.")
        return
    cmd = command.command
    args = command.args

    # Определим размер поля
    if cmd.startswith("findgame") and cmd != "findgame":
        try:
            field_size = int(cmd.replace("findgame", ""))
        except ValueError:
            field_size = DEFAULT_FIELD_SIZE
    else:
        field_size = DEFAULT_FIELD_SIZE

    # Переопределим по аргументу, если передан
    if args:
        try:
            tokens = list(map(int, args.strip().split()))
            if len(tokens) >= 1:
                field_size = tokens[0]
            if len(tokens) >= 2:
                win_condition = tokens[1]
            else:
                win_condition = DEFAULT_WIN_CONDITION
        except ValueError:
            field_size = DEFAULT_FIELD_SIZE
            win_condition = DEFAULT_WIN_CONDITION
    else:
        win_condition = DEFAULT_WIN_CONDITION

    # Ограничим размер поля
    field_size = max(MIN_FIELD_SIZE, min(MAX_FIELD_SIZE, field_size))

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    username = msg.from_user.username

    if has_session(chat_id):
        await msg.answer("⚠️ Игра уже запущена в этом чате!")
        return

    session = create_session(chat_id, field_size, win_condition)
    session.add_player(user_id, username)

    await msg.answer(
        f"🔍 Старт игры!\nПоле: {field_size}×{field_size}\n"
        f"Победа при {win_condition} находках",
        reply_markup=build_field_keyboard(field_size)
    )

def build_field_keyboard(field_size: int) -> InlineKeyboardMarkup:
    keyboard = []
    for y in range(field_size):
        row = []
        for x in range(field_size):
            btn = InlineKeyboardButton(
                text="⬜",  # закрытая клетка
                callback_data=f"fg:{x}:{y}"
            )
            row.append(btn)
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data.startswith("fg:"))
async def handle_click(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    session = get_session(chat_id)
    if not session:
        await callback.answer("❌ Игра ещё не началась!", show_alert=True)
        return

    player = session.get_current_player()
    if not player or player.user_id != user_id:
        await callback.answer("⏳ Сейчас не твой ход!", show_alert=False)
        return

    # Получим координаты
    try:
        _, x_str, y_str = callback.data.split(":")
        x, y = int(x_str), int(y_str)
    except ValueError:
        await callback.answer("❌ Некорректные данные!", show_alert=True)
        return

    result = session.click_cell(x, y)

    if result == "found":
        await callback.message.answer(f"✅ {player.username} нашёл предмет!")
    elif result == "special":
        await callback.message.answer(f"🌟 {player.username} нашёл **особый предмет** и ПОБЕДИЛ!")
    else:
        await callback.message.answer(f"❌ {player.username} промахнулся.")

    winner = session.check_win()
    if winner:
        await callback.message.answer(f"🏆 Победил {winner.username} с {winner.score} очками!")
        # Сессия закончена — можно удалить или сбросить
        # del_session(chat_id)  # если будет реализована

    else:
        session.advance_turn()
        await callback.message.answer(f"🔁 Ход переходит к {session.get_current_player().username}")

    # Перегенерируем поле (всегда!)
    session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
    new_markup = build_field_keyboard(session.field_size)
    await callback.message.edit_reply_markup(reply_markup=new_markup)

    await callback.answer()  # чтобы убрать "часики"