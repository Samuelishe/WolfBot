from features.findgame.session import GameSession
from features.findgame.handlers import build_field_keyboard
from .config import AFK_TIMEOUT, AFK_LIMIT, MIN_ITEMS_PER_FIELD, MAX_ITEMS_PER_FIELD
from aiogram import Bot
from asyncio import sleep


async def start_turn_timer(bot: Bot, session: GameSession):
    current = session.get_current_player()
    initial_turn = session.turn_index

    await sleep(AFK_TIMEOUT)

    # Проверим: не изменился ли игрок (кто-то кликнул до таймера)
    if not session.started or session.turn_index != initial_turn:
        return

    user_id = current.user_id
    session.afk_counters[user_id] += 1

    chat_id = session.chat_id
    if session.afk_counters[user_id] >= AFK_LIMIT:
        session.remove_player(user_id)
        await bot.send_message(chat_id, f"💤 {current.username} пропустил {AFK_LIMIT} хода и выбыл из игры!")

        if len(session.players) == 1:
            winner = session.players[0]
            await bot.send_message(chat_id, f"🏆 Победил {winner.username}, все остальные выбыли!")
            return

        session.advance_turn()
    else:
        await bot.send_message(chat_id, f"⏳ {current.username} пропустил ход ({session.afk_counters[user_id]}/{AFK_LIMIT})")
        session.advance_turn()

    # Перегенерировать поле и клавиатуру
    session.generate_field(min_items=MIN_ITEMS_PER_FIELD, max_items=MAX_ITEMS_PER_FIELD)
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=session.field_message_id,
        reply_markup=build_field_keyboard(session.field_size)
    )

    # Новый ход — запускаем таймер заново
    await start_turn_timer(bot, session)