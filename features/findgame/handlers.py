from random import randint

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from .config import (DEFAULT_FIELD_SIZE,
                     MIN_FIELD_SIZE,
                     MAX_FIELD_SIZE,
                     DEFAULT_WIN_CONDITION,
                     MIN_ITEMS_PER_FIELD,
                     MAX_ITEMS_PER_FIELD,
                     EMOJI_CLOSED,
                     EMOJI_EMPTY,
                     EMOJI_ITEM,
                     EMOJI_SPECIAL)
from .session import GameSession
from .session_manager import get_session, set_session, del_session, has_session
from features.findgame.logic import start_turn_timer
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


router = Router()

@router.message(Command(commands=["findgame", "fg", "findgame3", "findgame4", "findgame5", "findgame6"]))
async def handle_findgame(msg: Message, command: CommandObject):
    if command is None:
        await msg.answer("❌ Не удалось обработать команду.")
        return

    cmd = command.command
    args = command.args

    # Значения по умолчанию
    field_size = DEFAULT_FIELD_SIZE
    win_condition = DEFAULT_WIN_CONDITION

    # Попытка определить из команды (например, /findgame5)
    if cmd.startswith("findgame") and cmd != "findgame":
        try:
            field_size = int(cmd.replace("findgame", ""))
        except ValueError:
            pass

    # Попытка переопределить аргументами
    if args:
        try:
            tokens = list(map(int, args.strip().split()))
            if len(tokens) >= 1:
                field_size = tokens[0]
            if len(tokens) >= 2:
                win_condition = tokens[1]
        except ValueError:
            pass

    # Ограничим размер поля
    field_size = max(MIN_FIELD_SIZE, min(MAX_FIELD_SIZE, field_size))

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    username = msg.from_user.username

    if has_session(chat_id):
        await msg.answer("⚠️ Игра уже запущена в этом чате!")
        return

    session = GameSession(chat_id, field_size, win_condition)
    set_session(chat_id, session)
    session.add_player(user_id, username)

    sent_msg = await msg.answer(
        f"🔍 Старт игры!\nПоле: {field_size}×{field_size}\n"
        f"Победа при {win_condition} находках",
        reply_markup=build_field_keyboard(session)
    )

    session.field_message_id = sent_msg.message_id

def build_field_keyboard(session: GameSession) -> InlineKeyboardMarkup:
    keyboard = []

    for y in range(session.field_size):
        row = []
        for x in range(session.field_size):
            if (x, y) not in session.opened_cells:
                emoji = EMOJI_CLOSED
                callback_data = f"fg:{x}:{y}"
            else:
                cell = session.grid[y][x]
                if cell == "item":
                    emoji = EMOJI_ITEM
                elif cell == "special":
                    emoji = EMOJI_SPECIAL
                else:
                    emoji = EMOJI_EMPTY
                callback_data = "fg:noop"  # нажимать нельзя

            row.append(InlineKeyboardButton(
                text=emoji,
                callback_data=callback_data
            ))
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
    username = callback.from_user.username or callback.from_user.full_name or "Игрок"

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

        #Бросок кубиков
        dice_rolls = {}
        used_totals = set()

        for player in session.players:
            while True:
                dice1 = randint(1, 6)
                dice2 = randint(1, 6)
                total = dice1 + dice2
                if total not in used_totals:
                    used_totals.add(total)
                    dice_rolls[player.user_id] = (total, dice1, dice2)
                    break

        # Сортировка игроков по сумме бросков (по убыванию)
        session.players.sort(key=lambda p: dice_rolls[p.user_id][0], reverse=True)

        # Сообщение с бросками
        roll_messages = []
        for player in session.players:
            _, d1, d2 = dice_rolls[player.user_id]
            roll_text = f"{player.display_name}: {dice_emoji(d1)}{dice_emoji(d2)}"
            roll_messages.append(roll_text)

        await callback.message.answer("🎲 Результаты бросков:\n" + "\n".join(roll_messages))

        #Генерация поля
        session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
        await callback.message.edit_text(
            f"🎮 Игра началась!\nХод первого игрока: {session.get_current_player().username}",
            new_markup = build_field_keyboard(session)
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
        await callback.message.answer(f"🏳️ Игрок {player.display_name} сдался и выбыл из игры.")

        if len(session.players) == 1:
            winner = session.players[0]
            await callback.message.answer(f"🏆 Победил {winner.username}, все остальные выбыли!")
            del_session(chat_id)

        elif session.get_current_player().user_id == user_id:
            session.advance_turn()
            await start_turn_timer(callback.bot, session)
            await callback.message.answer(f"🔁 Ход переходит к {session.get_current_player().username}")

        session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
        new_markup = build_field_keyboard(session)
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
        await callback.answer("⏳ Сейчас не твой ход!", show_alert=True)
        return

    if callback.data == "fg:noop":
        await callback.answer()
        return

    # Получим координаты
    try:
        _, x_str, y_str = callback.data.split(":")
        x, y = int(x_str), int(y_str)
    except ValueError:
        await callback.answer("❌ Некорректные данные!", show_alert=True)
        return

    result = session.click_cell(x, y)
    if result == "already_opened":
        await callback.answer("⛔ Эта клетка уже открыта!", show_alert=True)
        return
    if result == "found":
        await callback.message.answer(f"✅ {player.display_name} нашёл предмет!")
    elif result == "special":
        await callback.message.answer(f"🌟 {player.display_name} нашёл **особый предмет** и ПОБЕДИЛ!")
    else:
        await callback.message.answer(f"❌ {player.display_name} промахнулся.")

    winner = session.check_win()
    if winner:
        await callback.message.answer(f"🏆 Победил {winner.username} с {winner.score} очками!")
        del_session(chat_id)

    else:
        session.advance_turn()
        await start_turn_timer(callback.bot, session)
        await callback.message.answer(f"🔁 Ход переходит к {session.get_current_player().username}")

    # Перегенерируем поле (всегда!)
    session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
    new_markup = build_field_keyboard(session)
    await callback.message.edit_reply_markup(reply_markup=new_markup)

    await callback.answer()  # чтобы убрать "часики"

def dice_emoji(value: int) -> str:
    return {
        1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
    }.get(value, "?")