import os
import random

from .config import ANSWERS_DIR, ALL_MODES, RAGE_MODE_STATES, FILE_LABELS, MODE_LABELS

async def load_answers(mode: str) -> list[str]:
    """Загружает ответы из случайного файла для режима."""
    if mode == "rage_mode":
        mode = random.choice(RAGE_MODE_STATES)

    mode_dir = os.path.join(
        str(ANSWERS_DIR),
        *[str(p) for p in mode.split("/")]
    )

    if not os.path.exists(mode_dir):
        return []

    txt_files = [f for f in os.listdir(mode_dir) if f.endswith(".txt")]
    if not txt_files:
        return []

    selected_file = random.choice(txt_files)
    file_path = os.path.join(mode_dir, selected_file)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            answers = [line.strip() for line in f if line.strip()]
        return answers
    except Exception:
        return []

async def get_magicball_answer() -> tuple[str, str, str] | None:
    """Выбирает и возвращает одну случайную фразу, а также режим и файл."""
    mode = random.choice(ALL_MODES)
    answers = await load_answers(mode)

    if not answers:
        return None

    # Повторяем выбор файла (в том же стиле)
    if mode == "rage_mode":
        mode = random.choice(RAGE_MODE_STATES)

    mode_dir = os.path.join(str(ANSWERS_DIR), *mode.split("/"))
    txt_files = [f for f in os.listdir(mode_dir) if f.endswith(".txt")]
    if not txt_files:
        return None

    selected_file = random.choice(txt_files)
    file_path = os.path.join(mode_dir, selected_file)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return None
        answer = random.choice(lines)
    except Exception:
        return None

    return answer, mode, selected_file