import requests
from bs4 import BeautifulSoup
import json
import random

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router(name="recipe_router")

@router.message(Command("recipe"))
async def send_random_recipe(message: Message):
    for _ in range(5):
        recipe_id = random.randint(100000, 260000)
        title, image_url, ingredients, difficulty, spiciness, cuisine, time_str = fetch_recipe(recipe_id)
        if title and image_url and ingredients:
            break
    else:
        await message.answer("🥲 Не удалось найти подходящий рецепт.")
        return

    url = f"https://food.ru/recipes/{recipe_id}"
    caption = f'<b><a href="{url}">{title}</a></b>\n'
    if cuisine:
        caption += f"Кухня: {cuisine}\n"
    caption += f"Сложность: {difficulty}\n"
    if spiciness:
        caption += f"      Острота: {spiciness}\n"
    if time_str:
        caption += f"⏱ Время на кухне: {time_str}\n\n"

    caption += "\n".join(f"• {item}" for item in ingredients[:20])

    try:
        await message.answer_photo(photo=image_url, caption=caption, parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] Ошибка отправки фото: {e}")
        await message.answer(f"{caption}\n\n(⚠️ Картинку не удалось загрузить)", parse_mode="HTML")


def fetch_recipe(recipe_id: int):
    url = f"https://food.ru/recipes/{recipe_id}"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
    except Exception:
        return None, None, None, None, None, None, None

    soup = BeautifulSoup(r.text, 'html.parser')

    title = None
    image = None
    ingredients = []
    difficulty_str = ""
    spiciness_str = ""
    cuisine_str = ""
    time_str = ""

    # 1. JSON-LD
    data = soup.find("script", type="application/ld+json")
    if data:
        try:
            js = json.loads(data.string)
            if isinstance(js, list):
                js = next((x for x in js if x.get("@type") == "Recipe"), js[0])
            if js.get("@type") == "Recipe":
                img = js.get("image")
                if isinstance(img, list):
                    img = img[0]
                if img:
                    image = img

                ing = js.get("recipeIngredient")
                if ing:
                    ingredients = ing
        except Exception as e:
            print(f"[DEBUG] JSON-LD ошибка: {e}")

    # 2. Название (если не было в JSON)
    if not title:
        title_tag = soup.find("h1", itemprop="name")
        if title_tag:
            title = title_tag.get_text(strip=True)

    # 3. og:image (если не было в JSON)
    if not image:
        og = soup.find("meta", property="og:image")
        if og:
            image = og.get("content")

    # 4. Ингредиенты (если не было в JSON)
    if not ingredients:
        for row in soup.select("tr.ingredient"):
            name = row.select_one("span.name")
            tds = row.find_all("td")
            if name and len(tds) >= 2:
                amount = tds[1].get_text(strip=True)
                ingredients.append(f"{name.get_text(strip=True)} — {amount}")

    # 5. Сложность и 6. Острота
    for row in soup.select("div.properties_row___W5cZ"):
        inner_divs = row.find_all("div", recursive=False)
        for div in inner_divs:
            span = div.select_one("span.properties_property__YugVw")
            level_div = div.select_one("div.properties_level___bLQQ")
            if not span or not level_div:
                continue

            label_text = span.get_text(strip=True)

            if label_text.startswith("Сложность"):
                active = len(level_div.select("svg.properties_iconActive__yDry0"))
                inactive = len(level_div.select("svg.properties_icon__fhXg9"))
                difficulty_str = "🟩" * active + "⬜" * inactive

            elif label_text.startswith("Острота"):
                all_svgs = level_div.find_all("svg")
                active = 0
                for svg in all_svgs:
                    if not svg.find("g", attrs={"opacity": "0.5"}):
                        active += 1
                spiciness_str = "🌶️" * active

    # 7. Кухня
    cuisine_block = soup.select_one("div.properties_kitchen__N9cv1 div.properties_value__kAeD9")
    if cuisine_block:
        cuisine_str = cuisine_block.get_text(strip=True)

    # 8. Время на кухне
    time_blocks = soup.find_all("span", class_="properties_property__YugVw")
    for span in time_blocks:
        if span.get_text(strip=True).startswith("Время на кухне"):
            value_div = span.find_next_sibling("div", class_="properties_value__kAeD9")
            if not value_div:
                value_div = span.find_next_sibling("div", class_="properties_value__kAeD9 properties_valueWithIcon__WDXDm")
            if value_div:
                time_str = value_div.get_text(strip=True)
            break

    # 🧱 Усиленная защита от крашей
    if not title:
        title = "Неизвестное блюдо"

    if not any([title, image, ingredients]):
        return None, None, None, None, None, None, None

    return title, image, ingredients, difficulty_str, spiciness_str, cuisine_str, time_str
