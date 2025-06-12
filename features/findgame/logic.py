from features.findgame.session import GameSession
from features.findgame.board import build_field_keyboard
from features.findgame.utils import dice_emoji
from .config import AFK_TIMEOUT, AFK_LIMIT
from aiogram import Bot
from asyncio import sleep, create_task  # только нужные импорты
from aiogram.exceptions import TelegramRetryAfter

async def start_turn_timer(bot: Bot, session: GameSession):
    current = session.get_current_player()
    initial_turn = session.current_turn_index
    user_id = current.user_id
    chat_id = session.chat_id

    async def timer():
        await sleep(AFK_TIMEOUT)

        # Игрок уже походил — таймер устарел
        if not session.started or session.current_turn_index != initial_turn:
            return

        session.afk_counters[user_id] += 1

        if session.afk_counters[user_id] >= AFK_LIMIT:
            session.remove_player(user_id)
            await bot.send_message(chat_id, f"💤 {current.username} пропустил {AFK_LIMIT} хода и выбыл из игры!")

            if len(session.players) == 1:
                winner = session.players[0]
                await bot.send_message(chat_id, f"🏆 Победил {winner.username}, все остальные выбыли!")
                return

            session.advance_turn()
        else:
            await bot.send_message(chat_id, f"⏳ {current.username} пропустил ход "
                                            f"({session.afk_counters[user_id]}/{AFK_LIMIT})")
            session.advance_turn()

        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=session.field_message_id,
            reply_markup=build_field_keyboard(session)
        )

        # Просто вызвать саму функцию заново — без обёртки
        await start_turn_timer(bot, session)

    # Запуск самого таймера (один раз)
    session.afk_task = create_task(timer())

async def append_to_dice_log(bot, session, new_line: str):
    session.append_to_log(new_line)

    header = "🎲 Результаты бросков и ходов:\n"
    for idx, player in enumerate(session.players, start=1):
        dice = session.dice_rolls.get(player.user_id)
        if dice:
            _, d1, d2 = dice
            header += f"{player.display_name}: {dice_emoji(d1)}{dice_emoji(d2)} - {idx} ход\n"

    body = "\n".join(session.dice_log)
    new_text = header + ("\n" + body if body else "")

    if session.last_dice_log_text == new_text:
        return

    try:
        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.dice_message_id,
            text=new_text
        )
    except TelegramRetryAfter as e:
        print(f"[append_to_dice_log] Flood control: wait {e.retry_after}s")
    except Exception as e:
        print(f"[append_to_dice_log] Ошибка: {e}")
    finally:
        # Даже если ничего не изменилось — всё равно запоминаем текст
        session.last_dice_log_text = new_text

def generate_scoreboard(session: GameSession) -> str:
    all_players = session.players + session.eliminated_players
    all_players.sort(key=lambda p: p.score, reverse=True)

    lines = ["\n📊 Итоговая таблица счёта:"]
    for idx, player in enumerate(all_players, 1):
        lines.append(f"{idx}. {player.display_name}: {player.score} очк.")
    return "\n".join(lines)

async def append_multiple_to_dice_log(bot, session, lines: list[str]):
    changed = False
    for line in lines:
        if line:  # защита от пустых строк
            session.append_to_log(line)
            changed = True

    if not changed:
        return

    header = "🎲 Результаты бросков и ходов:\n"
    for idx, player in enumerate(session.players, start=1):
        dice = session.dice_rolls.get(player.user_id)
        if dice:
            _, d1, d2 = dice
            header += f"{player.display_name}: {dice_emoji(d1)}{dice_emoji(d2)} - {idx} ход\n"

    body = "\n".join(session.dice_log)
    new_text = header + ("\n" + body if body else "")

    if session.last_dice_log_text == new_text:
        return

    try:
        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.dice_message_id,
            text=new_text
        )
    except TelegramRetryAfter as e:
        print(f"[append_multiple_to_dice_log] Flood control: wait {e.retry_after}s")
    except Exception as e:
        print(f"[append_multiple_to_dice_log] Ошибка: {e}")
    finally:
        session.last_dice_log_text = new_text  # даже при ошибке мы обновим