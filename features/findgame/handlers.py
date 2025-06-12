from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from .config import DEFAULT_FIELD_SIZE, MIN_FIELD_SIZE, MAX_FIELD_SIZE, DEFAULT_WIN_CONDITION

router = Router()

@router.message(Command(commands=["findgame", "fg", "findgame3", "findgame4", "findgame5", "findgame6"]))
async def handle_findgame(msg: Message, command: CommandObject):
    cmd = command.command  # тип: str
    args = command.args    # тип: str | None

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

    # Ограничим
    field_size = max(MIN_FIELD_SIZE, min(MAX_FIELD_SIZE, field_size))

    await msg.answer(
        f"🔍 Старт игры!\nПоле: {field_size}×{field_size}\n"
        f"Победа при {win_condition} находках"
    )