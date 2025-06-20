print("🔮 MAGICBALL HANDLERS загружены")

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
from .config import FILE_LABELS, MODE_LABELS

from .logic import get_magicball_answer

router = Router(name="magicball_router")

@router.message(Command(commands=["mb","magicball"]))
async def handle_magicball(message: Message):
    # Анимация
    msg = await message.answer("Магический шар медленно проявляет очертания ответа...")
    await asyncio.sleep(2)

    try:
        await msg.edit_text("Пелена тайны рассеивается...")
    except Exception:
        await message.answer("Что-то пошло не так во время предсказания...")
        return

    await asyncio.sleep(2)

    result = await get_magicball_answer()
    if not result:
        await message.answer("Не удалось вызвать духа ответа. Попробуй позже.")
        return

    answer, mode, filename = result
    full_path = f"{mode}/{filename}"

    mode_label = MODE_LABELS.get(mode.split("/")[0], "🤔 Неизвестный режим")
    file_label = FILE_LABELS.get(full_path, "📄 Неизвестный файл")

    try:
        await msg.edit_text(
            f"{mode_label}  |  {file_label}\n\n"
            f"Магический шар говорит:\n{answer}"
        )
    except Exception:
        await message.answer(
            f"{mode_label}  |  {file_label}\n\n"
            f"Магический шар говорит:\n{answer}"
        )