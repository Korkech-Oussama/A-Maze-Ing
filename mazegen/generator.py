import random
import collections
from typing import List, Tuple, Optional, Set


WEST: int = 0b1000
SOUTH: int = 0b0100
EAST: int = 0b0010
NORTH: int = 0b0001

DELTA: dict = {
    WEST: (-1, 0),
    SOUTH: (0, 1),
    EAST: (1, 0),
    NORTH: (0, -1)
}

OPPOSIT: dict = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST
}

COORD_42: set[tuple[int, int]] = {
    # The '4'
    (0, 0),
    (0, 1),
    (0, 2), (1, 2), (2, 2),
                    (2, 3),
                    (2, 4),

    # The '2'
    (4, 0), (5, 0), (6, 0),
                    (6, 1),
    (4, 2), (5, 2), (6, 2),
    (4, 3),                
    (4, 4), (5, 4), (6, 4)
}

class MazeGenerator:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.grid: List[List[int]] = [[15] * self.width for _ in range(self.height)]
        self.block_42: Set[Tuple[int, int]] = set()

    def _create_42_block(self):
        if self.width < 9 or self.height < 7:
            print("skip generating the 42 shield")
            return
        center_x: int = self.width // 2
        center_y: int = self.height //2
        start_x: int = center_x - 3
        start_y: int = center_y - 2
        for (x, y) in COORD_42:
            dynamic_x: int = start_x + x
            dynamic_y: int = start_y + y
            self.block_42.add((dynamic_x, dynamic_y))

    def _carve_passage(self, cx: int, cy: int) -> None:
        directions: list = [WEST, SOUTH, EAST, NORTH]
        random.shuffle(directions)
        for direction in directions:
            dx, dy = DELTA[direction]
            nx = cx + dx
            ny = cy + dy
            if (0 <= nx < self.width and 0 <= ny < self.height and
               self.grid[ny][nx] == 15 and (nx, ny) not in self.block_42):
                self.grid[cy][cx] &= ~direction
                self.grid[ny][nx] &= ~OPPOSIT[direction]
                self._carve_passage(nx, ny)

    def show_hexa(self):
        for row in self.grid:
            print([format(item, 'X') for item in row])

    def display(self):
        top = "#" * (self.width * 2 + 1) 
        print(top)
        for row in self.grid:
            room: str = "#"
            floor: str = "#"
            for cell in row:
                room += " "
                if cell & EAST:
                    room += "#"
                else:
                    room += " "
                if cell & SOUTH:
                    floor += "#"
                else:
                    floor += " "
                floor += "#"
            print(room)
            print(floor)


if __name__ == "__main__":
    maze = MazeGenerator(9, 7)
    maze._create_42_block()
    maze._carve_passage(0,0)
    maze.show_hexa()
    maze.display()
