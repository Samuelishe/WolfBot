from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("findgame"))
async def start_findgame(msg: Message):
    await msg.answer("Запускаем игру!")