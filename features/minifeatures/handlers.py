from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from random import SystemRandom


router = Router(name="minifeatures_router")
secure_random = SystemRandom()

@router.message(Command("dice"))
async def roll_dice(message: Message):
    dice_emoji = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅",
    }

    die1 = secure_random.randint(1, 6)
    die2 = secure_random.randint(1, 6)
    total = die1 + die2
    result = f"{dice_emoji[die1]} + {dice_emoji[die2]} = {total}"
    await message.answer(f"🎲 Результат броска: {result}")

@router.message(Command("flip"))
async def coin_flip(message: Message):
    roll = secure_random.randint(1, 100)

    if roll <= 46:
        side = "Орёл 🦅"
    elif roll <= 92:
        side = "Решка 🪙"
    elif roll <= 94:
        side = "Монета встала на ребро 😲"
    else:
        side = "Монета укатилась под шкаф 🫠"

    await message.answer(f"🪙 Результат броска: {side}")