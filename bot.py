# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram import Router
from config import BOT_TOKEN

from features.findgame.handlers import router as findgame_router
from features.core.handlers import router as core_router
from features.recipe.handlers import router as recipe_router
from features.tarot.handlers import router as tarot_router
from features.minifeatures.handlers import router as minifeatures_router
from features.magicball.handlers import router as magicball_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    try:

        print("🔁 Подключаем core_router")
        dp.include_router(core_router)

        print("🔁 Подключаем findgame_router")
        dp.include_router(findgame_router)

        print("🔁 Подключаем recipe_router")
        dp.include_router(recipe_router)

        print("🔁 Подключаем tarot_router")
        dp.include_router(tarot_router)

        print("🔁 Подключаем minifeatures_router")
        dp.include_router(minifeatures_router)

        print("🔁 Подключаем magicball_router")
        dp.include_router(magicball_router)

        print("✅ Все роутеры подключены.")
        print("🚀 Бот запускается...")

        def print_router_info(router: Router, depth=0):
            indent = "  " * depth
            print(f"{indent}📍 Router: {router.name or 'unnamed'}")
            for handler in router.message.handlers:
                filters = [f.__class__.__name__ for f in handler.filters]
                print(f"{indent}  🧩 Message handler with filters: {filters}")
            for subrouter in router.sub_routers:
                print_router_info(subrouter, depth + 1)

        print("🧠 Анализ всех роутеров и их хендлеров:")
        print_router_info(dp)
        await dp.start_polling(bot)

    except Exception as e:
        print(f"❌ Ошибка во время запуска: {e}")
        import traceback
        traceback.print_exc()
        await asyncio.sleep(99999)


if __name__ == "__main__":
    asyncio.run(main())