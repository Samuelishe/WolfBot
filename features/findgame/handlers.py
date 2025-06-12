from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from .config import (DEFAULT_FIELD_SIZE,
                     MIN_FIELD_SIZE,
                     MAX_FIELD_SIZE,
                     DEFAULT_WIN_CONDITION,
                     MIN_ITEMS_PER_FIELD,
                     MAX_ITEMS_PER_FIELD)
from .session import GameSession
from features.findgame.logic import start_turn_timer
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

    sent_msg = await msg.answer(
        f"🔍 Старт игры!\nПоле: {field_size}×{field_size}\n"
        f"Победа при {win_condition} находках",
        reply_markup=build_field_keyboard(field_size)
    )

    session.field_message_id = sent_msg.message_id

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

def build_control_keyboard(session: GameSession, user_id: int) -> InlineKeyboardMarkup:
    buttons = []

    if session.started:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏳️ Сдаться", callback_data="fg:giveup")]
        ])

    if user_id not in [p.user_id for p in session.players]:
        buttons.append([InlineKeyboardButton(text="👤 Присоединиться", callback_data="fg:join")])
    else:
        buttons.append([InlineKeyboardButton(text="❌ Покинуть", callback_data="fg:leave")])
        if user_id == session.players[0].user_id and len(session.players) >= 2:
            buttons.append([InlineKeyboardButton(text="▶️ Начать", callback_data="fg:start")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.in_({"fg:join", "fg:leave", "fg:start", "fg:giveup"}))
async def handle_control_buttons(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    username = callback.from_user.username or "Игрок"

    session = get_session(chat_id)
    if not session:
        await callback.answer("❌ Игра не найдена.")
        return

    if callback.data == "fg:join":
        if session.add_player(user_id, username):
            await callback.answer("✅ Ты присоединился к игре.")
        else:
            await callback.answer("⚠️ Ты уже в игре!")

    elif callback.data == "fg:leave":
        if any(p.user_id == user_id for p in session.players):
            session.remove_player(user_id)
            await callback.answer("🚪 Ты покинул игру.")
        else:
            await callback.answer("❌ Ты не участвуешь в игре.")

    elif callback.data == "fg:start":
        if session.players[0].user_id != user_id:
            await callback.answer("❌ Только инициатор может начать игру.")
            return
        if len(session.players) < 2:
            await callback.answer("⚠️ Нужно минимум 2 игрока.")
            return
        session.started = True
        session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
        await callback.message.edit_text(
            f"🎮 Игра началась!\nХод первого игрока: {session.get_current_player().username}",
            reply_markup=build_field_keyboard(session.field_size)
        )
        await callback.answer("🚀 Поехали!")
        await start_turn_timer(callback.bot, session)

    elif callback.data == "fg:giveup":
        if not session.started:
            await callback.answer("❌ Игра ещё не началась.")
            return

        player = next((p for p in session.players if p.user_id == user_id), None)
        if not player:
            await callback.answer("❌ Ты не участвуешь.")
            return

        session.remove_player(user_id)
        await callback.message.answer(f"🏳️ Игрок {player.username} сдался и выбыл из игры.")

        if len(session.players) == 1:
            winner = session.players[0]
            await callback.message.answer(f"🏆 Победил {winner.username}, все остальные выбыли!")
            # del_session(chat_id)  # опционально
        elif session.get_current_player().user_id == user_id:
            session.advance_turn()
            await start_turn_timer(callback.bot, session)
            await callback.message.answer(f"🔁 Ход переходит к {session.get_current_player().username}")

        session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
        new_markup = build_field_keyboard(session.field_size)
        await callback.message.edit_reply_markup(reply_markup=new_markup)
        await callback.answer("😢 Ты сдался.")

    # Кнопки управления обновлять не нужно, если уже началась
    if not session.started:
        control_markup = build_control_keyboard(session, user_id)
        await callback.message.edit_reply_markup(reply_markup=control_markup)


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
        await start_turn_timer(callback.bot, session)
        await callback.message.answer(f"🔁 Ход переходит к {session.get_current_player().username}")

    # Перегенерируем поле (всегда!)
    session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
    new_markup = build_field_keyboard(session.field_size)
    await callback.message.edit_reply_markup(reply_markup=new_markup)

    await callback.answer()  # чтобы убрать "часики"

