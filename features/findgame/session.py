from typing import List, Optional
import random


class Player:
    def __init__(self, user_id: int, username: Optional[str]):
        self.user_id = user_id
        self.username = username or f"id:{user_id}"
        self.score = 0
        self.last_roll = None  # (dice1, dice2)

    def __repr__(self):
        return f"<Player {self.username} (id={self.user_id}) score={self.score}>"

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

    def add_player(self, user_id: int, username: Optional[str]) -> bool:
        if any(p.user_id == user_id for p in self.players):
            return False  # уже есть
        self.players.append(Player(user_id, username))
        return True

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
        num_items = random.randint(min_items, max_items)
        has_special = random.random() < special_chance

        # если special будет, то обычных предметов на 1 меньше
        actual_items = num_items - 1 if has_special else num_items

        # Инициализируем все клетки как пустые
        flat_grid = ['empty'] * total_cells

        # Случайно разместим обычные предметы
        item_indices = random.sample(range(total_cells), actual_items)
        for idx in item_indices:
            flat_grid[idx] = 'item'

        # Сохраним координаты обычных предметов
        self.item_positions = [(idx // self.field_size, idx % self.field_size) for idx in item_indices]

        # Если special, разместим его в отдельной клетке
        if has_special:
            empty_indices = [i for i in range(total_cells) if flat_grid[i] == 'empty']
            if empty_indices:
                special_idx = random.choice(empty_indices)
                flat_grid[special_idx] = 'special'
                self.special_position = (special_idx // self.field_size, special_idx % self.field_size)

        # Преобразуем в 2D grid
        self.grid = [
            flat_grid[i:i + self.field_size]
            for i in range(0, total_cells, self.field_size)
        ]

    def click_cell(self, x: int, y: int) -> str:
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
        for p in self.players:
            if p.score >= self.win_condition:
                self.winner = p
                return p
        return None