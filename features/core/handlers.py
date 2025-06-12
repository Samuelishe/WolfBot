from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def handle_start(msg: Message):
    await msg.answer("👋 Привет! Я — шерстяной волчара! Теперь я тут, используй команду help")


@router.message(Command("help"))
async def handle_help(msg: Message):
    await msg.answer("📘 Доступные команды:\n"
                     "/findgame — начать игру по поиску предметов.\n"
                     "/findgame3…6 — задать размер поля.\n"
                     "/help — показать справку.")