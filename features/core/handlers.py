from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router(name="core_router")

@router.message(Command("start"))
async def handle_start(msg: Message):
    await msg.answer("👋 Привет! Я — шерстяной волчара! Теперь я тут, используй команду help")


@router.message(Command("help"))
async def handle_help(msg: Message):
    await msg.answer("📘 Доступные команды:\n"
                     "/taro, /tarot, /taro1, /taro2, /taro3, /taro4 - таро\n"
                     "/recipe - рецепт\n"
                     "/dice - кинуть кубики\n"
                     "/flip - подбросить монету"
                     "/help — показать справку [вы тут]\n")