from aiogram import Router, F
from aiogram.types import Message, InputMediaPhoto, FSInputFile
from aiogram.filters import Command
from random import choice
import re


from .libtaro import (get_random_cards,
                      get_cards_covers,
                      get_cards_names,
                      get_two_cards_interpretation,
                      card_decks_names
                      )
router = Router(name="tarot_router")

# Регулярка для таро-раскладов
TARO_PATTERN = re.compile(r"^\s*(расклад|таро)[\s,:-]*(на|для)\b", re.IGNORECASE)

# Универсальный хендлер для чтения таро
async def send_tarot_reading_with_deck(message: Message, deck_name: str):
    cards = get_random_cards(2, deck_name)
    image_paths = get_cards_covers(cards)
    card_names = get_cards_names(cards)
    interpretation = get_two_cards_interpretation(cards)

    media = [
        InputMediaPhoto(media=FSInputFile(img_path))
        for img_path in image_paths
    ]
    await message.answer_media_group(media)

    cards_text = f"🔮 Карты: {card_names[0]} + {card_names[1]}"
    await message.answer(f"{cards_text}\n\n{interpretation}")

# Основная команда /taro или /tarot (по умолчанию classic2)
@router.message(Command("taro", "tarot"))
async def send_tarot_default(message: Message):
    await send_tarot_reading_with_deck(message, "classic2")

# Дополнительные команды
@router.message(Command("taro1"))
async def send_tarot_1(message: Message):
    await send_tarot_reading_with_deck(message, "classic")

@router.message(Command("taro2"))
async def send_tarot_2(message: Message):
    await send_tarot_reading_with_deck(message, "classic2")

@router.message(Command("taro3"))
async def send_tarot_3(message: Message):
    await send_tarot_reading_with_deck(message, "game_of_thrones")

@router.message(Command("taro4"))
async def send_tarot_4(message: Message):
    await send_tarot_reading_with_deck(message, "wolf")

@router.message(F.text.regexp(TARO_PATTERN))
async def detect_tarot_request(message: Message):
    if message.text and TARO_PATTERN.search(message.text):
        await _send_tarot(message)


async def _send_tarot(message: Message):
    cards = get_random_cards(2, choice(card_decks_names))
    image_paths = get_cards_covers(cards)
    card_names = get_cards_names(cards)
    interpretation = get_two_cards_interpretation(cards)

    media = [FSInputFile(path) for path in image_paths]
    await message.answer_media_group([InputMediaPhoto(media=img) for img in media])

    cards_text = f"🔮 Карты: {card_names[0]} + {card_names[1]}"
    await message.answer(f"{cards_text}\n\n{interpretation}")