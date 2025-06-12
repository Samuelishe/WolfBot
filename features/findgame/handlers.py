from random import randint
from asyncio import sleep

from aiogram import Router, F
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from .config import (DEFAULT_FIELD_SIZE,
                     MIN_FIELD_SIZE,
                     MAX_FIELD_SIZE,
                     DEFAULT_WIN_CONDITION,
                     MIN_ITEMS_PER_FIELD,
                     MAX_ITEMS_PER_FIELD)
from .session import GameSession
from .session_manager import get_session, set_session, del_session, has_session
from features.findgame.utils import dice_emoji, are_markups_different
from features.findgame.logic import (start_turn_timer,
                                     append_to_dice_log,
                                     append_multiple_to_dice_log,
                                     generate_scoreboard)
from features.findgame.board import build_field_keyboard


router = Router()

@router.message(Command("findgame", "fg", "findgame3", "findgame4", "findgame5", "findgame6"))
async def handle_findgame(msg: Message):
    print("[DEBUG] handle_findgame вызван")

    # Значения по умолчанию
    field_size = DEFAULT_FIELD_SIZE
    win_condition = DEFAULT_WIN_CONDITION

    # Парсим команду и аргументы вручную
    full_text = msg.text.lstrip("/")  # убираем слэш
    command_part, _, args_part = full_text.partition(" ")

    # Попытка определить из команды (например, /findgame5)
    if command_part.startswith("findgame") and command_part != "findgame":
        try:
            field_size = int(command_part.replace("findgame", ""))
        except ValueError:
            pass

    # Попытка переопределить аргументами
    if args_part:
        try:
            tokens = list(map(int, args_part.strip().split()))
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

    # Показываем сообщение с кнопками управления, но без поля
    sent_msg = await msg.answer(
        f"🔍 Старт игры!\nПоле: {field_size}×{field_size}\n"
        f"Победа при {win_condition} находках",
        reply_markup=build_control_keyboard(session)
    )

    session.field_message_id = sent_msg.message_id


def build_control_keyboard(session: GameSession) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="👤 Присоединиться", callback_data="fg:join"),
            InlineKeyboardButton(text="❌ Выйти", callback_data="fg:leave")
        ]
    ]

    # Добавляем кнопку "Начать", только если достаточно игроков
    if len(session.players) >= 2:
        keyboard.append([InlineKeyboardButton(text="▶️ Начать", callback_data="fg:start")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.in_({"fg:join", "fg:leave", "fg:start", "fg:giveup"}))
async def handle_control_buttons(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.full_name or "Игрок"

    session = get_session(chat_id)
    if not session:
        await callback.answer("❌ Игра не найдена.")
        return

    action = callback.data

    if action == "fg:join":
        if session.add_player(user_id, username):
            await callback.answer("✅ Ты присоединился к игре.")
        else:
            await callback.answer("⚠️ Ты уже в игре!")

    elif action == "fg:leave":
        if any(p.user_id == user_id for p in session.players):
            session.remove_player(user_id)
            await callback.answer("🚪 Ты покинул игру.")
        else:
            await callback.answer("❌ Ты не участвуешь в игре.")

    elif action == "fg:start":
        if session.players[0].user_id != user_id:
            await callback.answer("❌ Только инициатор может начать игру.")
            return
        if len(session.players) < 2:
            await callback.answer("⚠️ Нужно минимум 2 игрока.")
            return

        session.started = True

        # 🎲 Бросок кубиков
        dice_rolls = {}
        used_totals = set()
        for player in session.players:
            while True:
                d1, d2 = randint(1, 6), randint(1, 6)
                total = d1 + d2
                if total not in used_totals:
                    used_totals.add(total)
                    dice_rolls[player.user_id] = (total, d1, d2)
                    break

        session.players.sort(key=lambda p: dice_rolls[p.user_id][0], reverse=True)
        session.dice_rolls = dice_rolls

        roll_texts = []
        for player in session.players:
            _, d1, d2 = dice_rolls[player.user_id]
            roll_texts.append(f"{player.display_name}: {dice_emoji(d1)}{dice_emoji(d2)}")

        dice_msg = await callback.message.answer("🎲 Результаты бросков:\n" + "\n".join(roll_texts))
        session.dice_message_id = dice_msg.message_id

        # 🧠 ВАЖНО: сначала генерируем поле, чтобы grid уже был готов
        session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)

        # 🎯 Теперь отображаем поле — оно будет корректным
        await callback.bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.field_message_id,
            text=f"🎮 Игра началась!\nХод первого игрока: {session.get_current_player().username}",
            reply_markup=build_field_keyboard(session)
        )

        # 🧾 Только теперь лог
        await append_to_dice_log(callback.bot, session,
                                 f"🔁 Ход переходит к {session.get_current_player().username}")

        await sleep(0.3)
        await callback.answer("🚀 Поехали!")
        session.cancel_afk_timer()
        await start_turn_timer(callback.bot, session)
        return

    elif action == "fg:giveup":
        if not session.started:
            await callback.answer("❌ Игра ещё не началась.")
            return

        player = next((p for p in session.players if p.user_id == user_id), None)
        if not player:
            await callback.answer("❌ Ты не участвуешь.")
            return

        session.remove_player(user_id)
        await append_to_dice_log(callback.bot, session,
                                 f"🏳️ Игрок {player.display_name} сдался и выбыл из игры.")

        if len(session.players) == 1:
            winner = session.players[0]
            await sleep(0.3)
            await append_to_dice_log(callback.bot, session,
                                     f"🏆 Победил {winner.username}, все остальные выбыли!")
            del_session(chat_id)
            return

        elif session.get_current_player().user_id == user_id:
            session.cancel_afk_timer()
            session.advance_turn()
            await append_to_dice_log(callback.bot, session,
                                     f"🔁 Ход переходит к {session.get_current_player().username}")
            await start_turn_timer(callback.bot, session)

        await callback.message.edit_reply_markup(reply_markup=build_field_keyboard(session))
        await callback.answer("😢 Ты сдался.")
        return

    # 🔁 Обновляем основную клавиатуру управления (если игра ещё не началась)
    if not session.started:
        new_markup = build_control_keyboard(session)
        if not callback.message.reply_markup or are_markups_different(callback.message.reply_markup, new_markup):
            try:
                await callback.message.edit_reply_markup(reply_markup=new_markup)
            except Exception as e:
                print(f"[control_buttons] Ошибка при обновлении клавиатуры: {e}")


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
    session.cancel_afk_timer()
    result = session.click_cell(x, y)
    if result == "already_opened":
        await callback.answer("⛔ Эта клетка уже открыта!", show_alert=True)

        # Переход хода и запуск таймера
        session.advance_turn()
        await start_turn_timer(callback.bot, session)
        await append_to_dice_log(callback.bot, session,
                                 f"🚫 {player.display_name} попытался открыть уже открытую клетку. Ход переходит.")

        new_markup = build_field_keyboard(session)
        if are_markups_different(callback.message.reply_markup, new_markup):
            try:
                await callback.message.edit_reply_markup(reply_markup=new_markup)
            except TelegramRetryAfter as e:
                print(f"[edit_reply_markup] Flood control: wait {e.retry_after}s")
        return
    log_lines = []

    if result == "found":
        log_lines.append(f"✅ {player.display_name} нашёл предмет!")
    elif result == "special":
        log_lines.append(f"🌟 {player.display_name} нашёл **особый предмет** и ПОБЕДИЛ!")
    else:
        log_lines.append(f"❌ {player.display_name} промахнулся.")

    winner = session.check_win()
    if winner:
        log_lines.append(f"🏆 Победил {winner.username} с {winner.score} очками!")
        scoreboard = generate_scoreboard(session)
        log_lines.append(scoreboard)
        await append_multiple_to_dice_log(callback.bot, session, log_lines)
        del_session(chat_id)
    else:
        session.advance_turn()
        await start_turn_timer(callback.bot, session)
        log_lines.append(f"🔁 Ход переходит к {session.get_current_player().username}")
        await append_multiple_to_dice_log(callback.bot, session, log_lines)

    new_markup = build_field_keyboard(session)
    if not callback.message.reply_markup or are_markups_different(callback.message.reply_markup, new_markup):
        try:
            await callback.message.edit_reply_markup(reply_markup=new_markup)
        except TelegramRetryAfter as e:
            print(f"[edit_reply_markup] Flood control: wait {e.retry_after}s")

    await callback.answer()  # чтобы убрать "часики"

