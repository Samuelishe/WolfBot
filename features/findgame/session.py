from typing import List, Optional
from asyncio import Task
from random import randint, random, sample, choice


class Player:
    def __init__(self, user_id: int, username: Optional[str]):
        self.user_id = user_id
        self.username = username or f"Игрок {user_id}"
        self.score = 0

    def __repr__(self):
        return f"<Player {self.username} (id={self.user_id}) score={self.score}>"

    @property
    def display_name(self) -> str:
        if self.username.startswith("@"):
            return self.username
        if self.username.startswith("Игрок "):
            return self.username
        return f"@{self.username}"

class GameSession:
    def __init__(self, chat_id: int, field_size: int, win_condition: int):
        self.chat_id = chat_id
        self.field_size = field_size
        self.win_condition = win_condition

        self.players: List[Player] = []
        self.started = False
        self.current_turn_index = 0
        self.winner: Optional[Player] = None

        self.grid = []  # 2D список или плоский список кнопок
        self.hidden_item = None  # координаты спрятанного предмета

        self.item_positions: List[tuple[int, int]] = []
        self.special_position: Optional[tuple[int, int]] = None

        self.afk_counters: dict[int, int] = {}  # user_id -> число пропусков подряд
        self.field_message_id: Optional[int] = None  # ID сообщения с полем

        self.control_message_id: Optional[int] = None  # ID сообщения с панелью управления
        self.control_messages: dict[int, int] = {}  # user_id -> message_id персонального управления

        self.opened_cells: set[tuple[int, int]] = set() # список открытых ячеек
        self.dice_message_id: Optional[int] = None  # ID сообщения с результатами
        self.afk_task: Optional[Task] = None  # текущий таймер хода
        self.dice_log: list[str] = []  # лог ходов и событий
        self.dice_rolls: dict[int, tuple[int, int, int]] = {}  # user_id -> (total, d1, d2)
        self.eliminated_players: list[Player] = [] # выбывшие игроки
        self.last_dice_log_text: Optional[str] = None # локальное хранение последнего текста лога

    def add_player(self, user_id: int, username: Optional[str]) -> bool:
        if any(p.user_id == user_id for p in self.players):
            return False  # уже есть
        self.players.append(Player(user_id, username))
        self.afk_counters[user_id] = 0
        return True

    def remove_player(self, user_id: int):
        player = next((p for p in self.players if p.user_id == user_id), None)
        if not player:
            return

        index = self.players.index(player)

        self.players.remove(player)
        self.eliminated_players.append(player)
        self.afk_counters.pop(user_id, None)

        # Сдвигаем current_turn_index, если удалённый игрок был:
        if index < self.current_turn_index:
            self.current_turn_index -= 1
        elif index == self.current_turn_index:
            # Если удалили текущего — следующий игрок становится первым
            if self.current_turn_index >= len(self.players):
                self.current_turn_index = 0

    def get_current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_turn_index]

    def advance_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)

    def generate_field(self, min_items: int, max_items: int, special_chance: float = 0.05):
        self.item_positions = []
        self.special_position = None

        total_cells = self.field_size * self.field_size
        num_items = randint(min_items, max_items)
        has_special = random() < special_chance

        # если special будет, то обычных предметов на 1 меньше
        actual_items = num_items - 1 if has_special else num_items

        # Инициализируем все клетки как пустые
        flat_grid = ['empty'] * total_cells

        # Случайно разместим обычные предметы
        item_indices = sample(range(total_cells), actual_items)
        for idx in item_indices:
            flat_grid[idx] = 'item'

        # Сохраним координаты обычных предметов
        self.item_positions = [(idx // self.field_size, idx % self.field_size) for idx in item_indices]

        # Если special, разместим его в отдельной клетке
        if has_special:
            empty_indices = [i for i in range(total_cells) if flat_grid[i] == 'empty']
            if empty_indices:
                special_idx = choice(empty_indices)
                flat_grid[special_idx] = 'special'
                self.special_position = (special_idx // self.field_size, special_idx % self.field_size)

        # Преобразуем в 2D grid
        self.grid = [
            flat_grid[i:i + self.field_size]
            for i in range(0, total_cells, self.field_size)
        ]

    def click_cell(self, x: int, y: int) -> str:
        if (x, y) in self.opened_cells:
            return "already_opened"  # Никакого действия, клетка уже открыта

        self.opened_cells.add((x, y))  # Сохраняем, что клетка открыта
        if not (0 <= x < self.field_size and 0 <= y < self.field_size):
            return "invalid"
        cell = self.grid[y][x]

        if cell == 'item':
            self.get_current_player().score += 1
            return "found"
        elif cell == 'special':
            self.get_current_player().score += 10
            self.winner = self.get_current_player()
            return "special"
        else:
            return "empty"


    def check_win(self) -> Optional[Player]:
        if self.winner:
            return self.winner
        for player in self.players:
            if player.score >= self.win_condition:
                return player
        return None

    def cancel_afk_timer(self):
        if self.afk_task:
            self.afk_task.cancel()
            self.afk_task = None

    def append_to_log(self, text: str):
        self.dice_log.append(text)