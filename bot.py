# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from features.findgame.handlers import router as findgame_router
print("[DEBUG] findgame_router импортирован")

from features.core.handlers import router as core_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(core_router)
    dp.include_router(findgame_router)  # ← подключаем findgame роутер

    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
