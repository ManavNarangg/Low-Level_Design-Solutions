# Game.py
import threading
from typing import Optional

class Game:
    def __init__(self, player1: Player, player2: Player, board_size: int):
        self._board = Board(board_size)
        self._players = [player1, player2]
        self._current_player_index = 0
        self._status = GameStatus.IN_PROGRESS
        self._lock = threading.Lock()

    def make_move(self, row: int, col: int) -> None:
        with self._lock:
            # Check if game is already over
            if self._status != GameStatus.IN_PROGRESS:
                raise InvalidMoveException("Game is already over!")

            # Validate the move
            if not self._board.is_cell_empty(row, col):
                raise InvalidMoveException(f"Cell ({row}, {col}) is already occupied")

            # Place the symbol
            current_player = self._players[self._current_player_index]
            self._board.place_symbol(row, col, current_player.symbol)

            # Check for win
            if self._check_win(row, col, current_player.symbol):
                self._status = (GameStatus.WINNER_X if current_player.symbol == Symbol.X
                               else GameStatus.WINNER_O)
                return

            # Check for draw
            if self._board.is_full():
                self._status = GameStatus.DRAW
                return

            # Switch to next player
            self._current_player_index = (self._current_player_index + 1) % 2

    def _check_win(self, row: int, col: int, symbol: Symbol) -> bool:
        board = self._board
        size = board.size

        # Check the row of the last move
        if all(board.get_cell(row, c).symbol == symbol for c in range(size)):
            return True

        # Check the column of the last move
        if all(board.get_cell(r, col).symbol == symbol for r in range(size)):
            return True

        # Check the main diagonal (only if the move is on it)
        if row == col and all(board.get_cell(i, i).symbol == symbol for i in range(size)):
            return True

        # Check the anti-diagonal (only if the move is on it)
        if row + col == size - 1 and all(board.get_cell(i, size - 1 - i).symbol == symbol for i in range(size)):
            return True

        return False

    @property
    def board(self) -> Board:
        return self._board

    @property
    def current_player(self) -> Player:
        return self._players[self._current_player_index]

    @property
    def status(self) -> GameStatus:
        return self._status

    @property
    def winner(self) -> Optional[Player]:
        if self._status == GameStatus.WINNER_X:
            return next(p for p in self._players if p.symbol == Symbol.X)
        elif self._status == GameStatus.WINNER_O:
            return next(p for p in self._players if p.symbol == Symbol.O)
        return None

    def print_board(self) -> None:
        self._board.print_board()

# Board.py
class Board:
    def __init__(self, size: int):
        self._size = size
        self._grid: list[list[Cell]] = []
        self._initialize_board()

    def _initialize_board(self) -> None:
        self._grid = [[Cell() for _ in range(self._size)] for _ in range(self._size)]

    def place_symbol(self, row: int, col: int, symbol: Symbol) -> None:
        self._validate_position(row, col)
        self._grid[row][col].symbol = symbol

    def is_cell_empty(self, row: int, col: int) -> bool:
        self._validate_position(row, col)
        return self._grid[row][col].is_empty()

    def is_full(self) -> bool:
        for row in self._grid:
            for cell in row:
                if cell.is_empty():
                    return False
        return True

    def get_cell(self, row: int, col: int) -> Cell:
        self._validate_position(row, col)
        return self._grid[row][col]

    @property
    def size(self) -> int:
        return self._size

    def _validate_position(self, row: int, col: int) -> None:
        if row < 0 or row >= self._size or col < 0 or col >= self._size:
            raise InvalidMoveException(f"Position ({row}, {col}) is out of bounds")

    def print_board(self) -> None:
        print()
        for i, row in enumerate(self._grid):
            row_str = " | ".join(f" {cell.symbol.display_char} " for cell in row)
            print(row_str)
            if i < self._size - 1:
                print("-" * (self._size * 5 - 1))
        print()

# Cell.py
class Cell:
    def __init__(self):
        self._symbol = Symbol.EMPTY

    @property
    def symbol(self) -> Symbol:
        return self._symbol

    @symbol.setter
    def symbol(self, value: Symbol):
        self._symbol = value

    def is_empty(self) -> bool:
        return self._symbol == Symbol.EMPTY

# Player.py
class Player:
    def __init__(self, name: str, symbol: Symbol):
        if symbol == Symbol.EMPTY:
            raise ValueError("Player cannot have EMPTY symbol")
        self._name = name
        self._symbol = symbol

    @property
    def name(self) -> str:
        return self._name

    @property
    def symbol(self) -> Symbol:
        return self._symbol

    def __str__(self) -> str:
        return f"{self._name} ({self._symbol.display_char})"

# gameStatus.py(Enum)
class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    WINNER_X = "winner_x"
    WINNER_O = "winner_o"
    DRAW = "draw"

# Symbol.py(Enum)
from enum import Enum

class Symbol(Enum):
    X = 'X'
    O = 'O'
    EMPTY = '_'

    @property
    def display_char(self) -> str:
        return self.value


def main():
    alice = Player("Alice", Symbol.X)
    bob = Player("Bob", Symbol.O)

    game = Game(alice, bob, 3)

    print("========== TIC TAC TOE ==========")

    # Alice (X) completes the top row and wins
    game.make_move(0, 0)  # X at (0,0)
    game.make_move(1, 0)  # O at (1,0)
    game.make_move(0, 1)  # X at (0,1)
    game.make_move(1, 1)  # O at (1,1)
    game.make_move(0, 2)  # X at (0,2) - Alice wins!

    game.print_board()

    print(f"Result: {game.status}")
    winner = game.winner
    if winner is not None:
        print(f"Winner: {winner.name}")

if __name__ == "__main__":
    main()
        