
import random
from abc import ABC
from collections import deque
from typing import Dict, List, Optional


class Player:
    def __init__(self, name: str):
        self._name = name
        self._position = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def position(self) -> int:
        return self._position

    def move_to(self, position: int) -> None:
        self._position = position


class Dice:
    def __init__(self, min_val: int = 1, max_val: int = 6):
        if min_val > max_val:
            raise ValueError("Minimum value cannot exceed maximum value")

        self._min_val = min_val
        self._max_val = max_val

    def roll(self) -> int:
        return random.randint(self._min_val, self._max_val)


class BoardEntity(ABC):
    def __init__(self, start: int, end: int):
        self._start = start
        self._end = end

    @property
    def start(self) -> int:
        return self._start

    @property
    def end(self) -> int:
        return self._end


class Snake(BoardEntity):
    def __init__(self, start: int, end: int):
        if start <= end:
            raise ValueError("Snake must go downward")
        super().__init__(start, end)


class Ladder(BoardEntity):
    def __init__(self, start: int, end: int):
        if start >= end:
            raise ValueError("Ladder must go upward")
        super().__init__(start, end)


class Board:
    def __init__(self, size: int):
        if size < 2:
            raise ValueError("Board size must be at least 2")

        self._size = size
        self._entities: Dict[int, BoardEntity] = {}

    @property
    def size(self) -> int:
        return self._size

    def add_entity(self, entity: BoardEntity) -> None:
        if not (1 <= entity.start <= self._size):
            raise ValueError("Entity start is outside the board")

        if not (1 <= entity.end <= self._size):
            raise ValueError("Entity end is outside the board")

        if entity.start in self._entities:
            raise ValueError("An entity already exists at this position")

        self._entities[entity.start] = entity

    def get_position(self, position: int) -> int:
        visited = set()

        while position in self._entities:
            if position in visited:
                raise ValueError("Cycle detected in board entities")

            visited.add(position)
            entity = self._entities[position]

            if isinstance(entity, Ladder):
                print(f"Ladder! {entity.start} -> {entity.end}")
            else:
                print(f"Snake! {entity.start} -> {entity.end}")

            position = entity.end

        return position


class Game:
    def __init__(
        self,
        board: Board,
        players: List[Player],
        dice: Dice
    ):
        if len(players) < 2:
            raise ValueError("At least two players are required")

        self._board = board
        self._dice = dice
        self._players = deque(players)
        self._winner: Optional[Player] = None

    def start_game(self) -> None:
        while self._players and self._winner is None:
            current_player = self._players.popleft()

            dice_value = self._dice.roll()
            old_position = current_player.position
            new_position = old_position + dice_value

            print(
                f"\n{current_player.name} rolled {dice_value}"
            )

            # Player must land exactly on the final square.
            if new_position > self._board.size:
                print(
                    f"{current_player.name} stays at {old_position}"
                    " (overshot the board)"
                )
                self._players.append(current_player)
                continue

            final_position = self._board.get_position(new_position)
            current_player.move_to(final_position)

            print(
                f"{current_player.name}: "
                f"{old_position} -> {final_position}"
            )

            if final_position == self._board.size:
                self._winner = current_player
                print(f"\n{current_player.name} wins!")
                break

            self._players.append(current_player)

    @property
    def winner(self) -> Optional[Player]:
        return self._winner


if __name__ == "__main__":
    board = Board(100)

    # Ladders
    for start, end in [
        (2, 38), (4, 14), (9, 31),
        (21, 42), (28, 84), (51, 67)
    ]:
        board.add_entity(Ladder(start, end))

    # Snakes
    for start, end in [
        (17, 7), (54, 34), (62, 19),
        (64, 60), (87, 36), (93, 73), (98, 79)
    ]:
        board.add_entity(Snake(start, end))

    players = [
        Player("Alice"),
        Player("Bob"),
        Player("Charlie")
    ]

    dice = Dice()
    game = Game(board, players, dice)
    game.start_game()
