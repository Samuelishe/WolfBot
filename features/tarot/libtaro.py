from pathlib import Path
from random import choice as get_rand
import configparser


resources_path = Path(__file__).resolve().parent / "resources"

#------------------------Словари----------------------------------------------------------------------------

card_decks_names = ["classic", "classic2", "game_of_thrones", "wolf"]
arcana = ["Major", "Minor"]
cards_orientations = ["upright", "reversed"]


major_arcanum_cards_names_russian = {
    "The Fool":"Дурак", "The Magician":"Маг", "The High Priestess":"Жрица", "The Empress":"Императрица",
    "The Emperor":"Император", "The Hierophant":"Иерофант", "The Lovers":"Влюблённые",
    "The Chariot":"Колесница", "Strength":"Сила", "The Hermit":"Отшельник",
    "The Wheel of Fortune":"Колесо фортуны", "Justice":"Справедливость", "The Hanged Man":"Повешенный",
    "Death":"Смерть", "Temperance":"Умеренность", "The Devil":"Дьявол", "The Tower":"Башня",
    "The Star":"Звезда", "The Moon":"Луна", "The Sun":"Солнце", "Judgement":"Суд","The World":"Мир"
}

major_arcanum_cards_names = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
    "The Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement",
    "The World"
]

minor_arcanum_cards_names_russian = {
    "Ace":"Туз", "Two":"Двойка", "Three":"Тройка", "Four":"Четвёрка", "Five":"Пятёрка",
    "Six":"Шестёрка", "Seven":"Семёрка", "Eight":"Восьмёрка", "Nine":"Девятка", "Ten":"Десятка",
    "Page":"Паж", "Knight":"Рыцарь", "Queen":"Королева", "King":"Король"
}

minor_arcanum_cards_names = [
    "Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "Page", "Knight", "Queen", "King"
]

suits_russian = {
    "wands":"жезлов", "swords":"мечей", "pentacles":"пентаклей", "cups":"чаш"
}

suits = ["wands", "swords", "pentacles", "cups"]

#---------------------Функции----------------------------------------------------------------------------------

def get_random_card(card_deck_name: str = get_rand(card_decks_names)) -> list[str]:
    arcanum = get_rand(arcana)
    if arcanum == "Minor":
        card_name = get_rand(minor_arcanum_cards_names)
        suit = get_rand(suits)
    else:
        card_name = get_rand(major_arcanum_cards_names)
        suit = ""
    card = [card_deck_name,
            arcanum,
            suit,
            card_name,
            "upright"]
    return card

def get_random_cards(cards_quantity: int = 2, card_deck_name: str = "classic") -> list[list[str]]:
    cards = []
    while len(cards) < cards_quantity:
        new_card = get_random_card(card_deck_name=card_deck_name)
        if new_card not in cards:
            cards.append(new_card)
    return cards

def get_cards_names(cards: list[list[str]] = None) -> list[str]:
    if cards is None:
        return []
    cards_names = []
    for card in cards:
        if card[1] == "Major":
            cards_names.append(major_arcanum_cards_names_russian[card[3]])
        else:
            cards_names.append(minor_arcanum_cards_names_russian[card[3]] + " " + suits_russian[card[2]])
    return cards_names

def get_two_cards_interpretation(cards: list[list[str]] = None, interpretations_folder: str = "classic") -> str:
    if cards is None:
        return ""
    else:
        first_card_arcanum = cards[0][1]
        first_card_suit = cards[0][2]
        first_card_name = cards[0][3]

        second_card_arcanum = cards[1][1]
        second_card_suit = cards[1][2]
        second_card_name = cards[1][3]

        prebuild_path_components = ["combinations", interpretations_folder]

        if first_card_arcanum == "Major":
            prebuild_path_components.append("major_arcana")
        else:
            prebuild_path_components.append(first_card_suit)

        prebuild_path_components.append(first_card_name)

        if second_card_arcanum == "Major":
            prebuild_path_components.append("major_arcana")
        else:
            prebuild_path_components.append(second_card_suit)

        interpretation_path = resources_path.joinpath(*prebuild_path_components).with_suffix(".ini")

        config = configparser.ConfigParser()
        config.read(interpretation_path, encoding="utf-8")
        interpretation = config.get("interpretations", second_card_name)

        return interpretation

def get_cards_covers(cards: list[list[str]] = None) -> list[str]:
    if cards is None:
        return []

    major_arcanum_card_index = {
        name: str(index) for index, name in enumerate(major_arcanum_cards_names)
    }

    minor_arcanum_card_index = {
        name: str(index) for index, name in enumerate(minor_arcanum_cards_names)
    }

    images_paths = []
    for card in cards:
        prebuild_path_components = ["covers", card[0]]

        if card[1] == "Major":
            prebuild_path_components.append("major arcana")  # ← с пробелом
            card_filename = major_arcanum_card_index[card[3]]
        else:
            prebuild_path_components.append(card[2])  # масть
            card_filename = minor_arcanum_card_index[card[3]]

        prebuild_path_components.append("straight")
        prebuild_path_components.append(card_filename)

        image_path = resources_path.joinpath(*prebuild_path_components).with_suffix(".png").as_posix()
        images_paths.append(image_path)

    return images_paths

def get_random_card_cover() -> list[str]:
    arcanum = get_rand(arcana)
    if arcanum == "Minor":
        card_name = get_rand(minor_arcanum_cards_names)
    else:
        card_name = get_rand(major_arcanum_cards_names)

    path_parts = [get_rand(card_decks_names),
                  arcanum,
                  get_rand(suits),
                  card_name,
                  get_rand(cards_orientations)]
    path_parts = [path_parts]

    return get_cards_covers(path_parts)



